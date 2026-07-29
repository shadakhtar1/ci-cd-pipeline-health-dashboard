from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.build import Build
from app.schemas.build import BuildRead, BuildSummary, RefreshResponse
from app.services.github_service import GitHubService
from app.services.metrics_service import MetricsService


class BuildService:
    """Service for persisting and retrieving build records."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.github_service = GitHubService()

    def list_builds(self, *, skip: int = 0, limit: int = 20) -> list[BuildRead]:
        builds = self.db.query(Build).order_by(Build.started_at.desc().nullslast(), Build.id.desc()).offset(skip).limit(limit).all()
        return [BuildRead.model_validate(build, from_attributes=True) for build in builds]

    def get_build(self, build_id: int) -> BuildRead | None:
        build = self.db.query(Build).filter(Build.id == build_id).first()
        if build is None:
            return None
        return BuildRead.model_validate(build, from_attributes=True)

    def get_dashboard_summary(self) -> BuildSummary:
        builds = self.db.query(Build).order_by(Build.started_at.desc().nullslast(), Build.id.desc()).all()
        total_builds = MetricsService.calculate_total_builds(builds)
        metrics = MetricsService.build_dashboard_metrics(builds)
        recent_builds = [BuildRead.model_validate(build, from_attributes=True) for build in builds[:5]]

        return BuildSummary(
            total_builds=metrics["total_builds"],
            success_rate=metrics["success_rate"],
            failure_rate=metrics["failure_rate"],
            average_build_duration=metrics["average_build_duration"],
            last_build_status=metrics["last_build_status"],
            successful_builds=metrics["successful_builds"],
            failed_builds=metrics["failed_builds"],
            running_builds=metrics["running_builds"],
            last_refresh_time=metrics["last_refresh_time"],
            recent_builds=recent_builds,
        )

    def refresh_builds(self) -> RefreshResponse:
        try:
            settings = get_settings()
            stats = self.github_service.sync_workflow_runs_to_db(
                self.db,
                owner=settings.github_owner,
                repo=settings.github_repo,
                per_page=20,
                max_pages=10,
            )
        except Exception as exc:
            return RefreshResponse(message=f"Refresh failed: {exc}", refreshed=0, inserted=0, updated=0, skipped=0)

        return RefreshResponse(
            message="Builds refreshed successfully",
            refreshed=stats["inserted"] + stats["updated"],
            inserted=stats["inserted"],
            updated=stats["updated"],
            skipped=stats["skipped"],
        )
