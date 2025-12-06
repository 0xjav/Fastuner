"""Adapter model for storing fine-tuned adapter artifacts"""

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from .base import Base, TimestampMixin


class Adapter(Base, TimestampMixin):
    """Adapter model - stores metadata about LoRA/QLoRA adapters"""

    __tablename__ = "adapters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    fine_tune_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fine_tune_jobs.id", ondelete="CASCADE"), nullable=False
    )

    # Adapter metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_model_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # S3 storage
    s3_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Version tracking
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="adapters")
    fine_tune_job: Mapped["FineTuneJob"] = relationship(
        "FineTuneJob", back_populates="adapter"
    )
    deployments: Mapped[list["Deployment"]] = relationship(
        "Deployment", back_populates="adapter", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Adapter(id={self.id}, name={self.name}, version={self.version})>"
