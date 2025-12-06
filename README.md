# Fastuner

**One-Click Model Deployment & Fine-Tuning Service for AWS SageMaker**

Fastuner enables developers to deploy and fine-tune open-source LLMs with a single command. Built for production, optimized for cost.

## Features

- **One-click deployment** of Hugging Face models to SageMaker
- **LoRA/QLoRA fine-tuning** with automatic dataset validation
- **Multi-tenant adapter serving** on shared base model endpoints
- **Ephemeral compute** with TTL-driven cleanup for cost optimization
- **Task-aware dataset splitting** with stratification support
- **CLI-first** developer experience
- **Infrastructure as Code** with Terraform
- **Cost tracking** and automatic cleanup

## Quick Start

**New to Fastuner?** → See [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete step-by-step instructions!

### 1. Configure AWS Credentials
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region
```

### 2. Install Fastuner
```bash
git clone https://github.com/0xjav/Fastuner.git
cd Fastuner
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
```

### 3. Deploy Infrastructure
```bash
cd infra/terraform
./deploy.sh  # Creates S3 buckets, IAM roles, Lambda function
# Copy the outputs to your .env file
```

### 4. Use the CLI
```bash
# Upload dataset
fastuner datasets upload examples/sentiment_analysis/sentiment.jsonl \
  --name "sentiment_v1" \
  --task-type classification

# Fine-tune with LoRA
fastuner finetune start \
  --model-id distilbert-base-uncased \
  --dataset-id ds_xxx \
  --adapter-name sentiment_adapter \
  --method lora

# Deploy adapter
fastuner deployments create --adapter-id adp_xxx

# Run inference
fastuner inference run \
  --model-id distilbert-base-uncased \
  --adapter sentiment_adapter \
  --input "This product is amazing!"

# Monitor costs
fastuner cleanup cost-report
```

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions and troubleshooting!

## Architecture

- **Control Plane**: FastAPI + SQLAlchemy + SQLite
- **Compute Plane**: SageMaker Training Jobs + LMI Inference Endpoints
- **Storage**: S3 (datasets, adapters, artifacts)
- **Cleanup**: Lambda + EventBridge (scheduled TTL-based cleanup)
- **Infrastructure**: Terraform for AWS resource management

## Dataset Schema

```jsonl
{"input_text": "Classify sentiment: I love this product!", "target_text": "positive"}
{"input_text": "Classify sentiment: Terrible experience.", "target_text": "negative"}
```

Requirements:
- Minimum 100 unique samples
- UTF-8 strings only
- `input_text`: 1-8192 chars
- `target_text`: 1-2048 chars

## Development

### Initial Setup

**IMPORTANT: Always use a virtual environment!**

```bash
# Clone repository
git clone https://github.com/0xjav/Fastuner.git
cd Fastuner

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -e .

# Set up environment
cp .env.example .env
# Edit .env with your AWS credentials

# Initialize database (SQLite - no setup needed!)
alembic upgrade head
```

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=fastuner tests/

# Run specific test file
pytest tests/test_validator.py -v
```

### Infrastructure Deployment

```bash
cd infra/terraform
./deploy.sh
```

This will create:
- S3 buckets for datasets and adapters
- SageMaker execution role
- Lambda cleanup function
- EventBridge schedule for automatic cleanup

For detailed development instructions, see [CONTRIBUTING.md](CONTRIBUTING.md)

## Roadmap

- ✅ CLI + LoRA/QLoRA fine-tuning + multi-tenant serving
- 🔜 Web UI, canary deployments, async inference
- 🔜 Full fine-tuning, RLHF/DPO, experiment tracking

## License

MIT

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)
