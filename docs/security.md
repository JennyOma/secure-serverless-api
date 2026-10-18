
# Security Design

## Authentication
Amazon Cognito authenticates users. API Gateway uses a JWT authorizer to protect both API routes.

## Authorization
Each request stores the authenticated user's Cognito `sub` identifier as `ownerId`.

When retrieving a request, Lambda checks that the authenticated user owns it. Requests belonging to another user return HTTP 404.

## IAM Permissions
Lambda has permission to:
- Write application logs to CloudWatch.
- Read individual items from the project DynamoDB table.
- Write individual items to the project DynamoDB table.

## Data Protection
- Authentication tokens must never be committed to GitHub.
- AWS credentials must never be stored in source code.
- Public API requests require a valid Cognito JWT.
- DynamoDB encryption at rest is provided by AWS.

## Limitations
- Authentication and ownership checks have passed local unit tests, but require AWS integration testing.
- There is no request rate limiting or AWS WAF configured.
- CloudWatch error alarms do not currently send notifications.
- Additional input size limits and security testing are recommended before production use.

## Deployment Safety
Project 05 uses distinct AWS resource names from Project 04. Terraform state and deployment plans must be checked before any AWS deployment.
