"""Configuration management for Fastuner"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "sqlite:///./fastuner.db"

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_account_id: str = ""

    # S3 Buckets
    s3_bucket_datasets: str = "fastuner-datasets-dev"
    s3_bucket_models: str = "fastuner-models-dev"
    s3_bucket_artifacts: str = "fastuner-artifacts-dev"

    # SageMaker
    sagemaker_execution_role_arn: str = ""
    sagemaker_vpc_id: str = ""
    sagemaker_subnet_ids: str = ""
    sagemaker_security_group_ids: str = ""

    # Cognito
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    cognito_region: str = "us-east-1"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    log_level: str = "INFO"

    # Deployment Configuration
    default_deployment_ttl: int = 3600  # 1 hour in seconds

    # Environment
    environment: str = "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"

    @property
    def sagemaker_subnet_list(self) -> list[str]:
        """Parse subnet IDs from comma-separated string"""
        return [s.strip() for s in self.sagemaker_subnet_ids.split(",") if s.strip()]

    @property
    def sagemaker_security_group_list(self) -> list[str]:
        """Parse security group IDs from comma-separated string"""
        return [s.strip() for s in self.sagemaker_security_group_ids.split(",") if s.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
