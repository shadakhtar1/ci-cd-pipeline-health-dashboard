from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from app.models.build import Build


class MetricsService:
    """Compute dashboard metrics from build records."""

    @staticmethod
    def calculate_success_rate(builds: Sequence[Build]) -> float:
        if not builds:
            return 0.0
        success_count = sum(1 for build in builds if build.status.lower() == "success")
        return round((success_count / len(builds)) * 100, 2)

    @staticmethod
    def calculate_failure_rate(builds: Sequence[Build]) -> float:
        if not builds:
            return 0.0
        failure_count = sum(1 for build in builds if build.status.lower() == "failure")
        return round((failure_count / len(builds)) * 100, 2)

    @staticmethod
    def calculate_average_build_duration(builds: Sequence[Build]) -> float:
        if not builds:
            return 0.0
        durations = [build.duration or 0 for build in builds]
        return round(sum(durations) / len(durations), 2)

    @staticmethod
    def calculate_last_build_status(builds: Sequence[Build]) -> str | None:
        if not builds:
            return None
        latest_build = max(
            builds,
            key=lambda build: (build.updated_at or build.created_at or datetime.min.replace(tzinfo=timezone.utc)),
        )
        return latest_build.status

    @staticmethod
    def calculate_total_builds(builds: Sequence[Build]) -> int:
        return len(builds)

    @staticmethod
    def calculate_successful_builds(builds: Sequence[Build]) -> int:
        return sum(1 for build in builds if build.status.lower() == "success")

    @staticmethod
    def calculate_failed_builds(builds: Sequence[Build]) -> int:
        return sum(1 for build in builds if build.status.lower() == "failure")

    @staticmethod
    def calculate_running_builds(builds: Sequence[Build]) -> int:
        return sum(1 for build in builds if build.status.lower() in {"in_progress", "running", "queued"})

    @staticmethod
    def calculate_last_refresh_time(builds: Sequence[Build]) -> datetime | None:
        if not builds:
            return None
        latest = max((build.updated_at for build in builds if build.updated_at), default=None)
        if latest is None:
            latest = max((build.created_at for build in builds if build.created_at), default=None)
        return latest

    @classmethod
    def build_dashboard_metrics(cls, builds: Sequence[Build]) -> dict[str, object]:
        return {
            "total_builds": cls.calculate_total_builds(builds),
            "success_rate": cls.calculate_success_rate(builds),
            "failure_rate": cls.calculate_failure_rate(builds),
            "average_build_duration": cls.calculate_average_build_duration(builds),
            "last_build_status": cls.calculate_last_build_status(builds),
            "successful_builds": cls.calculate_successful_builds(builds),
            "failed_builds": cls.calculate_failed_builds(builds),
            "running_builds": cls.calculate_running_builds(builds),
            "last_refresh_time": cls.calculate_last_refresh_time(builds),
        }
