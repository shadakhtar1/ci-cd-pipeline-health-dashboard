from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.mail.smtp_service import SMTPEmailService
from app.models.build import Build
from app.schemas.build import BuildRead, BuildSummary, RefreshResponse
from app.services.github_service import GitHubService
from app.services.metrics_service import MetricsService

logger = get_logger(__name__)


class BuildService:
    """Service for persisting and retrieving build records."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.github_service = GitHubService()
        self.email_service = SMTPEmailService()

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
            refreshed_count = self.github_service.sync_workflow_runs_to_db(
                self.db,
                owner=settings.github_owner,
                repo=settings.github_repo,
                per_page=20,
                max_pages=10,
            )
            sync_stats = getattr(self.github_service, "last_sync_stats", None) or {}
        except Exception as exc:
            return RefreshResponse(message=f"Refresh failed: {exc}", refreshed=0, inserted=0, updated=0, skipped=0)

        alerts_sent = 0
        for failed_build in sync_stats.get("failed_builds", []):
            try:
                if self.email_service.send_failure_alert(
                    pipeline_name=failed_build.get("pipeline_name") or failed_build.get("workflow_name") or "unknown",
                    build_number=failed_build.get("build_number") or 0,
                    branch=failed_build.get("branch"),
                    commit_sha=failed_build.get("commit_id"),
                    status=failed_build.get("status"),
                    duration=failed_build.get("duration"),
                    build_url=failed_build.get("build_url"),
                    timestamp=failed_build.get("completed_at") or failed_build.get("started_at"),
                ):
                    alerts_sent += 1
            except Exception as exc:
                logger.exception("Failed to deliver failure alert", extra={"error": str(exc), "build_number": failed_build.get("build_number")})

        logger.info("Completed refresh and alert processing", extra={"alerts_sent": alerts_sent})
        return RefreshResponse(
            message="Builds refreshed successfully",
            refreshed=refreshed_count,
            inserted=sync_stats.get("inserted", 0),
            updated=sync_stats.get("updated", 0),
            skipped=sync_stats.get("skipped", 0),
        )
