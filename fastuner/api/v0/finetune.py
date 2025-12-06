"""Fine-tune job API endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from fastuner.database import get_db
from fastuner.schemas.finetune import FineTuneJobResponse, FineTuneJobCreate
from fastuner.models.fine_tune_job import FineTuneJob, FineTuneMethod, JobStatus
from fastuner.models.dataset import Dataset
from fastuner.models.adapter import Adapter
from fastuner.core.training import TrainingOrchestrator
from fastuner.utils.id_generator import generate_job_id, generate_adapter_id

router = APIRouter()
logger = logging.getLogger(__name__)
training_orchestrator = TrainingOrchestrator()


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
    try:
        # Step 1: Validate dataset exists
        dataset = (
            db.query(Dataset)
            .filter(Dataset.id == job_request.dataset_id, Dataset.tenant_id == tenant_id)
            .first()
        )

        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Step 2: Create job record
        job_id = generate_job_id()

        hyperparameters = {
            "learning_rate": job_request.learning_rate,
            "num_epochs": job_request.num_epochs,
            "batch_size": job_request.batch_size,
            "lora_rank": job_request.lora_rank,
            "lora_alpha": job_request.lora_alpha,
            "lora_dropout": job_request.lora_dropout,
        }

        if job_request.hyperparameters:
            hyperparameters.update(job_request.hyperparameters)

        fine_tune_job = FineTuneJob(
            id=job_id,
            tenant_id=tenant_id,
            dataset_id=job_request.dataset_id,
            base_model_id=job_request.base_model_id,
            method=FineTuneMethod(job_request.method),
            adapter_name=job_request.adapter_name,
            learning_rate=job_request.learning_rate,
            num_epochs=job_request.num_epochs,
            batch_size=job_request.batch_size,
            lora_rank=job_request.lora_rank,
            lora_alpha=job_request.lora_alpha,
            lora_dropout=job_request.lora_dropout,
            hyperparameters=job_request.hyperparameters,
            auto_deploy=job_request.auto_deploy,
            status=JobStatus.PENDING,
        )

        db.add(fine_tune_job)
        db.commit()

        # Step 3: Create SageMaker training job
        try:
            dataset_s3_paths = {
                "train": dataset.train_s3_path,
                "val": dataset.val_s3_path,
                "test": dataset.test_s3_path,
            }

            sagemaker_job = training_orchestrator.create_training_job(
                job_id=job_id,
                tenant_id=tenant_id,
                base_model_id=job_request.base_model_id,
                dataset_s3_paths=dataset_s3_paths,
                adapter_name=job_request.adapter_name,
                method=FineTuneMethod(job_request.method),
                hyperparameters=hyperparameters,
            )

            # Update job with SageMaker details
            fine_tune_job.sagemaker_job_name = sagemaker_job["job_name"]
            fine_tune_job.sagemaker_job_arn = sagemaker_job["job_arn"]
            fine_tune_job.status = JobStatus.RUNNING

            db.commit()
            db.refresh(fine_tune_job)

            logger.info(f"Created fine-tune job {job_id} with SageMaker job {sagemaker_job['job_name']}")

        except Exception as e:
            # Update job status to failed
            fine_tune_job.status = JobStatus.FAILED
            fine_tune_job.error_message = str(e)
            db.commit()
            raise HTTPException(status_code=500, detail=f"Failed to create SageMaker job: {str(e)}")

        return fine_tune_job

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating fine-tune job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


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
