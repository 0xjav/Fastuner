"""Deployment API endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
from datetime import datetime

from fastuner.database import get_db
from fastuner.schemas.deployment import DeploymentResponse, DeploymentCreate
from fastuner.models.deployment import Deployment, DeploymentStatus
from fastuner.models.adapter import Adapter
from fastuner.core.inference import InferenceOrchestrator
from fastuner.utils.id_generator import generate_deployment_id

router = APIRouter()
logger = logging.getLogger(__name__)
inference_orchestrator = InferenceOrchestrator()


@router.post("/", response_model=DeploymentResponse, status_code=201)
async def create_deployment(
    deployment_request: DeploymentCreate,
    tenant_id: str,  # TODO: Extract from JWT token
    db: Session = Depends(get_db),
):
    """
    Create a new deployment (inference endpoint).

    This endpoint:
    1. Validates adapter exists
    2. Creates SageMaker endpoint with adapter
    3. Stores deployment metadata
    4. Returns deployment details
    """
    try:
        # Step 1: Validate adapter exists
        adapter = (
            db.query(Adapter)
            .filter(Adapter.id == deployment_request.adapter_id, Adapter.tenant_id == tenant_id)
            .first()
        )

        if not adapter:
            raise HTTPException(status_code=404, detail="Adapter not found")

        # Step 2: Create deployment record
        deployment_id = generate_deployment_id()
        endpoint_name = f"fastuner-{tenant_id[:8]}-{adapter.name[:20]}-{deployment_id[:8]}"

        deployment = Deployment(
            id=deployment_id,
            tenant_id=tenant_id,
            adapter_id=deployment_request.adapter_id,
            endpoint_name=endpoint_name,
            instance_type=deployment_request.instance_type,
            instance_count=deployment_request.instance_count,
            status=DeploymentStatus.CREATING,
            ttl_seconds=deployment_request.ttl_seconds,
            last_used_at=datetime.utcnow(),
        )

        db.add(deployment)
        db.commit()

        # Step 3: Create SageMaker endpoint
        try:
            endpoint_result = inference_orchestrator.create_or_get_endpoint(
                tenant_id=tenant_id,
                base_model_id=adapter.base_model_id,
                adapter_s3_path=adapter.s3_path,
                endpoint_name=endpoint_name,
                instance_type=deployment_request.instance_type,
                instance_count=deployment_request.instance_count,
            )

            # Update deployment with endpoint details
            deployment.endpoint_arn = endpoint_result.get("endpoint_arn")
            deployment.endpoint_config_name = endpoint_result.get("config_name")

            db.commit()
            db.refresh(deployment)

            logger.info(f"Created deployment {deployment_id} with endpoint {endpoint_name}")

        except Exception as e:
            # Update deployment status to failed
            deployment.status = DeploymentStatus.FAILED
            db.commit()
            raise HTTPException(status_code=500, detail=f"Failed to create endpoint: {str(e)}")

        return deployment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating deployment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[DeploymentResponse])
async def list_deployments(
    tenant_id: str,  # TODO: Extract from JWT token
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all deployments for a tenant"""
    deployments = (
        db.query(Deployment)
        .filter(Deployment.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return deployments


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: str,
    tenant_id: str,  # TODO: Extract from JWT token
    db: Session = Depends(get_db),
):
    """Get deployment details by ID"""
    deployment = (
        db.query(Deployment)
        .filter(Deployment.id == deployment_id, Deployment.tenant_id == tenant_id)
        .first()
    )

    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    return deployment


@router.delete("/{deployment_id}", status_code=204)
async def delete_deployment(
    deployment_id: str,
    tenant_id: str,  # TODO: Extract from JWT token
    db: Session = Depends(get_db),
):
    """Delete a deployment and tear down the endpoint"""
    deployment = (
        db.query(Deployment)
        .filter(Deployment.id == deployment_id, Deployment.tenant_id == tenant_id)
        .first()
    )

    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    # Delete SageMaker endpoint
    try:
        inference_orchestrator.delete_endpoint(
            endpoint_name=deployment.endpoint_name,
            delete_config=True,
            delete_model=True,
        )
        logger.info(f"Deleted SageMaker endpoint {deployment.endpoint_name}")
    except Exception as e:
        logger.error(f"Failed to delete endpoint: {e}")
        # Continue even if deletion fails

    # Update deployment status
    deployment.status = DeploymentStatus.DELETED
    db.commit()

    return None
