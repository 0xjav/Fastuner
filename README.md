# Fastuner

**One-Click Model Deployment & Fine-Tuning Service for AWS SageMaker**

Fastuner enables developers to deploy and fine-tune open-source LLMs with a single command. Built for production, optimized for cost.

## Features (V0)

- **One-click deployment** of Hugging Face models to SageMaker
- **LoRA/QLoRA fine-tuning** with automatic dataset validation
- **Multi-tenant adapter serving** on shared base model endpoints
- **Ephemeral compute** with TTL-driven cleanup for cost optimization
- **Task-aware dataset splitting** with stratification support
- **CLI-first** developer experience

## Quick Start

```bash
# Install
pip install fastuner

# Upload dataset
fastuner datasets upload data.jsonl --task-type text_generation

# Fine-tune with LoRA
fastuner finetune start \
  --model-id meta-llama/Llama-2-7b-chat-hf \
  --dataset-id ds_xxx \
  --method qlora \
  --auto-deploy

# Run inference
fastuner inference run \
  --model-id meta-llama/Llama-2-7b-chat-hf \
  --adapter sentiment_v1 \
  --input "Great service!"
```

## Architecture

- **Control Plane**: FastAPI + PostgreSQL + AWS Step Functions
- **Compute Plane**: SageMaker Training Jobs + LMI Inference Endpoints
- **Storage**: S3 (datasets, adapters, artifacts)
- **Auth**: AWS Cognito JWT

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

### Running the Service

```bash
# Run API server (with auto-reload)
uvicorn fastuner.api.main:app --reload

# Run tests
pytest tests/ -v

# Run CLI
fastuner --help
```

### Infrastructure Deployment

```bash
cd infra/cdk
cdk deploy
```

For detailed development instructions, see [CONTRIBUTING.md](CONTRIBUTING.md)

## Roadmap

- **V0** (Current): CLI + LoRA fine-tuning + multi-tenant serving
- **V1**: Web UI, canary deployments, async inference
- **V2**: Full fine-tuning, RLHF/DPO, experiment tracking

## License

MIT

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)
