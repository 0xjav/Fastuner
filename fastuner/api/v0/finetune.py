"""Fine-tune job API endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from fastuner.database import get_db
from fastuner.schemas.finetune import FineTuneJobResponse, FineTuneJobCreate
from fastuner.models.fine_tune_job import FineTuneJob

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=FineTuneJobResponse, status_code=201)
async def create_fine_tune_job(
    job_request: FineTuneJobCreate,
    tenant_id: str,  # TODO: Extract from JWT token
    db: Session = Depends(get_db),
):
    """
    Create a new fine-tuning job.

    This endpoint:
    1. Validates the request parameters
    2. Creates a SageMaker training job
    3. Stores job metadata in the database
    4. Returns job details
    """
    # TODO: Implement fine-tune job creation
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/", response_model=List[FineTuneJobResponse])
async def list_fine_tune_jobs(
    tenant_id: str,  # TODO: Extract from JWT token
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all fine-tune jobs for a tenant"""
    jobs = (
        db.query(FineTuneJob)
        .filter(FineTuneJob.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return jobs


@router.get("/{job_id}", response_model=FineTuneJobResponse)
async def get_fine_tune_job(
    job_id: str,
    tenant_id: str,  # TODO: Extract from JWT token
    db: Session = Depends(get_db),
):
    """Get fine-tune job details by ID"""
    job = (
        db.query(FineTuneJob)
        .filter(FineTuneJob.id == job_id, FineTuneJob.tenant_id == tenant_id)
        .first()
    )

    if not job:
        raise HTTPException(status_code=404, detail="Fine-tune job not found")

    return job


@router.delete("/{job_id}", status_code=204)
async def cancel_fine_tune_job(
    job_id: str,
    tenant_id: str,  # TODO: Extract from JWT token
    db: Session = Depends(get_db),
):
    """Cancel a running fine-tune job"""
    # TODO: Stop SageMaker training job
    raise HTTPException(status_code=501, detail="Not implemented yet")
