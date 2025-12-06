# Terraform outputs for Fastuner

output "datasets_bucket_name" {
  description = "Name of the datasets S3 bucket"
  value       = aws_s3_bucket.datasets.id
}

output "datasets_bucket_arn" {
  description = "ARN of the datasets S3 bucket"
  value       = aws_s3_bucket.datasets.arn
}

output "adapters_bucket_name" {
  description = "Name of the adapters S3 bucket"
  value       = aws_s3_bucket.adapters.id
}

output "adapters_bucket_arn" {
  description = "ARN of the adapters S3 bucket"
  value       = aws_s3_bucket.adapters.arn
}

output "sagemaker_execution_role_arn" {
  description = "ARN of the SageMaker execution role"
  value       = aws_iam_role.sagemaker_execution.arn
}

output "lambda_cleanup_function_name" {
  description = "Name of the Lambda cleanup function"
  value       = aws_lambda_function.cleanup.function_name
}

output "cleanup_schedule_expression" {
  description = "Schedule expression for cleanup"
  value       = aws_cloudwatch_event_rule.cleanup_schedule.schedule_expression
}

output "env_configuration" {
  description = "Environment variables for .env file"
  value = <<-EOT
    # Add these to your .env file:
    AWS_REGION=${var.aws_region}
    S3_DATASETS_BUCKET=${aws_s3_bucket.datasets.id}
    S3_ADAPTERS_BUCKET=${aws_s3_bucket.adapters.id}
    SAGEMAKER_EXECUTION_ROLE_ARN=${aws_iam_role.sagemaker_execution.arn}
  EOT
}
