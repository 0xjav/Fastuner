# Terraform variables for Fastuner

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "database_url" {
  description = "Database connection URL for Lambda"
  type        = string
  sensitive   = true
  default     = ""
}
