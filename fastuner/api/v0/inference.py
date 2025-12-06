"""Inference API endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from fastuner.database import get_db
from fastuner.schemas.inference import InferenceRequest, InferenceResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=InferenceResponse)
async def run_inference(
    request: InferenceRequest,
    tenant_id: str,  # TODO: Extract from JWT token
    db: Session = Depends(get_db),
):
    """
    Run inference using a deployed adapter.

    This endpoint:
    1. Finds the appropriate endpoint
    2. Updates last_used_at timestamp
    3. Sends request to SageMaker endpoint
    4. Returns predictions
    """
    # TODO: Implement inference
    raise HTTPException(status_code=501, detail="Not implemented yet")
