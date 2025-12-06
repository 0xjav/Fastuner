"""Inference API endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from fastuner.database import get_db
from fastuner.schemas.inference import InferenceRequest, InferenceResponse
from fastuner.models.deployment import Deployment, DeploymentStatus
from fastuner.models.adapter import Adapter
from fastuner.core.inference import InferenceOrchestrator

router = APIRouter()
logger = logging.getLogger(__name__)
inference_orchestrator = InferenceOrchestrator()


@router.post("/", response_model=InferenceResponse)
async def run_inference(
    request: InferenceRequest,
    tenant_id: str,  # TODO: Extract from JWT token
    db: Session = Depends(get_db),
):
    """
    Run inference using a deployed adapter.

    This endpoint:
    1. Finds the appropriate endpoint for the adapter
    2. Updates last_used_at timestamp
    3. Sends request to SageMaker endpoint
    4. Returns predictions
    """
    try:
        # Step 1: Find adapter by name and model
        adapter = (
            db.query(Adapter)
            .filter(
                Adapter.tenant_id == tenant_id,
                Adapter.name == request.adapter_name,
                Adapter.base_model_id == request.model_id,
            )
            .first()
        )

        if not adapter:
            raise HTTPException(
                status_code=404,
                detail=f"Adapter '{request.adapter_name}' not found for model '{request.model_id}'"
            )

        # Step 2: Find active deployment for this adapter
        deployment = (
            db.query(Deployment)
            .filter(
                Deployment.tenant_id == tenant_id,
                Deployment.adapter_id == adapter.id,
                Deployment.status == DeploymentStatus.ACTIVE,
            )
            .first()
        )

        if not deployment:
            raise HTTPException(
                status_code=404,
                detail=f"No active deployment found for adapter '{request.adapter_name}'. Please create a deployment first."
            )

        # Step 3: Update last_used_at timestamp
        deployment.last_used_at = datetime.utcnow()
        db.commit()

        # Step 4: Invoke SageMaker endpoint
        try:
            result = inference_orchestrator.invoke_endpoint(
                endpoint_name=deployment.endpoint_name,
                inputs=request.inputs,
                parameters=request.parameters,
            )

            return InferenceResponse(
                outputs=result["outputs"],
                adapter_name=request.adapter_name,
                latency_ms=result["latency_ms"],
                model_id=request.model_id,
            )

        except Exception as e:
            logger.error(f"Inference failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during inference: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
