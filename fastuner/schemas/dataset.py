"""Dataset Pydantic schemas"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class DatasetCreate(BaseModel):
    """Schema for creating a dataset"""

    name: str = Field(..., min_length=1, max_length=255)
    task_type: str = Field(..., pattern="^(text_generation|classification|qa)$")


class DatasetResponse(BaseModel):
    """Schema for dataset API responses"""

    id: str
    tenant_id: str
    name: str
    task_type: str
    schema_version: str
    raw_s3_path: str
    train_s3_path: str
    val_s3_path: str
    test_s3_path: str
    total_samples: int
    train_samples: int
    val_samples: int
    test_samples: int
    split_seed: int
    split_ratios: Dict[str, float]
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
