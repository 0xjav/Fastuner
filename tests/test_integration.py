"""Integration tests with mocked AWS services"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from fastuner.core.training import TrainingOrchestrator
from fastuner.core.inference import InferenceOrchestrator
from fastuner.models.fine_tune_job import FineTuneMethod


class TestTrainingOrchestrator:
    """Integration tests for training orchestration"""

    @patch("fastuner.core.training.orchestrator.get_sagemaker_client")
    def test_create_training_job(self, mock_sagemaker_client):
        """Test creating a SageMaker training job"""
        # Mock SageMaker client
        mock_client = Mock()
        mock_client.create_training_job.return_value = {
            "job_name": "test-job",
            "job_arn": "arn:aws:sagemaker:us-west-2:123456789012:training-job/test-job",
        }
        mock_sagemaker_client.return_value = mock_client

        orchestrator = TrainingOrchestrator()

        # Test job creation
        result = orchestrator.create_training_job(
            job_id="job_123",
            tenant_id="tenant_abc",
            base_model_id="meta-llama/Llama-2-7b-hf",
            dataset_s3_paths={
                "train": "s3://bucket/train.jsonl",
                "validation": "s3://bucket/val.jsonl",
            },
            adapter_name="test_adapter",
            method=FineTuneMethod.LORA,
            hyperparameters={
                "learning_rate": 0.0002,
                "num_epochs": 3,
                "batch_size": 4,
                "lora_rank": 16,
                "lora_alpha": 32,
            },
        )

        # Verify result
        assert result["job_name"] == "test-job"
        assert result["job_arn"].startswith("arn:aws:sagemaker")

        # Verify SageMaker client was called
        mock_client.create_training_job.assert_called_once()
        call_kwargs = mock_client.create_training_job.call_args[1]
        assert "job_name" in call_kwargs
        assert "image_uri" in call_kwargs
        assert "hyperparameters" in call_kwargs

    @patch("fastuner.core.training.orchestrator.get_sagemaker_client")
    def test_get_training_job_status(self, mock_sagemaker_client):
        """Test getting training job status"""
        # Mock SageMaker client
        mock_client = Mock()
        mock_client.describe_training_job.return_value = {
            "TrainingJobStatus": "Completed",
            "TrainingStartTime": datetime(2024, 1, 1, 12, 0, 0),
            "TrainingEndTime": datetime(2024, 1, 1, 14, 0, 0),
            "ModelArtifacts": {
                "S3ModelArtifacts": "s3://bucket/model.tar.gz"
            },
        }
        mock_sagemaker_client.return_value = mock_client

        orchestrator = TrainingOrchestrator()

        # Test status retrieval
        status = orchestrator.get_training_job_status("test-job")

        assert status["status"] == "Completed"
        assert status["model_s3_path"] == "s3://bucket/model.tar.gz"

        mock_client.describe_training_job.assert_called_once_with("test-job")

    @patch("fastuner.core.training.orchestrator.get_sagemaker_client")
    def test_cancel_training_job(self, mock_sagemaker_client):
        """Test canceling a training job"""
        # Mock SageMaker client
        mock_client = Mock()
        mock_client.stop_training_job.return_value = {}
        mock_sagemaker_client.return_value = mock_client

        orchestrator = TrainingOrchestrator()

        # Test job cancellation
        orchestrator.cancel_training_job("test-job")

        mock_client.stop_training_job.assert_called_once_with("test-job")


class TestInferenceOrchestrator:
    """Integration tests for inference orchestration"""

    @patch("fastuner.core.inference.orchestrator.get_sagemaker_client")
    def test_create_endpoint(self, mock_sagemaker_client):
        """Test creating a SageMaker endpoint"""
        # Mock SageMaker client
        mock_client = Mock()
        mock_client.describe_endpoint.side_effect = Exception("Endpoint doesn't exist")
        mock_client.create_model.return_value = {}
        mock_client.create_endpoint_config.return_value = {}
        mock_client.create_endpoint.return_value = {
            "EndpointArn": "arn:aws:sagemaker:us-west-2:123456789012:endpoint/test-endpoint",
        }
        mock_sagemaker_client.return_value = mock_client

        orchestrator = InferenceOrchestrator()

        # Test endpoint creation
        result = orchestrator.create_or_get_endpoint(
            tenant_id="tenant_abc",
            base_model_id="meta-llama/Llama-2-7b-hf",
            adapter_s3_path="s3://bucket/adapter",
            endpoint_name="test-endpoint",
            instance_type="ml.g5.xlarge",
            instance_count=1,
        )

        # Verify result
        assert result["endpoint_name"] == "test-endpoint"
        assert result["status"] == "Creating"

        # Verify SageMaker calls
        mock_client.create_model.assert_called_once()
        mock_client.create_endpoint_config.assert_called_once()
        mock_client.create_endpoint.assert_called_once()

    @patch("fastuner.core.inference.orchestrator.get_sagemaker_client")
    def test_get_existing_endpoint(self, mock_sagemaker_client):
        """Test getting an existing endpoint"""
        # Mock SageMaker client
        mock_client = Mock()
        mock_client.describe_endpoint.return_value = {
            "EndpointArn": "arn:aws:sagemaker:us-west-2:123456789012:endpoint/existing",
            "EndpointStatus": "InService",
        }
        mock_sagemaker_client.return_value = mock_client

        orchestrator = InferenceOrchestrator()

        # Test getting existing endpoint
        result = orchestrator.create_or_get_endpoint(
            tenant_id="tenant_abc",
            base_model_id="meta-llama/Llama-2-7b-hf",
            adapter_s3_path="s3://bucket/adapter",
            endpoint_name="existing",
            instance_type="ml.g5.xlarge",
            instance_count=1,
        )

        # Should return existing endpoint without creating new one
        assert result["endpoint_name"] == "existing"
        assert result["status"] == "InService"

        # Should NOT create new resources
        mock_client.create_model.assert_not_called()
        mock_client.create_endpoint.assert_not_called()

    @patch("fastuner.core.inference.orchestrator.get_sagemaker_runtime_client")
    def test_invoke_endpoint(self, mock_runtime_client):
        """Test invoking an endpoint for inference"""
        # Mock SageMaker Runtime client
        mock_client = Mock()
        mock_client.invoke_endpoint.return_value = b'{"outputs": ["Generated text"]}'
        mock_runtime_client.return_value = mock_client

        orchestrator = InferenceOrchestrator()

        # Test inference invocation
        result = orchestrator.invoke_endpoint(
            endpoint_name="test-endpoint",
            inputs=["Hello world"],
            parameters={"max_new_tokens": 50},
        )

        # Verify result
        assert "outputs" in result
        assert "latency_ms" in result
        assert result["latency_ms"] > 0

        # Verify runtime client was called
        mock_client.invoke_endpoint.assert_called_once()

    @patch("fastuner.core.inference.orchestrator.get_sagemaker_client")
    def test_delete_endpoint(self, mock_sagemaker_client):
        """Test deleting an endpoint with config and model"""
        # Mock SageMaker client
        mock_client = Mock()
        mock_client.describe_endpoint.return_value = {
            "EndpointConfigName": "test-config"
        }
        mock_client.sagemaker.describe_endpoint_config.return_value = {
            "ProductionVariants": [{"ModelName": "test-model"}]
        }
        mock_client.delete_endpoint.return_value = {}
        mock_client.delete_endpoint_config.return_value = {}
        mock_client.delete_model.return_value = {}
        mock_sagemaker_client.return_value = mock_client

        orchestrator = InferenceOrchestrator()

        # Test endpoint deletion
        orchestrator.delete_endpoint(
            endpoint_name="test-endpoint",
            delete_config=True,
            delete_model=True,
        )

        # Verify all resources were deleted
        mock_client.delete_endpoint.assert_called_once_with("test-endpoint")
        mock_client.delete_endpoint_config.assert_called_once_with("test-config")
        mock_client.delete_model.assert_called_once_with("test-model")


class TestEphemeralityManager:
    """Integration tests for ephemerality management"""

    @patch("fastuner.core.ephemerality.manager.SessionLocal")
    @patch("fastuner.core.ephemerality.manager.InferenceOrchestrator")
    def test_find_stale_deployments(self, mock_orchestrator, mock_session):
        """Test finding stale deployments based on TTL"""
        from fastuner.core.ephemerality import EphemeralityManager
        from fastuner.models.deployment import Deployment, DeploymentStatus
        from datetime import timedelta

        # Mock database session
        mock_db = Mock()
        mock_session.return_value = mock_db

        # Create mock deployments
        now = datetime.utcnow()
        stale_deployment = Mock(spec=Deployment)
        stale_deployment.id = "dep_stale"
        stale_deployment.status = DeploymentStatus.ACTIVE
        stale_deployment.last_used_at = now - timedelta(hours=2)  # 2 hours ago
        stale_deployment.ttl_seconds = 3600  # 1 hour TTL

        active_deployment = Mock(spec=Deployment)
        active_deployment.id = "dep_active"
        active_deployment.status = DeploymentStatus.ACTIVE
        active_deployment.last_used_at = now - timedelta(minutes=30)  # 30 mins ago
        active_deployment.ttl_seconds = 3600  # 1 hour TTL

        mock_db.query.return_value.filter.return_value.all.return_value = [
            stale_deployment,
            active_deployment,
        ]

        manager = EphemeralityManager()

        # Test finding stale deployments
        stale = manager.find_stale_deployments(mock_db)

        # Only the stale deployment should be found
        assert len(stale) == 1
        assert stale[0].id == "dep_stale"

    @patch("fastuner.core.ephemerality.manager.SessionLocal")
    def test_cost_report(self, mock_session):
        """Test generating cost report for active deployments"""
        from fastuner.core.ephemerality import EphemeralityManager
        from fastuner.models.deployment import Deployment, DeploymentStatus

        # Mock database session
        mock_db = Mock()
        mock_session.return_value = mock_db

        # Create mock deployments
        deployment1 = Mock(spec=Deployment)
        deployment1.id = "dep_1"
        deployment1.endpoint_name = "endpoint-1"
        deployment1.instance_type = "ml.g5.xlarge"
        deployment1.instance_count = 1
        deployment1.last_used_at = datetime.utcnow()
        deployment1.ttl_seconds = 3600

        deployment2 = Mock(spec=Deployment)
        deployment2.id = "dep_2"
        deployment2.endpoint_name = "endpoint-2"
        deployment2.instance_type = "ml.g5.2xlarge"
        deployment2.instance_count = 2
        deployment2.last_used_at = datetime.utcnow()
        deployment2.ttl_seconds = 3600

        mock_db.query.return_value.filter.return_value.all.return_value = [
            deployment1,
            deployment2,
        ]

        manager = EphemeralityManager()

        # Test cost report generation
        report = manager.get_cost_report(mock_db)

        assert report["active_count"] == 2
        assert report["total_hourly_cost"] > 0
        assert report["estimated_monthly_cost"] > 0
        assert len(report["deployments"]) == 2


# Pytest configuration
@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset mocks between tests"""
    yield
    # Cleanup happens automatically with pytest
