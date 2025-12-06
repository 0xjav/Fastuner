"""Fine-tune job Pydantic schemas"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class FineTuneJobCreate(BaseModel):
    """Schema for creating a fine-tune job"""

    base_model_id: str = Field(..., min_length=1, max_length=255)
    dataset_id: str = Field(..., min_length=1, max_length=36)
    method: str = Field(..., pattern="^(lora|qlora)$")
    adapter_name: str = Field(..., min_length=1, max_length=255)

    # Hyperparameters
    learning_rate: float = Field(default=0.0002, gt=0, le=0.1)
    num_epochs: int = Field(default=3, ge=1, le=100)
    batch_size: int = Field(default=4, ge=1, le=128)
    lora_rank: int = Field(default=16, ge=1, le=256)
    lora_alpha: int = Field(default=32, ge=1, le=512)
    lora_dropout: float = Field(default=0.05, ge=0, le=0.5)

    # Additional hyperparameters
    hyperparameters: Optional[Dict[str, Any]] = None

    # Auto-deployment flag
    auto_deploy: bool = False


class FineTuneJobResponse(BaseModel):
    """Schema for fine-tune job API responses"""

    id: str
    tenant_id: str
    dataset_id: str
    base_model_id: str
    method: str
    adapter_name: str
    learning_rate: float
    num_epochs: int
    batch_size: int
    lora_rank: int
    lora_alpha: int
    lora_dropout: float
    hyperparameters: Optional[Dict[str, Any]] = None
    sagemaker_job_name: Optional[str] = None
    sagemaker_job_arn: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    final_train_loss: Optional[float] = None
    final_val_loss: Optional[float] = None
    metrics_s3_path: Optional[str] = None
    auto_deploy: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
