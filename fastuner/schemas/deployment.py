"""Deployment Pydantic schemas"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DeploymentCreate(BaseModel):
    """Schema for creating a deployment"""

    adapter_id: str = Field(..., min_length=1, max_length=36)
    instance_type: str = Field(default="ml.g5.2xlarge")
    instance_count: int = Field(default=1, ge=1, le=10)
    ttl_seconds: int = Field(default=3600, ge=300, le=86400)  # 5 min to 24 hours


class DeploymentResponse(BaseModel):
    """Schema for deployment API responses"""

    id: str
    tenant_id: str
    adapter_id: str
    endpoint_name: str
    endpoint_config_name: Optional[str] = None
    endpoint_arn: Optional[str] = None
    instance_type: str
    instance_count: int
    status: str
    ttl_seconds: int
    last_used_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
