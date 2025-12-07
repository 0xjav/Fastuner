"""Dataset API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import logging
import random

from fastuner.database import get_db
from fastuner.schemas.dataset import DatasetResponse, DatasetCreate
from fastuner.models.dataset import Dataset, TaskType
from fastuner.core.dataset import DatasetValidator, ValidationError, DatasetSplitter
from fastuner.utils.s3 import get_s3_client
from fastuner.utils.id_generator import generate_dataset_id
from fastuner.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


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
    try:
        # Read file content
        content = await file.read()
        file_content = content.decode("utf-8")

        # Step 1 & 2: Validate and parse JSONL
        logger.info(f"Validating dataset '{name}' for tenant {tenant_id}")
        try:
            records = DatasetValidator.validate_jsonl(file_content)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")

        # Step 3 & 4: Split dataset
        split_seed = random.randint(1, 1000000)
        try:
            splits = DatasetSplitter.split(
                records=records,
                task_type=task_type,
                seed=split_seed,
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Splitting error: {str(e)}")

        # Step 5: Upload to S3
        dataset_id = generate_dataset_id()
        s3_client = get_s3_client()

        raw_key = f"{tenant_id}/datasets/{dataset_id}/raw.jsonl"
        train_key = f"{tenant_id}/datasets/{dataset_id}/train.jsonl"
        val_key = f"{tenant_id}/datasets/{dataset_id}/val.jsonl"
        test_key = f"{tenant_id}/datasets/{dataset_id}/test.jsonl"

        try:
            raw_s3_path = s3_client.upload_jsonl(
                settings.s3_datasets_bucket, raw_key, records
            )
            train_s3_path = s3_client.upload_jsonl(
                settings.s3_datasets_bucket, train_key, splits["train"]
            )
            val_s3_path = s3_client.upload_jsonl(
                settings.s3_datasets_bucket, val_key, splits["val"]
            )
            test_s3_path = s3_client.upload_jsonl(
                settings.s3_datasets_bucket, test_key, splits["test"]
            )
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload to S3: {str(e)}")

        # Step 6: Save metadata to database
        dataset = Dataset(
            id=dataset_id,
            tenant_id=tenant_id,
            name=name,
            task_type=TaskType(task_type),
            schema_version=DatasetValidator.SCHEMA_VERSION,
            raw_s3_path=raw_s3_path,
            train_s3_path=train_s3_path,
            val_s3_path=val_s3_path,
            test_s3_path=test_s3_path,
            total_samples=len(records),
            train_samples=len(splits["train"]),
            val_samples=len(splits["val"]),
            test_samples=len(splits["test"]),
            split_seed=split_seed,
            split_ratios=DatasetSplitter.DEFAULT_RATIOS,
        )

        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        logger.info(f"Dataset {dataset_id} created successfully")
        return dataset

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


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

    # Delete from database
    db.delete(dataset)
    db.commit()

    # Delete S3 files
    try:
        s3_client = get_s3_client()
        prefix = f"{tenant_id}/datasets/{dataset_id}/"
        s3_client.delete_prefix(settings.s3_datasets_bucket, prefix)
        logger.info(f"Deleted S3 files for dataset {dataset_id}")
    except Exception as e:
        logger.error(f"Failed to delete S3 files: {e}")
        # Continue even if S3 deletion fails

    return None
