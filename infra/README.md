# Fastuner Infrastructure

Infrastructure as Code for deploying Fastuner to AWS.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured
- Terraform v1.5+ installed

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS Cloud                             │
│                                                               │
│  ┌──────────────┐       ┌──────────────┐                    │
│  │   S3 Bucket  │       │  SageMaker   │                    │
│  │   Datasets   │◄──────┤   Training   │                    │
│  │   Adapters   │       │     Jobs     │                    │
│  └──────────────┘       └──────────────┘                    │
│         │                                                     │
│         │               ┌──────────────┐                    │
│         └───────────────►  SageMaker   │                    │
│                         │  Endpoints   │                    │
│                         │  (Inference) │                    │
│                         └──────────────┘                    │
│                                                               │
│  ┌──────────────┐       ┌──────────────┐                    │
│  │  EventBridge │───────►    Lambda    │                    │
│  │   Schedule   │       │   Cleanup    │                    │
│  └──────────────┘       └──────────────┘                    │
│                                                               │
│  ┌──────────────┐                                            │
│  │  CloudWatch  │  (Metrics & Logs)                         │
│  └──────────────┘                                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. S3 Storage
- Dataset storage (raw, train, val, test splits)
- Adapter artifacts
- Training job outputs

### 2. SageMaker
- Training jobs for fine-tuning
- Inference endpoints for serving
- Execution role with required permissions

### 3. Lambda + EventBridge
- Scheduled cleanup of stale endpoints (every 5 minutes)
- TTL-based cost optimization

### 4. IAM Roles
- SageMaker execution role
- Lambda execution role

## Deployment

### Option 1: Terraform (Recommended)

```bash
cd infra/terraform

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Deploy infrastructure
terraform apply

# Get outputs
terraform output
```

### Option 2: CloudFormation

```bash
cd infra/cloudformation

# Deploy stack
aws cloudformation deploy \
  --template-file fastuner-stack.yaml \
  --stack-name fastuner-v0 \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    Environment=dev

# Get outputs
aws cloudformation describe-stacks \
  --stack-name fastuner-v0 \
  --query 'Stacks[0].Outputs'
```

## Configuration

After deployment, update your `.env` file with the infrastructure outputs:

```bash
AWS_REGION=us-west-2
AWS_ACCOUNT_ID=123456789012
S3_DATASETS_BUCKET=fastuner-datasets-XXXXXXXX
S3_ADAPTERS_BUCKET=fastuner-adapters-XXXXXXXX
SAGEMAKER_EXECUTION_ROLE_ARN=arn:aws:iam::123456789012:role/fastuner-sagemaker-role
```

## Cost Estimation

**V0 Development/Testing** (per month):
- S3 Storage: ~$1-5 (100 GB)
- SageMaker Training: Pay per use (~$1-3/hour per job)
- SageMaker Endpoints: ~$1.4/hour (ml.g5.xlarge) * hours active
- Lambda + EventBridge: <$1

**Important**: Use TTL-based cleanup to minimize endpoint costs!

## Cleanup

To destroy all infrastructure:

```bash
# Terraform
cd infra/terraform
terraform destroy

# CloudFormation
aws cloudformation delete-stack --stack-name fastuner-v0
```

**Warning**: This will delete all S3 buckets and data!
