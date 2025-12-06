# Terraform configuration for Fastuner V0

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Fastuner"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# S3 bucket for datasets
resource "aws_s3_bucket" "datasets" {
  bucket_prefix = "fastuner-datasets-"
  force_destroy = var.environment == "dev" # Allow deletion in dev

  tags = {
    Name = "Fastuner Datasets"
  }
}

resource "aws_s3_bucket_versioning" "datasets" {
  bucket = aws_s3_bucket.datasets.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "datasets" {
  bucket = aws_s3_bucket.datasets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 bucket for adapters
resource "aws_s3_bucket" "adapters" {
  bucket_prefix = "fastuner-adapters-"
  force_destroy = var.environment == "dev"

  tags = {
    Name = "Fastuner Adapters"
  }
}

resource "aws_s3_bucket_versioning" "adapters" {
  bucket = aws_s3_bucket.adapters.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "adapters" {
  bucket = aws_s3_bucket.adapters.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM role for SageMaker
resource "aws_iam_role" "sagemaker_execution" {
  name = "fastuner-sagemaker-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "sagemaker_s3_access" {
  name = "fastuner-sagemaker-s3-access"
  role = aws_iam_role.sagemaker_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.datasets.arn,
          "${aws_s3_bucket.datasets.arn}/*",
          aws_s3_bucket.adapters.arn,
          "${aws_s3_bucket.adapters.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

# IAM role for Lambda cleanup function
resource "aws_iam_role" "lambda_cleanup" {
  name = "fastuner-lambda-cleanup-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_cleanup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_sagemaker_access" {
  name = "fastuner-lambda-sagemaker-access"
  role = aws_iam_role.lambda_cleanup.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sagemaker:DescribeEndpoint",
          "sagemaker:DeleteEndpoint",
          "sagemaker:DescribeEndpointConfig",
          "sagemaker:DeleteEndpointConfig",
          "sagemaker:DescribeModel",
          "sagemaker:DeleteModel"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda function for cleanup (placeholder - actual code needs to be packaged)
resource "aws_lambda_function" "cleanup" {
  filename      = "lambda_function.zip" # You need to create this
  function_name = "fastuner-cleanup"
  role          = aws_iam_role.lambda_cleanup.arn
  handler       = "fastuner.lambda.cleanup_handler.handler"
  runtime       = "python3.11"
  timeout       = 300 # 5 minutes

  environment {
    variables = {
      DATABASE_URL = var.database_url
      DRY_RUN      = "false"
    }
  }
}

# EventBridge rule for scheduled cleanup (every 5 minutes)
resource "aws_cloudwatch_event_rule" "cleanup_schedule" {
  name                = "fastuner-cleanup-schedule"
  description         = "Trigger cleanup every 5 minutes"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "cleanup_lambda" {
  rule      = aws_cloudwatch_event_rule.cleanup_schedule.name
  target_id = "CleanupLambda"
  arn       = aws_lambda_function.cleanup.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cleanup.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cleanup_schedule.arn
}

# CloudWatch log group for Lambda
resource "aws_cloudwatch_log_group" "lambda_cleanup" {
  name              = "/aws/lambda/${aws_lambda_function.cleanup.function_name}"
  retention_in_days = 7
}
