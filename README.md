# Secure Serverless Client Requests API
A serverless REST API built using AWS, Python and Terraform. It allows authenticated users to create client requests and retrieve their status securely.

## Architecture
**Amazon API Gateway → AWS Lambda → Amazon DynamoDB**

Amazon Cognito provides JWT authentication, while Amazon CloudWatch supports logging and error monitoring.

## AWS Services and Tools

- **AWS Lambda:** Runs the Python 3.12 application.
- **Amazon API Gateway:** Exposes REST-style HTTP endpoints.
- **Amazon DynamoDB:** Stores client requests.
- **Amazon Cognito:** Authenticates API users.
- **Amazon CloudWatch:** Collects Lambda logs and monitors errors.
- **AWS IAM:** Controls access between AWS services.
- **Terraform:** Defines AWS infrastructure as code.
- **GitHub Actions:** Runs automated validation and tests.

## API Endpoints
Both endpoints require a valid Cognito JWT.

MethodEndpointDescriptionPOST`/requests`Create a client requestGET`/requests/{requestId}`Retrieve your own request
### Example request

```
{
  "clientName": "Example Client",
  "description": "Requesting technical assistance"
}
```

### Example successful response

```
{
  "message": "Client request created",
  "requestId": "generated-uuid",
  "status": "PENDING"
}
```

## Security

- Cognito JWT authentication protects both API routes.
- Each record stores the authenticated user's identifier.
- Users cannot retrieve records belonging to another user.
- Lambda uses an IAM role with scoped DynamoDB read/write permissions.
- API Gateway invokes Lambda through an explicitly configured permission.

## Testing
Run the Python unit tests:

```
python -m pip install boto3
python -m unittest discover -s tests -v
```
Validate Terraform:

```
terraform -chdir=terraform init -backend=false
terraform -chdir=terraform fmt -check
terraform -chdir=terraform validate
```
GitHub Actions runs these checks automatically on pushes and pull requests.

## Project Status

**Deployed, partially integration-tested and safely decommissioned — October 2026.**

- Successfully deployed 15 AWS resources using Terraform.
- Confirmed the API rejected unauthenticated requests with HTTP 401.
- Passed five Python unit tests.
- GitHub Actions CI pipeline passed.
- Verified Cognito's first-login password challenge.
- Authenticated POST and GET tests were not completed.
- Destroyed all 15 AWS resources and confirmed Terraform state was empty.

The source code remains on GitHub. AWS resources were removed to minimise ongoing costs.
## Future Improvements

- Automated deployment after security approval
- Improved application metrics and alert notifications
- Pagination and request listing
- Request status update functionality
- Additional security and integration tests

## Author
JennyOms's Cloud engineering portfolio project demonstrating AWS serverless architecture, infrastructure as code, security and CI. ```
GitHub: https://github.com/JennyOma
```