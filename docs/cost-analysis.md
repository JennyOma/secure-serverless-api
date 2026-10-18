
# AWS Cost Analysis

## Services Used

| AWS Service | Potential Cost |
|---|---|
| AWS Lambda | Invocations and execution duration |
| API Gateway HTTP API | API requests |
| DynamoDB | On-demand reads, writes and storage |
| Amazon Cognito | Usage depending on applicable pricing tier |
| Amazon CloudWatch | Logs, storage and metric alarms |

## Cost-Control Measures

- DynamoDB uses `PAY_PER_REQUEST` billing.
- Lambda runs only when invoked.
- One CloudWatch error alarm is configured.
- No NAT Gateway, EC2 instance or load balancer is required.
- GitHub Actions validates code without deploying AWS infrastructure.

## Important Notes

This is not a zero-cost guarantee. Charges can arise even during testing, and Free Tier eligibility depends on the AWS account and service.

Before deployment:
1. Check the AWS Billing dashboard and Free Tier usage.
2. Review the Terraform plan for unexpected resources.
3. Set an AWS Budget alert where appropriate.
4. Check the current AWS pricing for the deployment region, `eu-north-1`.

After testing, review costs and decide whether to retain or explicitly destroy Project 05 resources. Never destroy Project 04 infrastructure as part of Project 05 cleanup.
