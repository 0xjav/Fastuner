#!/bin/bash
# Deploy Fastuner infrastructure to AWS using Terraform

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Fastuner Infrastructure Deployment ===${NC}\n"

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: Terraform is not installed${NC}"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}\n"

# Package Lambda function
echo "Packaging Lambda function..."
cd ../../
pip install -t /tmp/lambda_package -r requirements.txt
cd /tmp/lambda_package
zip -r ../lambda_function.zip .
cd -
cp fastuner/lambda/cleanup_handler.py /tmp/lambda_package/
cd /tmp/lambda_package
zip -g ../lambda_function.zip cleanup_handler.py
mv /tmp/lambda_function.zip infra/terraform/
cd infra/terraform
echo -e "${GREEN}✓ Lambda function packaged${NC}\n"

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Select workspace (optional)
read -p "Enter environment (dev/staging/prod) [dev]: " ENV
ENV=${ENV:-dev}

# Plan deployment
echo -e "\n${YELLOW}Planning infrastructure changes...${NC}"
terraform plan -var="environment=$ENV" -out=tfplan

# Confirm deployment
echo -e "\n${YELLOW}Ready to deploy infrastructure.${NC}"
read -p "Continue with deployment? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

# Apply deployment
echo -e "\n${GREEN}Deploying infrastructure...${NC}"
terraform apply tfplan

# Get outputs
echo -e "\n${GREEN}=== Deployment Complete! ===${NC}\n"
terraform output env_configuration

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Copy the environment variables above to your .env file"
echo "2. Update AWS_ACCOUNT_ID in .env"
echo "3. Run 'fastuner datasets upload' to test the pipeline"

echo -e "\n${GREEN}Done!${NC}"
