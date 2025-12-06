"""Deployment model for tracking SageMaker inference endpoints"""

from sqlalchemy import String, Integer, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime
import enum

from .base import Base, TimestampMixin


class DeploymentStatus(str, enum.Enum):
    """Deployment status"""
    CREATING = "creating"
    ACTIVE = "active"
    UPDATING = "updating"
    DELETING = "deleting"
    DELETED = "deleted"
    FAILED = "failed"


class Deployment(Base, TimestampMixin):
    """Deployment model - tracks SageMaker inference endpoints"""

    __tablename__ = "deployments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    adapter_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("adapters.id", ondelete="CASCADE"), nullable=False
    )

    # SageMaker endpoint details
    endpoint_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    endpoint_config_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    endpoint_arn: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Instance configuration
    instance_type: Mapped[str] = mapped_column(
        String(50), default="ml.g5.2xlarge", nullable=False
    )
    instance_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Status
    status: Mapped[DeploymentStatus] = mapped_column(
        SQLEnum(DeploymentStatus), default=DeploymentStatus.CREATING, nullable=False
    )

    # Ephemerality tracking
    ttl_seconds: Mapped[int] = mapped_column(
        Integer, default=3600, nullable=False  # 1 hour default
    )
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="deployments")
    adapter: Mapped["Adapter"] = relationship("Adapter", back_populates="deployments")

    def __repr__(self) -> str:
        return f"<Deployment(id={self.id}, endpoint_name={self.endpoint_name}, status={self.status})>"
