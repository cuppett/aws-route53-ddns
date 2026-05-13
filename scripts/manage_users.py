#!/usr/bin/env python3
"""CLI tool for managing DDNS Route53 authorization records in DynamoDB."""

import argparse
import datetime
import sys

import bcrypt
import boto3
from boto3.dynamodb.conditions import Key


DEFAULT_TABLE = 'DDNSAuthorization'


def _table(args):
    session = boto3.Session(profile_name=getattr(args, 'profile', None))
    ddb = session.resource('dynamodb', region_name=getattr(args, 'region', 'us-east-1'))
    return ddb.Table(args.table)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def _parse_hosts(hosts_str: str) -> list[dict]:
    """Parse 'ZONE_ID:hostname,ZONE_ID:hostname' into list of dicts."""
    result = []
    for entry in hosts_str.split(','):
        entry = entry.strip()
        if not entry:
            continue
        if ':' not in entry:
            print(f"ERROR: Invalid host entry '{entry}' — expected ZONE_ID:hostname", file=sys.stderr)
            sys.exit(1)
        zone_id, hostname = entry.split(':', 1)
        result.append({'zone_id': zone_id.strip(), 'hostname': hostname.strip()})
    return result


def cmd_add_user(args):
    table = _table(args)
    existing = table.get_item(Key={'username': args.username}).get('Item')
    if existing:
        print(f"ERROR: User '{args.username}' already exists. Use update-password or add-host.", file=sys.stderr)
        sys.exit(1)

    allowed_hosts = _parse_hosts(args.hosts) if args.hosts else []
    now = _now()
    table.put_item(Item={
        'username': args.username,
        'password_hash': _hash_password(args.password),
        'enabled': True,
        'allowed_hosts': allowed_hosts,
        'created_at': now,
        'updated_at': now,
    })
    print(f"Created user '{args.username}' with {len(allowed_hosts)} host(s).")


def cmd_list_users(args):
    table = _table(args)
    resp = table.scan(ProjectionExpression='username, enabled, allowed_hosts, updated_at')
    items = sorted(resp.get('Items', []), key=lambda x: x['username'])
    if not items:
        print('No users found.')
        return
    for item in items:
        status = 'enabled' if item.get('enabled', True) else 'DISABLED'
        hosts = item.get('allowed_hosts', [])
        host_list = ', '.join(f"{h['hostname']} ({h['zone_id']})" for h in hosts) or '(none)'
        print(f"  {item['username']}  [{status}]  hosts: {host_list}  updated: {item.get('updated_at', '?')}")


def cmd_disable_user(args):
    table = _table(args)
    table.update_item(
        Key={'username': args.username},
        UpdateExpression='SET enabled = :v, updated_at = :t',
        ExpressionAttributeValues={':v': False, ':t': _now()},
    )
    print(f"Disabled user '{args.username}'.")


def cmd_enable_user(args):
    table = _table(args)
    table.update_item(
        Key={'username': args.username},
        UpdateExpression='SET enabled = :v, updated_at = :t',
        ExpressionAttributeValues={':v': True, ':t': _now()},
    )
    print(f"Enabled user '{args.username}'.")


def cmd_remove_user(args):
    table = _table(args)
    table.delete_item(Key={'username': args.username})
    print(f"Removed user '{args.username}'.")


def cmd_update_password(args):
    table = _table(args)
    table.update_item(
        Key={'username': args.username},
        UpdateExpression='SET password_hash = :h, updated_at = :t',
        ExpressionAttributeValues={':h': _hash_password(args.password), ':t': _now()},
    )
    print(f"Updated password for '{args.username}'.")


def cmd_add_host(args):
    table = _table(args)
    item = table.get_item(Key={'username': args.username}).get('Item')
    if not item:
        print(f"ERROR: User '{args.username}' not found.", file=sys.stderr)
        sys.exit(1)

    hosts = list(item.get('allowed_hosts', []))
    for h in hosts:
        if h['hostname'] == args.hostname:
            print(f"Host '{args.hostname}' already in allowed list for '{args.username}'.")
            return

    hosts.append({'zone_id': args.zone_id, 'hostname': args.hostname})
    table.update_item(
        Key={'username': args.username},
        UpdateExpression='SET allowed_hosts = :h, updated_at = :t',
        ExpressionAttributeValues={':h': hosts, ':t': _now()},
    )
    print(f"Added host '{args.hostname}' (zone {args.zone_id}) for user '{args.username}'.")


def cmd_remove_host(args):
    table = _table(args)
    item = table.get_item(Key={'username': args.username}).get('Item')
    if not item:
        print(f"ERROR: User '{args.username}' not found.", file=sys.stderr)
        sys.exit(1)

    hosts = [h for h in item.get('allowed_hosts', []) if h['hostname'] != args.hostname]
    table.update_item(
        Key={'username': args.username},
        UpdateExpression='SET allowed_hosts = :h, updated_at = :t',
        ExpressionAttributeValues={':h': hosts, ':t': _now()},
    )
    print(f"Removed host '{args.hostname}' from user '{args.username}'.")


def main():
    parser = argparse.ArgumentParser(description='Manage DDNS Route53 authorization records')
    parser.add_argument('--table', default=DEFAULT_TABLE, help='DynamoDB table name')
    parser.add_argument('--profile', default=None, help='AWS profile name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')

    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('add-user', help='Create a new DDNS user')
    p.add_argument('--username', required=True)
    p.add_argument('--password', required=True)
    p.add_argument('--hosts', default='', help='Comma-separated ZONE_ID:hostname pairs')

    sub.add_parser('list-users', help='List all DDNS users')

    p = sub.add_parser('disable-user', help='Disable a user (blocks authentication)')
    p.add_argument('--username', required=True)

    p = sub.add_parser('enable-user', help='Re-enable a disabled user')
    p.add_argument('--username', required=True)

    p = sub.add_parser('remove-user', help='Permanently delete a user')
    p.add_argument('--username', required=True)

    p = sub.add_parser('update-password', help='Change a user\'s password')
    p.add_argument('--username', required=True)
    p.add_argument('--password', required=True)

    p = sub.add_parser('add-host', help='Add a hostname to a user\'s allowed list')
    p.add_argument('--username', required=True)
    p.add_argument('--zone-id', required=True, dest='zone_id')
    p.add_argument('--hostname', required=True)

    p = sub.add_parser('remove-host', help='Remove a hostname from a user\'s allowed list')
    p.add_argument('--username', required=True)
    p.add_argument('--hostname', required=True)

    args = parser.parse_args()
    commands = {
        'add-user': cmd_add_user,
        'list-users': cmd_list_users,
        'disable-user': cmd_disable_user,
        'enable-user': cmd_enable_user,
        'remove-user': cmd_remove_user,
        'update-password': cmd_update_password,
        'add-host': cmd_add_host,
        'remove-host': cmd_remove_host,
    }
    commands[args.command](args)


if __name__ == '__main__':
    main()
