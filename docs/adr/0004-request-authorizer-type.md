# ADR 0004: REQUEST-type authorizer instead of TOKEN-type

**Date:** 2026-05-12  
**Status:** Accepted

## Context

The legacy implementation uses a TOKEN-type authorizer that extracts the `Authorization` header and passes it to Lambda. TOKEN authorizers only see the identity source value (a single string), not the full request context.

The new authorizer needs to:
1. Parse HTTP Basic Auth (Base64 decode username:password from the `Authorization` header)
2. Look up the user in DynamoDB
3. Verify bcrypt password
4. Pass `allowed_hosts` to the update handler via authorizer context

The TOKEN type is sufficient for step 1-3, but REQUEST type provides the full event object and is the AWS-recommended approach for new implementations.

## Decision

Use a REQUEST-type authorizer with `method.request.header.Authorization` as the single identity source. This enables API Gateway to cache the auth result by the Authorization header value (300s TTL).

The authorizer Lambda receives the full request context but only uses the Authorization header. The `allowed_hosts` list is serialized as a JSON string in the authorizer context and parsed by the update handler from `event['requestContext']['authorizer']['allowed_hosts']`.

## Consequences

- Cache key is the Authorization header value, so different users with different credentials get independent cache entries
- The update handler does not need to hit DynamoDB for hostname lookups — it receives the pre-authorized allowed_hosts list from the authorizer context
- If a user's allowed_hosts are updated in DynamoDB, the change takes up to 300s to propagate (cache TTL). This is acceptable for a DDNS service.
- Gateway response overrides convert 401/403 (from auth failure) to `200 badauth` for DynDNS2 protocol compliance
