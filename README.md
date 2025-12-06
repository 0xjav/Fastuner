# Fastuner

**One-Click Model Deployment & Fine-Tuning Service for AWS SageMaker**

Fastuner enables developers to deploy and fine-tune open-source LLMs with a single command. Built for production, optimized for cost.

## Features (V0) ✅

- **One-click deployment** of Hugging Face models to SageMaker
- **LoRA/QLoRA fine-tuning** with automatic dataset validation
- **Multi-tenant adapter serving** on shared base model endpoints
- **Ephemeral compute** with TTL-driven cleanup for cost optimization
- **Task-aware dataset splitting** with stratification support
- **CLI-first** developer experience
- **Infrastructure as Code** with Terraform
- **Comprehensive tests** with 30+ test cases
- **Cost tracking** and automatic cleanup

## Quick Start

### 1. Deploy Infrastructure
```bash
cd infra/terraform
./deploy.sh
# Copy the outputs to your .env file
```

### 2. Install and Configure
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install
pip install -e .

# Configure .env with AWS credentials from Terraform outputs
```

### 3. Use the CLI
```bash
# Upload dataset
fastuner datasets upload examples/skyrim_ner/skyrim_entities.jsonl \
  --name "skyrim_gliner2" \
  --task-type text_generation

# Fine-tune with QLoRA
fastuner finetune start \
  --model-id glineur/gliner_medium-v2.1 \
  --dataset-id ds_xxx \
  --adapter-name skyrim_entities_v1 \
  --method qlora

# Deploy adapter
fastuner deployments create --adapter-id adp_xxx

# Run inference
fastuner inference run \
  --model-id glineur/gliner_medium-v2.1 \
  --adapter skyrim_entities_v1 \
  --input "Alduin destroyed Helgen"

# Monitor costs
fastuner cleanup cost-report
```

## Architecture

- **Control Plane**: FastAPI + SQLite (V0) / PostgreSQL (production)
- **Compute Plane**: SageMaker Training Jobs + LMI Inference Endpoints
- **Storage**: S3 (datasets, adapters, artifacts)
- **Cleanup**: Lambda + EventBridge (scheduled TTL-based cleanup)
- **Auth**: Query params (V0) / AWS Cognito JWT (production)
- **Infrastructure**: Terraform for AWS resource management

## Dataset Schema (V0)

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

- **V0** (Current): CLI + LoRA fine-tuning + multi-tenant serving
- **V1**: Web UI, canary deployments, async inference
- **V2**: Full fine-tuning, RLHF/DPO, experiment tracking

## License

MIT

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)
