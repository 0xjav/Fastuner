"""Inference Pydantic schemas"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class InferenceRequest(BaseModel):
    """Schema for inference request"""

    model_id: str = Field(..., min_length=1, max_length=255)
    adapter_name: str = Field(..., min_length=1, max_length=255)
    inputs: List[str] = Field(..., min_items=1, max_items=100)
    parameters: Optional[Dict[str, Any]] = None


class InferenceResponse(BaseModel):
    """Schema for inference response"""

    outputs: List[str]
    adapter_name: str
    latency_ms: float
    model_id: str
