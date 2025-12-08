"""
SageMaker training script for LoRA/QLoRA fine-tuning using PEFT.

This script:
- Loads datasets from SageMaker input channels
- Applies LoRA configuration using PEFT
- Fine-tunes with Hugging Face Trainer
- Saves adapter weights to S3
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List

import boto3
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
from datasets import Dataset as HFDataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_jsonl(file_path: str) -> List[Dict]:
    """Load JSONL file"""
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data


def prepare_generation_dataset(
    records: List[Dict],
    tokenizer,
    max_length: int = 2048,
):
    """Prepare dataset for text generation (instruction tuning)"""
    # Format: <input_text>\n\n<target_text>
    texts = []
    for r in records:
        # Instruction-response format
        text = f"{r['input_text']}\n\n{r['target_text']}{tokenizer.eos_token}"
        texts.append(text)

    encodings = tokenizer(
        texts,
        truncation=True,
        padding=False,  # Dynamic padding in data collator
        max_length=max_length,
    )

    # For causal LM, labels are the same as input_ids
    return HFDataset.from_dict({
        "input_ids": encodings["input_ids"],
        "attention_mask": encodings["attention_mask"],
    })


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser()

    # Model configuration
    parser.add_argument("--base_model_id", type=str, default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--adapter_name", type=str, default="default_adapter")
    parser.add_argument("--method", type=str, default="lora")

    # Training parameters
    parser.add_argument("--learning_rate", type=float, default=0.0002)
    parser.add_argument("--num_epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--gradient_accumulation_steps", type=int, default=4)

    # LoRA configuration
    parser.add_argument("--lora_rank", type=int, default=16)
    parser.add_argument("--lora_alpha", type=int, default=32)
    parser.add_argument("--lora_dropout", type=float, default=0.05)
    parser.add_argument("--lora_target_modules", type=str, default="q_proj,v_proj")

    # QLoRA configuration
    parser.add_argument("--use_4bit", type=str, default="false")
    parser.add_argument("--bnb_4bit_compute_dtype", type=str, default="float16")
    parser.add_argument("--bnb_4bit_quant_type", type=str, default="nf4")

    # Paths
    parser.add_argument("--output_dir", type=str, default="/opt/ml/model")

    args = parser.parse_args()
    return args


def main():
    """Main training function"""

    # Parse arguments
    args = parse_args()

    # Convert string boolean
    use_4bit = args.use_4bit.lower() in ["true", "1", "yes"]

    # Parse target modules
    lora_target_modules = [m.strip() for m in args.lora_target_modules.split(",")]

    # Auto-detect target modules based on model architecture
    if lora_target_modules == ["q_proj", "v_proj"]:
        # Most causal LMs (Llama, Qwen, etc.) use q_proj, k_proj, v_proj, o_proj
        lora_target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]
        logger.info("Using standard causal LM target modules: q_proj, k_proj, v_proj, o_proj")

    # SageMaker paths (from environment)
    train_dir = os.environ.get("SM_CHANNEL_TRAIN", "/opt/ml/input/data/train")
    val_dir = os.environ.get("SM_CHANNEL_VALIDATION", "/opt/ml/input/data/validation")
    test_dir = os.environ.get("SM_CHANNEL_TEST", "/opt/ml/input/data/test")
    model_dir = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")
    output_dir = os.environ.get("SM_OUTPUT_DATA_DIR", "/opt/ml/output")

    logger.info(f"Starting training with base model: {args.base_model_id}")
    logger.info(f"LoRA config: rank={args.lora_rank}, alpha={args.lora_alpha}, dropout={args.lora_dropout}")
    logger.info(f"Target modules: {lora_target_modules}")
    logger.info(f"Use 4-bit: {use_4bit}")
    logger.info(f"Train dir: {train_dir}")
    logger.info(f"Val dir: {val_dir}")
    logger.info(f"Test dir: {test_dir}")

    # Load datasets
    logger.info("Loading datasets...")
    logger.info(f"Looking for train data in: {train_dir}")
    logger.info(f"Looking for val data in: {val_dir}")
    logger.info(f"Looking for test data in: {test_dir}")

    # List files in directories for debugging
    try:
        if Path(train_dir).exists():
            train_files = list(Path(train_dir).iterdir())
            logger.info(f"Files in train dir: {train_files}")
        else:
            logger.error(f"Train directory does not exist: {train_dir}")

        if Path(val_dir).exists():
            val_files = list(Path(val_dir).iterdir())
            logger.info(f"Files in val dir: {val_files}")
        else:
            logger.error(f"Val directory does not exist: {val_dir}")

        if Path(test_dir).exists():
            test_files = list(Path(test_dir).iterdir())
            logger.info(f"Files in test dir: {test_files}")
        else:
            logger.error(f"Test directory does not exist: {test_dir}")
    except Exception as e:
        logger.warning(f"Could not list directory contents: {e}")

    train_file = Path(train_dir) / "train.jsonl"
    val_file = Path(val_dir) / "val.jsonl"
    test_file = Path(test_dir) / "test.jsonl"

    logger.info(f"Train file exists: {train_file.exists()}")
    logger.info(f"Val file exists: {val_file.exists()}")
    logger.info(f"Test file exists: {test_file.exists()}")

    train_records = load_jsonl(train_file)
    val_records = load_jsonl(val_file)
    test_records = load_jsonl(test_file)

    logger.info(f"Loaded {len(train_records)} train samples, {len(val_records)} val samples, {len(test_records)} test samples")

    # Load tokenizer and model
    logger.info("Loading tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model_id)

    # Add padding token if needed
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model with quantization if QLoRA
    model_kwargs = {}

    if use_4bit:
        from transformers import BitsAndBytesConfig

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )
        model_kwargs["quantization_config"] = bnb_config
        model_kwargs["device_map"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model_id,
        **model_kwargs
    )

    # Configure LoRA
    logger.info("Applying LoRA configuration...")
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        inference_mode=False,
        r=args.lora_rank,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=lora_target_modules,
    )

    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # Prepare datasets
    logger.info("Tokenizing datasets...")
    train_dataset = prepare_generation_dataset(train_records, tokenizer)
    val_dataset = prepare_generation_dataset(val_records, tokenizer)
    test_dataset = prepare_generation_dataset(test_records, tokenizer)

    # Data collator for language modeling
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False  # We're doing causal LM, not masked LM
    )

    # Training arguments
    # Note: Using eval_strategy for compatibility with older transformers versions
    training_args = TrainingArguments(
        output_dir=model_dir,
        learning_rate=args.learning_rate,
        num_train_epochs=args.num_epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        eval_strategy="epoch",  # Changed from evaluation_strategy for older transformers
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        logging_dir=f"{output_dir}/logs",
        logging_steps=10,
        save_total_limit=2,
        fp16=torch.cuda.is_available(),
        report_to=[],  # Disable wandb, tensorboard
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    # Train
    logger.info("Starting training...")
    train_result = trainer.train()

    # Save final model (adapter only)
    logger.info(f"Saving adapter to {model_dir}...")
    model.save_pretrained(model_dir)
    tokenizer.save_pretrained(model_dir)

    # Save training metrics
    metrics = train_result.metrics
    trainer.log_metrics("train", metrics)
    trainer.save_metrics("train", metrics)

    # Evaluate on validation set
    logger.info("Running final evaluation on validation set...")
    eval_metrics = trainer.evaluate()
    trainer.log_metrics("eval", eval_metrics)
    trainer.save_metrics("eval", eval_metrics)

    # Evaluate on test set
    logger.info("Running final evaluation on test set...")
    test_metrics = trainer.evaluate(eval_dataset=test_dataset)
    trainer.log_metrics("test", test_metrics)
    trainer.save_metrics("test", test_metrics)

    logger.info("Training complete!")
    logger.info(f"Final train loss: {metrics.get('train_loss', 'N/A')}")
    logger.info(f"Final eval loss: {eval_metrics.get('eval_loss', 'N/A')}")
    logger.info(f"Final test loss: {test_metrics.get('eval_loss', 'N/A')}")

    # Upload metrics to S3 for retrieval by API
    try:
        logger.info("Uploading metrics to S3...")

        # Get S3 output path from environment (set by orchestrator)
        output_s3_path = os.environ.get("SM_OUTPUT_DATA_DIR", "")

        # Combine all metrics
        all_metrics = {
            "train": {
                "train_loss": metrics.get("train_loss"),
                "train_runtime": metrics.get("train_runtime"),
                "train_samples_per_second": metrics.get("train_samples_per_second"),
            },
            "validation": {
                "eval_loss": eval_metrics.get("eval_loss"),
                "eval_runtime": eval_metrics.get("eval_runtime"),
                "eval_samples_per_second": eval_metrics.get("eval_samples_per_second"),
            },
            "test": {
                "eval_loss": test_metrics.get("eval_loss"),
                "eval_runtime": test_metrics.get("eval_runtime"),
                "eval_samples_per_second": test_metrics.get("eval_samples_per_second"),
            }
        }

        # Save locally first
        metrics_file = Path(output_dir) / "metrics.json"
        with open(metrics_file, "w") as f:
            json.dump(all_metrics, f, indent=2)

        logger.info(f"Metrics saved locally to {metrics_file}")
        logger.info(f"Metrics: {json.dumps(all_metrics, indent=2)}")

    except Exception as e:
        logger.error(f"Failed to save metrics: {e}", exc_info=True)
        # Don't fail the job if metrics upload fails


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Training failed with error: {e}", exc_info=True)
        sys.exit(1)
