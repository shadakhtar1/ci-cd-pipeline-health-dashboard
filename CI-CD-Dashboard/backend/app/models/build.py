from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Build(Base, TimestampMixin):
    """Represents a single CI/CD build execution record."""

    __tablename__ = "builds"

    __table_args__ = (
        Index("ix_builds_pipeline_name", "pipeline_name"),
        Index("ix_builds_status", "status"),
        Index("ix_builds_branch", "branch"),
        Index("ix_builds_started_at", "started_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pipeline_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    build_number: Mapped[int] = mapped_column(Integer, nullable=False)
    workflow_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    branch: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    commit_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    commit_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
