"""Dataset model for storing dataset metadata"""

from sqlalchemy import String, Integer, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any
import enum

from .base import Base, TimestampMixin


class TaskType(str, enum.Enum):
    """Supported task types for datasets"""
    TEXT_GENERATION = "text_generation"
    CLASSIFICATION = "classification"
    QA = "qa"


class Dataset(Base, TimestampMixin):
    """Dataset model - stores metadata about uploaded datasets"""

    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )

    # Dataset metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_type: Mapped[TaskType] = mapped_column(SQLEnum(TaskType), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(50), default="v0_text", nullable=False)

    # S3 paths
    raw_s3_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    train_s3_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    val_s3_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    test_s3_path: Mapped[str] = mapped_column(String(1024), nullable=False)

    # Statistics
    total_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    train_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    val_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    test_samples: Mapped[int] = mapped_column(Integer, nullable=False)

    # Splitting configuration
    split_seed: Mapped[int] = mapped_column(Integer, nullable=False)
    split_ratios: Mapped[Dict[str, float]] = mapped_column(
        JSON, default={"train": 0.8, "val": 0.1, "test": 0.1}, nullable=False
    )

    # Additional metadata
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="datasets")
    fine_tune_jobs: Mapped[list["FineTuneJob"]] = relationship(
        "FineTuneJob", back_populates="dataset", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, name={self.name}, task_type={self.task_type})>"
