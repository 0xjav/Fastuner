"""SageMaker utility functions for training and inference"""

import boto3
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

from fastuner.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SageMakerClient:
    """Wrapper for SageMaker operations"""

    def __init__(self):
        self.sagemaker = boto3.client("sagemaker", region_name=settings.aws_region)

    def create_training_job(
        self,
        job_name: str,
        role_arn: str,
        image_uri: str,
        input_data_config: list[Dict[str, Any]],
        output_path: str,
        hyperparameters: Dict[str, str],
        instance_type: str = "ml.g5.2xlarge",
        instance_count: int = 1,
        max_runtime_seconds: int = 86400,  # 24 hours
        volume_size_gb: int = 100,
        entry_point: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a SageMaker training job.

        Args:
            job_name: Unique name for the training job
            role_arn: IAM role ARN with SageMaker permissions
            image_uri: Docker image URI for training
            input_data_config: Input data configuration
            output_path: S3 path for model artifacts
            hyperparameters: Training hyperparameters
            instance_type: SageMaker instance type
            instance_count: Number of instances
            max_runtime_seconds: Maximum training time
            volume_size_gb: EBS volume size

        Returns:
            SageMaker training job response
        """
        try:
            # Convert hyperparameters to strings (SageMaker requirement)
            str_hyperparameters = {k: str(v) for k, v in hyperparameters.items()}

            # Add entry point if provided (for Hugging Face containers)
            # Note: source_dir parameter should be passed separately if needed
            if entry_point:
                str_hyperparameters["sagemaker_program"] = entry_point
                # sagemaker_submit_directory will be set in orchestrator if source_dir is provided

            response = self.sagemaker.create_training_job(
                TrainingJobName=job_name,
                RoleArn=role_arn,
                AlgorithmSpecification={
                    "TrainingImage": image_uri,
                    "TrainingInputMode": "File",
                },
                InputDataConfig=input_data_config,
                OutputDataConfig={
                    "S3OutputPath": output_path,
                },
                ResourceConfig={
                    "InstanceType": instance_type,
                    "InstanceCount": instance_count,
                    "VolumeSizeInGB": volume_size_gb,
                },
                StoppingCondition={
                    "MaxRuntimeInSeconds": max_runtime_seconds,
                },
                HyperParameters=str_hyperparameters,
            )

            logger.info(f"Created training job: {job_name}")
            return response

        except ClientError as e:
            logger.error(f"Failed to create training job: {e}")
            raise

    def describe_training_job(self, job_name: str) -> Dict[str, Any]:
        """Get training job details"""
        try:
            response = self.sagemaker.describe_training_job(TrainingJobName=job_name)
            return response
        except ClientError as e:
            logger.error(f"Failed to describe training job {job_name}: {e}")
            raise

    def stop_training_job(self, job_name: str) -> None:
        """Stop a running training job"""
        try:
            self.sagemaker.stop_training_job(TrainingJobName=job_name)
            logger.info(f"Stopped training job: {job_name}")
        except ClientError as e:
            logger.error(f"Failed to stop training job {job_name}: {e}")
            raise

    def create_model(
        self,
        model_name: str,
        role_arn: str,
        image_uri: str,
        model_data_url: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a SageMaker model.

        Args:
            model_name: Unique model name
            role_arn: IAM role ARN
            image_uri: Docker image for inference
            model_data_url: S3 URL to model artifacts
            environment: Environment variables for container

        Returns:
            SageMaker model response
        """
        try:
            container_def = {
                "Image": image_uri,
            }

            if model_data_url:
                container_def["ModelDataUrl"] = model_data_url

            if environment:
                container_def["Environment"] = environment

            response = self.sagemaker.create_model(
                ModelName=model_name,
                ExecutionRoleArn=role_arn,
                PrimaryContainer=container_def,
            )

            logger.info(f"Created model: {model_name}")
            return response

        except ClientError as e:
            logger.error(f"Failed to create model: {e}")
            raise

    def create_endpoint_config(
        self,
        config_name: str,
        model_name: str,
        instance_type: str = "ml.g5.2xlarge",
        instance_count: int = 1,
    ) -> Dict[str, Any]:
        """Create endpoint configuration"""
        try:
            response = self.sagemaker.create_endpoint_config(
                EndpointConfigName=config_name,
                ProductionVariants=[
                    {
                        "VariantName": "AllTraffic",
                        "ModelName": model_name,
                        "InstanceType": instance_type,
                        "InitialInstanceCount": instance_count,
                    }
                ],
            )

            logger.info(f"Created endpoint config: {config_name}")
            return response

        except ClientError as e:
            logger.error(f"Failed to create endpoint config: {e}")
            raise

    def create_endpoint(
        self,
        endpoint_name: str,
        config_name: str,
    ) -> Dict[str, Any]:
        """Create inference endpoint"""
        try:
            response = self.sagemaker.create_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=config_name,
            )

            logger.info(f"Created endpoint: {endpoint_name}")
            return response

        except ClientError as e:
            logger.error(f"Failed to create endpoint: {e}")
            raise

    def describe_endpoint(self, endpoint_name: str) -> Dict[str, Any]:
        """Get endpoint details"""
        try:
            response = self.sagemaker.describe_endpoint(EndpointName=endpoint_name)
            return response
        except ClientError as e:
            logger.error(f"Failed to describe endpoint {endpoint_name}: {e}")
            raise

    def delete_endpoint(self, endpoint_name: str) -> None:
        """Delete an endpoint"""
        try:
            self.sagemaker.delete_endpoint(EndpointName=endpoint_name)
            logger.info(f"Deleted endpoint: {endpoint_name}")
        except ClientError as e:
            logger.error(f"Failed to delete endpoint {endpoint_name}: {e}")
            raise

    def delete_endpoint_config(self, config_name: str) -> None:
        """Delete endpoint configuration"""
        try:
            self.sagemaker.delete_endpoint_config(EndpointConfigName=config_name)
            logger.info(f"Deleted endpoint config: {config_name}")
        except ClientError as e:
            logger.error(f"Failed to delete endpoint config {config_name}: {e}")
            raise

    def delete_model(self, model_name: str) -> None:
        """Delete a model"""
        try:
            self.sagemaker.delete_model(ModelName=model_name)
            logger.info(f"Deleted model: {model_name}")
        except ClientError as e:
            logger.error(f"Failed to delete model {model_name}: {e}")
            raise


class SageMakerRuntimeClient:
    """Wrapper for SageMaker Runtime (inference) operations"""

    def __init__(self):
        self.runtime = boto3.client("sagemaker-runtime", region_name=settings.aws_region)

    def invoke_endpoint(
        self,
        endpoint_name: str,
        payload: bytes,
        content_type: str = "application/json",
    ) -> bytes:
        """
        Invoke a SageMaker endpoint for inference.

        Args:
            endpoint_name: Name of the endpoint
            payload: Request payload
            content_type: Content type of payload

        Returns:
            Response body as bytes
        """
        try:
            response = self.runtime.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType=content_type,
                Body=payload,
            )

            return response["Body"].read()

        except ClientError as e:
            logger.error(f"Failed to invoke endpoint {endpoint_name}: {e}")
            raise


def get_sagemaker_client() -> SageMakerClient:
    """Get SageMaker client instance"""
    return SageMakerClient()


def get_sagemaker_runtime_client() -> SageMakerRuntimeClient:
    """Get SageMaker Runtime client instance"""
    return SageMakerRuntimeClient()
