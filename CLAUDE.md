# DDNS Route53 — Developer Notes

## Project

DynDNS2-compatible DDNS service built on AWS Lambda (containers), API Gateway, DynamoDB, and Route53. Replaces the legacy direct-proxy implementation (`xo1u3hdvy7`) in account 771294529343.

## AWS Context

- **Account:** 771294529343
- **Profile:** `cuppett` (use `--profile cuppett` or `AWS_PROFILE=cuppett`)
- **Region:** us-east-1
- **Zones under management:**
  - `cuppett.com` → `ZYD1DIOLOG0D0` (PRODUCTION — do not touch during testing)
  - `sanyshyn.com` → `Z08718261I7WZAVTSSBXA`
  - `cuppett.dev` → `Z07412393IK1HEEHEGRPG` (use for testing)

## Testing Safety

**Always use `cuppett.dev` for integration testing.** `cuppett.com` and `google.cuppett.com` are active production DDNS records used for real IP connectivity. Disrupting them causes actual downtime.

## Running Tests

```bash
pip install -r tests/requirements.txt
pytest tests/ -v
```

Tests use `moto` to mock AWS services. No real AWS calls during unit tests.

## Building the Container

```bash
podman build -t ddns-route53:latest -f Containerfile .
```

## Key Files

| File | Purpose |
|------|---------|
| `src/validators.py` | FQDN, IPv4, User-Agent validation |
| `src/dns_utils.py` | Route53 get/upsert helpers |
| `src/authorizer.py` | REQUEST authorizer (Basic Auth + DynamoDB + bcrypt) |
| `src/update_handler.py` | `/nic/update` Lambda (full DynDNS2 protocol) |
| `src/checkip_handler.py` | `/checkip` Lambda |
| `scripts/manage_users.py` | CLI for managing DynamoDB user records |
| `cloudformation/ddns_service.yaml` | Main service stack (ECR repo managed separately via aws-codebuild-podman) |

## DynDNS2 Response Codes

`good {IP}`, `nochg {IP}`, `badauth`, `notfqdn`, `nohost`, `numhost`, `badagent`, `dnserr`, `911`

All responses are HTTP 200 with Content-Type: text/plain. Errors are in the body.
