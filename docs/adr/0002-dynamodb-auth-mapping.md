# ADR 0002: DynamoDB for authentication and hostname mapping

**Date:** 2026-05-12  
**Status:** Accepted

## Context

The legacy implementation stores a single shared authorization token in SSM Parameter Store (`DDNS_ROUTE53_AUTHORIZATION`). Any client with this token can update any hostname in the allowed zone. There is no per-user or per-hostname restriction beyond IAM.

Requirements:
- Multiple users/devices, each with their own credentials
- Each user authorized for specific hostnames only
- Credentials must be updatable without redeploying infrastructure
- Passwords must be stored securely (hashed)

## Decision

Use DynamoDB with a single table (`DDNSAuthorization`), partition key `username` (String). Each item stores:
- `password_hash`: bcrypt hash (cost 12)
- `enabled`: Boolean kill switch
- `allowed_hosts`: List of `{zone_id, hostname}` maps

Managed via a local CLI tool (`scripts/manage_users.py`). The Lambda authorizer performs a `GetItem` by username, then verifies the password with `bcrypt.checkpw()`.

## Alternatives Considered

- **SSM Parameter per user**: Simpler but no structured hostname mapping; updating requires IAM access to SSM
- **Secrets Manager**: Better for secrets rotation but more expensive and overkill for this use case
- **Cognito**: Overengineered; adds significant complexity for a small number of users

## Consequences

- DynamoDB `GetItem` on each auth request (~1ms); amortized by 300s authorizer cache
- PAY_PER_REQUEST billing makes cost negligible at DDNS update frequencies
- `allowed_hosts` embedded in the user item (not normalized) because the list is always small and always read as a whole
- bcrypt at cost 12 adds ~250ms to the authorizer cold start; warm authorizer cache makes this acceptable
