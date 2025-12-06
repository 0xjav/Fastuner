"""Fine-tune job model for tracking training jobs"""

from sqlalchemy import String, Integer, JSON, ForeignKey, Enum as SQLEnum, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any
import enum

from .base import Base, TimestampMixin


class FineTuneMethod(str, enum.Enum):
    """Supported fine-tuning methods"""
    LORA = "lora"
    QLORA = "qlora"


class JobStatus(str, enum.Enum):
    """Fine-tune job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FineTuneJob(Base, TimestampMixin):
    """Fine-tune job model - tracks SageMaker training jobs"""

    __tablename__ = "fine_tune_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )

    # Job configuration
    base_model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[FineTuneMethod] = mapped_column(SQLEnum(FineTuneMethod), nullable=False)
    adapter_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Hyperparameters
    learning_rate: Mapped[float] = mapped_column(Float, default=0.0002, nullable=False)
    num_epochs: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    batch_size: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    lora_rank: Mapped[int] = mapped_column(Integer, default=16, nullable=False)
    lora_alpha: Mapped[int] = mapped_column(Integer, default=32, nullable=False)
    lora_dropout: Mapped[float] = mapped_column(Float, default=0.05, nullable=False)

    # Additional hyperparameters as JSON
    hyperparameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # SageMaker details
    sagemaker_job_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sagemaker_job_arn: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Status tracking
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metrics
    final_train_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_val_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metrics_s3_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Auto-deployment flag
    auto_deploy: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="fine_tune_jobs")
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="fine_tune_jobs")
    adapter: Mapped[Optional["Adapter"]] = relationship(
        "Adapter", back_populates="fine_tune_job", uselist=False
    )

    def __repr__(self) -> str:
        return f"<FineTuneJob(id={self.id}, status={self.status}, adapter_name={self.adapter_name})>"
