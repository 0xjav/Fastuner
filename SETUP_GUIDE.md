# Fastuner Setup Guide

Complete step-by-step instructions to get Fastuner running on your machine.

---

## Prerequisites

- **Python 3.11+** installed
- **AWS Account** with admin access
- **AWS CLI** installed ([Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
- **Terraform 1.5+** installed ([Install Guide](https://developer.hashicorp.com/terraform/install))
- **Git** installed

---

## Step 1: AWS Credentials Setup

### Option A: Using AWS CLI (Recommended)

1. **Get your AWS credentials** from the AWS Console:
   - Go to: https://console.aws.amazon.com/iam/
   - Click **Users** → Your username → **Security credentials**
   - Click **Create access key**
   - Save the **Access Key ID** and **Secret Access Key**

2. **Configure AWS CLI**:
   ```bash
   aws configure
   ```

   Enter:
   - AWS Access Key ID: `AKIAXXXXXXXXXXXXXXXX`
   - AWS Secret Access Key: `your-secret-key`
   - Default region name: `us-west-2` (or your preferred region)
   - Default output format: `json`

3. **Verify configuration**:
   ```bash
   aws sts get-caller-identity
   ```

   You should see your AWS account ID and user ARN.

### Option B: Using Environment Variables

Alternatively, you can set environment variables:

**macOS/Linux:**
```bash
export AWS_ACCESS_KEY_ID="AKIAXXXXXXXXXXXXXXXX"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-west-2"
```

**Windows (Command Prompt):**
```cmd
set AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
set AWS_SECRET_ACCESS_KEY=your-secret-key
set AWS_DEFAULT_REGION=us-west-2
```

**Windows (PowerShell):**
```powershell
$env:AWS_ACCESS_KEY_ID="AKIAXXXXXXXXXXXXXXXX"
$env:AWS_SECRET_ACCESS_KEY="your-secret-key"
$env:AWS_DEFAULT_REGION="us-west-2"
```

---

## Step 2: Clone and Install Fastuner

1. **Clone the repository**:
   ```bash
   git clone https://github.com/0xjav/Fastuner.git
   cd Fastuner
   ```

2. **Create virtual environment**:

   **macOS/Linux:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   **Windows:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -e .
   ```

4. **Verify installation**:
   ```bash
   fastuner --version
   ```

---

## Step 3: Deploy AWS Infrastructure

1. **Navigate to Terraform directory**:
   ```bash
   cd infra/terraform
   ```

2. **Make deploy script executable** (macOS/Linux only):
   ```bash
   chmod +x deploy.sh
   ```

3. **Run deployment**:

   **macOS/Linux:**
   ```bash
   ./deploy.sh
   ```

   **Windows (use Git Bash or WSL):**
   ```bash
   bash deploy.sh
   ```

   Or manually:
   ```bash
   # Initialize Terraform
   terraform init

   # Review plan
   terraform plan

   # Apply infrastructure
   terraform apply
   ```

4. **Save the outputs**:

   After deployment, you'll see output like:
   ```
   datasets_bucket_name = "fastuner-datasets-abc123"
   adapters_bucket_name = "fastuner-adapters-def456"
   sagemaker_execution_role_arn = "arn:aws:iam::123456789012:role/..."
   ```

   **Copy these values!** You'll need them in the next step.

---

## Step 4: Configure Environment

1. **Go back to project root**:
   ```bash
   cd ../..  # Back to Fastuner/
   ```

2. **Create `.env` file**:
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` file** with your AWS details:

   Open `.env` in your text editor and update:

   ```bash
   # AWS Configuration
   AWS_REGION=us-west-2  # Your AWS region
   AWS_ACCOUNT_ID=123456789012  # Your AWS account ID (from terraform output)

   # S3 Buckets (from terraform output)
   S3_DATASETS_BUCKET=fastuner-datasets-abc123
   S3_ADAPTERS_BUCKET=fastuner-adapters-def456

   # SageMaker (from terraform output)
   SAGEMAKER_EXECUTION_ROLE_ARN=arn:aws:iam::123456789012:role/fastuner-sagemaker-execution-role

   # Database (default - no changes needed for V0)
   DATABASE_URL=sqlite:///./fastuner.db

   # Deployment defaults
   DEFAULT_TTL_SECONDS=3600
   ```

4. **Initialize database**:
   ```bash
   alembic upgrade head
   ```

   You should see: "Running upgrade ... -> ..., initial schema"

---

## Step 5: Test the Setup

### Test 1: Upload Sentiment Dataset

```bash
fastuner datasets upload examples/sentiment_analysis/sentiment.jsonl \
  --name "sentiment_test" \
  --task-type classification
```

**Expected output:**
```
✓ Dataset uploaded successfully!

Dataset ID: ds_abc123def456
Name: sentiment_test
Task Type: classification
Total Samples: 100
Train: 80 | Validation: 10 | Test: 10
```

### Test 2: List Datasets

```bash
fastuner datasets list
```

You should see your uploaded dataset.

### Test 3: Start Fine-Tuning Job

```bash
fastuner finetune start \
  --model-id distilbert-base-uncased \
  --dataset-id ds_abc123def456 \
  --adapter-name sentiment_adapter_v1 \
  --method lora \
  --num-epochs 3
```

**Expected output:**
```
✓ Fine-tuning job started!

Job ID: ftj_xyz789
Model: distilbert-base-uncased
Dataset: ds_abc123def456
Adapter Name: sentiment_adapter_v1
Status: RUNNING
```

### Test 4: Check Job Status

```bash
fastuner finetune get ftj_xyz789
```

---

## Step 6: Deploy and Run Inference

Once training completes (check with `fastuner finetune get <job-id>`):

### Deploy the Adapter

```bash
fastuner deployments create --adapter-id adp_abc123
```

**Expected output:**
```
✓ Deployment created!

Deployment ID: dep_xyz789
Endpoint: fastuner-tenant-sentiment-abc123
Status: CREATING
```

### Wait for Endpoint (takes 5-10 minutes)

```bash
fastuner deployments get dep_xyz789
```

Wait until status is **ACTIVE**.

### Run Inference

```bash
fastuner inference run \
  --model-id distilbert-base-uncased \
  --adapter sentiment_adapter_v1 \
  --input "This product is absolutely amazing!"
```

**Expected output:**
```
✓ Inference complete!

Output: positive
Latency: 145ms
```

---

## Step 7: Monitor Costs

### Check Active Deployments

```bash
fastuner cleanup cost-report
```

**Expected output:**
```
💰 Cost Report

Active Deployments: 1
Total Hourly Cost: $1.408
Est. Monthly Cost: $1028.64

┌─────────────────────────┬─────────────┬───────┬─────────┬──────────┬──────────┐
│ Endpoint                │ Instance    │ Count │ $/hour  │ Last Used│ Idle Time│
├─────────────────────────┼─────────────┼───────┼─────────┼──────────┼──────────┤
│ fastuner-tenant-sent... │ ml.g5.xlarge│ 1     │ $1.408  │ 14:32:15 │ 5m       │
└─────────────────────────┴─────────────┴───────┴─────────┴──────────┴──────────┘
```

### Manual Cleanup (if needed)

```bash
# Delete specific deployment
fastuner deployments delete dep_xyz789

# Or run automatic cleanup now
fastuner cleanup run
```

**Note:** Lambda automatically cleans up idle endpoints every 5 minutes based on TTL.

---

## Common Issues

### Issue 1: "AWS credentials not configured"

**Solution:** Run `aws configure` or set environment variables (see Step 1).

### Issue 2: "Terraform command not found"

**Solution:** Install Terraform: https://developer.hashicorp.com/terraform/install

### Issue 3: "Permission denied" on deploy.sh

**Solution (macOS/Linux):**
```bash
chmod +x infra/terraform/deploy.sh
```

### Issue 4: Dataset upload fails

**Solution:** Check that:
1. Your `.env` file has the correct S3 bucket names
2. Your AWS credentials have S3 access
3. The JSONL file has valid format (see examples/)

### Issue 5: Training job fails

**Solution:** Check:
1. SageMaker execution role has correct permissions
2. Model ID is valid (from Hugging Face)
3. Instance type is available in your region

### Issue 6: Endpoint deployment stuck

**Solution:**
1. Check AWS Console → SageMaker → Endpoints
2. Look for error messages
3. Common issue: Instance type not available in region
   - Try different instance: `--instance-type ml.m5.xlarge`

---

## File Locations

- **AWS Credentials**: `~/.aws/credentials` (Linux/macOS) or `%USERPROFILE%\.aws\credentials` (Windows)
- **Environment Config**: `.env` (in project root)
- **Database**: `fastuner.db` (in project root, created automatically)
- **Sample Datasets**: `examples/` directory

---

## Quick Command Reference

```bash
# Datasets
fastuner datasets upload <file> --name <name> --task-type <type>
fastuner datasets list
fastuner datasets get <id>
fastuner datasets delete <id>

# Fine-tuning
fastuner finetune start --model-id <model> --dataset-id <id> --adapter-name <name>
fastuner finetune list
fastuner finetune get <job-id>
fastuner finetune cancel <job-id>

# Deployments
fastuner deployments create --adapter-id <id>
fastuner deployments list
fastuner deployments get <id>
fastuner deployments delete <id>

# Inference
fastuner inference run --model-id <model> --adapter <name> --input "<text>"

# Cleanup
fastuner cleanup status
fastuner cleanup cost-report
fastuner cleanup run [--dry-run]
```

---

## Next Steps

1. Try the **Skyrim NER example**: `examples/skyrim_ner/`
2. Create your own dataset (see Dataset Schema in README)
3. Experiment with different models and hyperparameters
4. Set up automatic cleanup schedules

---

## Getting Help

- **Documentation**: See [README.md](README.md)
- **Issues**: https://github.com/0xjav/Fastuner/issues
- **Examples**: Check `examples/` directory

---

## Cleaning Up

When you're done testing:

### Delete Deployments
```bash
fastuner deployments list
fastuner deployments delete <deployment-id>
```

### Destroy Infrastructure (optional)
```bash
cd infra/terraform
terraform destroy
```

**Warning:** This deletes all S3 buckets and data!

---

**You're all set!** 🚀 Happy fine-tuning!
