"""Tenant model for multi-tenancy support"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from .base import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    """Tenant model - represents an organization or user"""

    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cognito_user_pool_id: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    datasets: Mapped[List["Dataset"]] = relationship(
        "Dataset", back_populates="tenant", cascade="all, delete-orphan"
    )
    fine_tune_jobs: Mapped[List["FineTuneJob"]] = relationship(
        "FineTuneJob", back_populates="tenant", cascade="all, delete-orphan"
    )
    adapters: Mapped[List["Adapter"]] = relationship(
        "Adapter", back_populates="tenant", cascade="all, delete-orphan"
    )
    deployments: Mapped[List["Deployment"]] = relationship(
        "Deployment", back_populates="tenant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name})>"
