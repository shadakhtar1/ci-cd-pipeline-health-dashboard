from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BuildBase(BaseModel):
    pipeline_name: str = Field(..., min_length=1)
    build_number: int
    workflow_name: Optional[str] = None
    status: str = Field(..., min_length=1)
    duration: Optional[int] = None
    branch: Optional[str] = None
    commit_id: Optional[str] = None
    commit_message: Optional[str] = None
    author: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    logs: Optional[str] = None


class BuildCreate(BuildBase):
    pass


class BuildRead(BuildBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BuildSummary(BaseModel):
    total_builds: int
    success_rate: float
    failure_rate: float
    average_build_duration: float
    last_build_status: Optional[str]
    successful_builds: int
    failed_builds: int
    running_builds: int
    last_refresh_time: Optional[datetime]
    recent_builds: list[BuildRead]


class RefreshResponse(BaseModel):
    message: str
    refreshed: int
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
