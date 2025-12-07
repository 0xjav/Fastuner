"""
Inference orchestration for multi-tenant adapter serving.

This module handles:
- SageMaker endpoint creation/management
- Multi-tenant adapter loading
- Inference requests
- Endpoint lifecycle
"""

import logging
import json
from typing import Dict, Any, List
from datetime import datetime

from fastuner.config import get_settings
from fastuner.utils.sagemaker import get_sagemaker_client, get_sagemaker_runtime_client

logger = logging.getLogger(__name__)
settings = get_settings()


class InferenceOrchestrator:
    """Orchestrates SageMaker inference endpoints for multi-tenant adapter serving"""

    # Default LMI inference image
    DEFAULT_LMI_IMAGE = "763104351884.dkr.ecr.{region}.amazonaws.com/djl-inference:0.25.0-deepspeed0.11.0-cu118"

    def __init__(self):
        self.sagemaker = get_sagemaker_client()
        self.runtime = get_sagemaker_runtime_client()

    def create_or_get_endpoint(
        self,
        tenant_id: str,
        base_model_id: str,
        adapter_s3_path: str,
        endpoint_name: str,
        instance_type: str = "ml.g5.2xlarge",
        instance_count: int = 1,
    ) -> Dict[str, Any]:
        """
        Create a new SageMaker endpoint or return existing one.

        For V0, we create a new endpoint per adapter (simpler).
        V1+ will implement true multi-tenant adapter serving.

        Args:
            tenant_id: Tenant ID
            base_model_id: Base model (e.g., "meta-llama/Llama-2-7b-chat-hf")
            adapter_s3_path: S3 path to adapter artifacts
            endpoint_name: Unique endpoint name
            instance_type: SageMaker instance type
            instance_count: Number of instances

        Returns:
            Endpoint details
        """
        try:
            # Check if endpoint already exists
            try:
                existing = self.sagemaker.describe_endpoint(endpoint_name)
                logger.info(f"Endpoint {endpoint_name} already exists")
                return {
                    "endpoint_name": endpoint_name,
                    "endpoint_arn": existing["EndpointArn"],
                    "status": existing["EndpointStatus"],
                }
            except:
                # Endpoint doesn't exist, create it
                pass

            # Generate unique model and config names (max 63 chars for SageMaker)
            timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            # Ensure names fit within 63 char limit: endpoint_name (max 35) + suffix (max 28)
            max_endpoint_len = 35
            safe_endpoint_name = endpoint_name[:max_endpoint_len] if len(endpoint_name) > max_endpoint_len else endpoint_name
            model_name = f"{safe_endpoint_name}-m-{timestamp}"
            config_name = f"{safe_endpoint_name}-c-{timestamp}"

            # LMI environment variables for adapter loading
            environment = {
                "HF_MODEL_ID": base_model_id,
                "OPTION_ADAPTER_S3_PATH": adapter_s3_path,
                "OPTION_ENABLE_LORA": "true",
                "OPTION_MAX_INPUT_LEN": "2048",
                "OPTION_MAX_OUTPUT_LEN": "512",
            }

            # Image URI
            image_uri = self.DEFAULT_LMI_IMAGE.format(region=settings.aws_region)

            # Create model
            self.sagemaker.create_model(
                model_name=model_name,
                role_arn=settings.sagemaker_execution_role_arn,
                image_uri=image_uri,
                environment=environment,
            )

            # Create endpoint config
            self.sagemaker.create_endpoint_config(
                config_name=config_name,
                model_name=model_name,
                instance_type=instance_type,
                instance_count=instance_count,
            )

            # Create endpoint
            response = self.sagemaker.create_endpoint(
                endpoint_name=endpoint_name,
                config_name=config_name,
            )

            logger.info(f"Created endpoint: {endpoint_name}")

            return {
                "endpoint_name": endpoint_name,
                "endpoint_arn": response["EndpointArn"],
                "model_name": model_name,
                "config_name": config_name,
                "status": "Creating",
            }

        except Exception as e:
            logger.error(f"Failed to create endpoint: {e}")
            raise

    def get_endpoint_status(self, endpoint_name: str) -> Dict[str, Any]:
        """
        Get endpoint status.

        Args:
            endpoint_name: Endpoint name

        Returns:
            Endpoint status details
        """
        try:
            endpoint = self.sagemaker.describe_endpoint(endpoint_name)
            return {
                "status": endpoint["EndpointStatus"],
                "creation_time": endpoint.get("CreationTime"),
                "last_modified_time": endpoint.get("LastModifiedTime"),
                "failure_reason": endpoint.get("FailureReason"),
            }
        except Exception as e:
            logger.error(f"Failed to get endpoint status: {e}")
            raise

    def invoke_endpoint(
        self,
        endpoint_name: str,
        inputs: List[str],
        parameters: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Invoke endpoint for inference.

        Args:
            endpoint_name: Endpoint name
            inputs: List of input texts
            parameters: Generation parameters

        Returns:
            Inference results
        """
        try:
            # Prepare request payload
            payload = {
                "inputs": inputs,
                "parameters": parameters or {},
            }

            # Invoke endpoint
            start_time = datetime.utcnow()
            response_body = self.runtime.invoke_endpoint(
                endpoint_name=endpoint_name,
                payload=json.dumps(payload).encode("utf-8"),
                content_type="application/json",
            )
            end_time = datetime.utcnow()

            # Parse response
            result = json.loads(response_body.decode("utf-8"))

            latency_ms = (end_time - start_time).total_seconds() * 1000

            return {
                "outputs": result.get("outputs", result.get("predictions", [])),
                "latency_ms": latency_ms,
            }

        except Exception as e:
            logger.error(f"Failed to invoke endpoint {endpoint_name}: {e}")
            raise

    def delete_endpoint(
        self,
        endpoint_name: str,
        delete_config: bool = True,
        delete_model: bool = True,
    ) -> None:
        """
        Delete endpoint and optionally its config and model.

        Args:
            endpoint_name: Endpoint name
            delete_config: Whether to delete endpoint config
            delete_model: Whether to delete model
        """
        try:
            # Get endpoint details before deletion
            endpoint = self.sagemaker.describe_endpoint(endpoint_name)
            config_name = endpoint.get("EndpointConfigName")

            # Get model name from config if needed
            model_name = None
            if delete_model and config_name:
                config = self.sagemaker.sagemaker.describe_endpoint_config(
                    EndpointConfigName=config_name
                )
                model_name = config["ProductionVariants"][0]["ModelName"]

            # Delete endpoint
            self.sagemaker.delete_endpoint(endpoint_name)
            logger.info(f"Deleted endpoint: {endpoint_name}")

            # Delete config
            if delete_config and config_name:
                self.sagemaker.delete_endpoint_config(config_name)
                logger.info(f"Deleted endpoint config: {config_name}")

            # Delete model
            if delete_model and model_name:
                self.sagemaker.delete_model(model_name)
                logger.info(f"Deleted model: {model_name}")

        except Exception as e:
            logger.error(f"Failed to delete endpoint {endpoint_name}: {e}")
            raise


def get_inference_orchestrator() -> InferenceOrchestrator:
    """Get InferenceOrchestrator instance"""
    return InferenceOrchestrator()
