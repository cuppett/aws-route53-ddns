# DDNS Route53

Dynamic DNS update service using API Gateway with a direct AWS service proxy
integration to Route53. Clients issue a single GET request to update an A record
in any hosted zone they supply as a path parameter.

## Architecture

```
Client
  │  GET /{zone_id}/nic/update?hostname=X&myip=Y
  │  Authorization: <shared-token>
  ▼
API Gateway (REST, REGIONAL)
  ├─ TOKEN authorizer Lambda
  │    reads shared credential from SSM SecureString DDNS_ROUTE53_AUTHORIZATION
  │    returns Allow/Deny (no caching)
  └─ AWS service proxy integration
       POST route53:ChangeResourceRecordSets on hostedzone/{zone_id}/rrset/
       returns hardcoded "good"
```

## Prerequisites

- AWS CLI configured with a profile that has CloudFormation and IAM permissions
- SSM SecureString parameter `DDNS_ROUTE53_AUTHORIZATION` pre-created with the
  shared authorization token

## Deploy

```bash
aws cloudformation deploy \
  --template-file cloudformation/ddns_service.yaml \
  --stack-name ddns-route53 \
  --capabilities CAPABILITY_NAMED_IAM \
  --profile <your-profile>
```

## Usage

```bash
API=https://APIGW_ID.execute-api.us-east-1.amazonaws.com/prod
ZONE_ID=Z0123456789ABCDEFGHIJ

curl -H "Authorization: <shared-token>" \
  "$API/$ZONE_ID/nic/update?hostname=home.example.com&myip=1.2.3.4"
# → good
```

Limitations: always returns `good`, no `nochg` detection, no input validation,
single shared credential for all clients/zones.
