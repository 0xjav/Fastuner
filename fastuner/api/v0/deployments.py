"""Deployment API endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from fastuner.database import get_db
from fastuner.schemas.deployment import DeploymentResponse, DeploymentCreate
from fastuner.models.deployment import Deployment

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=DeploymentResponse, status_code=201)
async def create_deployment(
    deployment_request: DeploymentCreate,
    tenant_id: str,  # TODO: Extract from JWT token
    db: Session = Depends(get_db),
):
    """
    Create a new deployment (inference endpoint).

    This endpoint:
    1. Creates or reuses a multi-tenant SageMaker endpoint
    2. Registers the adapter
    3. Returns deployment details
    """
    # TODO: Implement deployment creation
    raise HTTPException(status_code=501, detail="Not implemented yet")


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
    # TODO: Delete SageMaker endpoint
    raise HTTPException(status_code=501, detail="Not implemented yet")
