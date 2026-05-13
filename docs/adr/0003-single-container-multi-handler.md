# ADR 0003: Single container image with multiple Lambda handler entry points

**Date:** 2026-05-12  
**Status:** Accepted

## Context

The service requires three Lambda functions: an authorizer, an update handler, and a checkip handler. Each needs Python, boto3, and bcrypt (except checkip). They share utility modules (`validators.py`, `dns_utils.py`).

Options:
1. One container image per Lambda function
2. One container image, multiple entry points (different `ImageConfig.Command` per Lambda)
3. ZIP-based Lambda functions

## Decision

Package all three handlers in a single container image based on `public.ecr.aws/lambda/python:3.13`. CloudFormation sets `ImageConfig.Command` per Lambda to select the handler:
- `["src.authorizer.handler"]`
- `["src.update_handler.handler"]`  
- `["src.checkip_handler.handler"]`

## Consequences

- Single ECR push updates all three Lambdas simultaneously (consistent versioning)
- Smaller total ECR storage than three separate images
- Build pipeline is simpler (one Containerfile, one image tag)
- Image size is slightly larger than strictly necessary for checkip, but the overhead is negligible
- All functions must be redeployed when any handler changes; acceptable given the small codebase
