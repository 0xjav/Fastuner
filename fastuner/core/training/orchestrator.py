"""
Training job orchestration for LoRA/QLoRA fine-tuning.

This module handles:
- SageMaker training job creation
- Hyperparameter validation
- Model artifact management
- Job monitoring
"""

import logging
from typing import Dict, Any
from datetime import datetime

from fastuner.config import get_settings
from fastuner.utils.sagemaker import get_sagemaker_client
from fastuner.utils.s3 import get_s3_client
from fastuner.models.fine_tune_job import FineTuneMethod

logger = logging.getLogger(__name__)
settings = get_settings()


class TrainingOrchestrator:
    """Orchestrates SageMaker training jobs for fine-tuning"""

    # Default training image (will be replaced with actual image)
    DEFAULT_TRAINING_IMAGE = "763104351884.dkr.ecr.{region}.amazonaws.com/huggingface-pytorch-training:2.0.0-transformers4.28.1-gpu-py310-cu118-ubuntu20.04"

    def __init__(self):
        self.sagemaker = get_sagemaker_client()
        self.s3 = get_s3_client()

    def create_training_job(
        self,
        job_id: str,
        tenant_id: str,
        base_model_id: str,
        dataset_s3_paths: Dict[str, str],  # {train, val, test}
        adapter_name: str,
        method: FineTuneMethod,
        hyperparameters: Dict[str, Any],
        instance_type: str = "ml.g5.2xlarge",
    ) -> Dict[str, Any]:
        """
        Create a SageMaker training job for LoRA/QLoRA fine-tuning.

        Args:
            job_id: Unique job ID
            tenant_id: Tenant ID
            base_model_id: Hugging Face model ID
            dataset_s3_paths: S3 paths for train/val/test splits
            adapter_name: Name for the fine-tuned adapter
            method: Fine-tuning method (LoRA/QLoRA)
            hyperparameters: Training hyperparameters
            instance_type: SageMaker instance type

        Returns:
            SageMaker job response with job name and ARN
        """
        # Generate unique job name (SageMaker requires)
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        job_name = f"fastuner-{tenant_id}-{job_id[:8]}-{timestamp}"

        # Prepare hyperparameters for SageMaker
        training_hyperparameters = {
            # Model configuration
            "base_model_id": base_model_id,
            "adapter_name": adapter_name,
            "method": method.value,

            # Training parameters
            "learning_rate": hyperparameters.get("learning_rate", 0.0002),
            "num_epochs": hyperparameters.get("num_epochs", 3),
            "batch_size": hyperparameters.get("batch_size", 4),
            "gradient_accumulation_steps": hyperparameters.get("gradient_accumulation_steps", 4),

            # LoRA configuration
            "lora_rank": hyperparameters.get("lora_rank", 16),
            "lora_alpha": hyperparameters.get("lora_alpha", 32),
            "lora_dropout": hyperparameters.get("lora_dropout", 0.05),
            "lora_target_modules": hyperparameters.get("lora_target_modules", "q_proj,v_proj"),

            # QLoRA-specific (if method is qlora)
            "use_4bit": "true" if method == FineTuneMethod.QLORA else "false",
            "bnb_4bit_compute_dtype": "float16",
            "bnb_4bit_quant_type": "nf4",

            # Output configuration
            "output_dir": "/opt/ml/model",
        }

        # Input data configuration
        input_data_config = [
            {
                "ChannelName": "train",
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": dataset_s3_paths["train"],
                        "S3DataDistributionType": "FullyReplicated",
                    }
                },
            },
            {
                "ChannelName": "validation",
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": dataset_s3_paths["val"],
                        "S3DataDistributionType": "FullyReplicated",
                    }
                },
            },
        ]

        # Output path for model artifacts
        output_path = f"s3://{settings.s3_bucket_models}/{tenant_id}/adapters/{job_id}"

        # Training image URI
        image_uri = self.DEFAULT_TRAINING_IMAGE.format(region=settings.aws_region)

        try:
            # Create the training job
            response = self.sagemaker.create_training_job(
                job_name=job_name,
                role_arn=settings.sagemaker_execution_role_arn,
                image_uri=image_uri,
                input_data_config=input_data_config,
                output_path=output_path,
                hyperparameters=training_hyperparameters,
                instance_type=instance_type,
                instance_count=1,
                max_runtime_seconds=86400,  # 24 hours max
                volume_size_gb=100,
            )

            logger.info(f"Created SageMaker training job: {job_name}")

            return {
                "job_name": job_name,
                "job_arn": response["TrainingJobArn"],
                "output_path": output_path,
            }

        except Exception as e:
            logger.error(f"Failed to create training job: {e}")
            raise

    def get_training_job_status(self, job_name: str) -> Dict[str, Any]:
        """
        Get the status of a training job.

        Args:
            job_name: SageMaker job name

        Returns:
            Job status information
        """
        try:
            job_details = self.sagemaker.describe_training_job(job_name)

            return {
                "status": job_details["TrainingJobStatus"],
                "secondary_status": job_details.get("SecondaryStatus"),
                "failure_reason": job_details.get("FailureReason"),
                "model_artifacts": job_details.get("ModelArtifacts", {}).get("S3ModelArtifacts"),
                "training_time_seconds": job_details.get("TrainingTimeInSeconds"),
                "billable_time_seconds": job_details.get("BillableTimeInSeconds"),
                "final_metric_data": job_details.get("FinalMetricDataList", []),
            }

        except Exception as e:
            logger.error(f"Failed to get training job status: {e}")
            raise

    def stop_training_job(self, job_name: str) -> None:
        """
        Stop a running training job.

        Args:
            job_name: SageMaker job name
        """
        try:
            self.sagemaker.stop_training_job(job_name)
            logger.info(f"Stopped training job: {job_name}")
        except Exception as e:
            logger.error(f"Failed to stop training job: {e}")
            raise

    def extract_adapter_artifacts(
        self,
        job_name: str,
        model_artifacts_s3_path: str,
        adapter_id: str,
        tenant_id: str,
    ) -> str:
        """
        Extract adapter artifacts from training output.

        Args:
            job_name: SageMaker job name
            model_artifacts_s3_path: S3 path to model.tar.gz
            adapter_id: Adapter ID
            tenant_id: Tenant ID

        Returns:
            S3 path to extracted adapter
        """
        # In V0, we'll assume the training script outputs adapters directly
        # In production, we'd download model.tar.gz, extract, and re-upload
        adapter_s3_path = f"s3://{settings.s3_bucket_models}/{tenant_id}/adapters/{adapter_id}/"

        logger.info(f"Adapter artifacts available at: {adapter_s3_path}")
        return adapter_s3_path


def get_training_orchestrator() -> TrainingOrchestrator:
    """Get TrainingOrchestrator instance"""
    return TrainingOrchestrator()
