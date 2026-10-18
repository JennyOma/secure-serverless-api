
provider "aws" {
  region = "eu-north-1"
}

# DynamoDB: store client requests
resource "aws_dynamodb_table" "users_table" {
  name         = "ClientRequestsTf"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "userId"

  attribute {
    name = "userId"
    type = "S"
  }
}

# Package the Python Lambda function
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../src/lambda_function.py"
  output_path = "${path.module}/lambda.zip"
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "secure-client-requests-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

# Lambda permission to write CloudWatch logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda permissions for DynamoDB
resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "secure-client-requests-dynamodb-access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:GetItem",
        "dynamodb:PutItem"
      ]
      Resource = aws_dynamodb_table.users_table.arn
    }]
  })
}

# Lambda function
resource "aws_lambda_function" "greeter" {
  function_name    = "secure-client-requests"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 10

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.users_table.name
    }
  }
}

# Cognito user pool
resource "aws_cognito_user_pool" "clients" {
  name = "secure-client-requests-users"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
  }
}

# Cognito app client
resource "aws_cognito_user_pool_client" "api_client" {
  name         = "secure-client-requests-app"
  user_pool_id = aws_cognito_user_pool.clients.id

  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]

  prevent_user_existence_errors = "ENABLED"
}

# API Gateway HTTP API
resource "aws_apigatewayv2_api" "greeter_api" {
  name          = "secure-client-requests-api"
  protocol_type = "HTTP"
}

# Cognito JWT authorizer
resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id          = aws_apigatewayv2_api.greeter_api.id
  authorizer_type = "JWT"
  name            = "cognito-jwt-authorizer"

  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    audience = [aws_cognito_user_pool_client.api_client.id]
    issuer   = "https://cognito-idp.eu-north-1.amazonaws.com/${aws_cognito_user_pool.clients.id}"
  }
}

# Connect API Gateway to Lambda
resource "aws_apigatewayv2_integration" "greeter_integration" {
  api_id                 = aws_apigatewayv2_api.greeter_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.greeter.invoke_arn
  payload_format_version = "2.0"
}

# Create a client request
resource "aws_apigatewayv2_route" "create_request" {
  api_id             = aws_apigatewayv2_api.greeter_api.id
  route_key          = "POST /requests"
  target             = "integrations/${aws_apigatewayv2_integration.greeter_integration.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

# Retrieve a client request
resource "aws_apigatewayv2_route" "get_request" {
  api_id             = aws_apigatewayv2_api.greeter_api.id
  route_key          = "GET /requests/{requestId}"
  target             = "integrations/${aws_apigatewayv2_integration.greeter_integration.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

# Deploy API changes automatically
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.greeter_api.id
  name        = "$default"
  auto_deploy = true
}

# Allow this API Gateway to invoke Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.greeter.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.greeter_api.execution_arn}/*/*"
}

# Outputs
output "api_url" {
  value = aws_apigatewayv2_api.greeter_api.api_endpoint
}

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.clients.id
}

output "cognito_app_client_id" {
  value = aws_cognito_user_pool_client.api_client.id
}

# CloudWatch alarm for Lambda errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "secure-client-requests-lambda-errors"
  alarm_description   = "Detects errors in the client requests Lambda"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.greeter.function_name
  }
}
