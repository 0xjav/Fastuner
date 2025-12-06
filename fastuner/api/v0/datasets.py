"""Dataset API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import logging

from fastuner.database import get_db
from fastuner.schemas.dataset import DatasetResponse, DatasetCreate
from fastuner.models.dataset import Dataset

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=DatasetResponse, status_code=201)
async def create_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    task_type: str = Form(...),
    tenant_id: str = Form(...),  # TODO: Extract from JWT token
    db: Session = Depends(get_db),
):
    """
    Upload and validate a dataset.

    This endpoint:
    1. Validates the JSONL file format
    2. Performs schema validation
    3. Deduplicates samples
    4. Splits data into train/val/test
    5. Uploads to S3
    6. Returns dataset metadata
    """
    # TODO: Implement dataset upload, validation, and splitting
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/", response_model=List[DatasetResponse])
async def list_datasets(
    tenant_id: str,  # TODO: Extract from JWT token
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all datasets for a tenant"""
    datasets = (
        db.query(Dataset)
        .filter(Dataset.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return datasets


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    tenant_id: str,  # TODO: Extract from JWT token
    db: Session = Depends(get_db),
):
    """Get dataset metadata by ID"""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.tenant_id == tenant_id)
        .first()
    )

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return dataset


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: str,
    tenant_id: str,  # TODO: Extract from JWT token
    db: Session = Depends(get_db),
):
    """Delete a dataset"""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.tenant_id == tenant_id)
        .first()
    )

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    db.delete(dataset)
    db.commit()

    # TODO: Also delete S3 files
    return None
