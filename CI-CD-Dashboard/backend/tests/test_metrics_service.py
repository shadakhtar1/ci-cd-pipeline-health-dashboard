from datetime import datetime, timezone

from app.models.build import Build
from app.services.metrics_service import MetricsService


def test_metrics_service_calculates_dashboard_values() -> None:
    """The metrics service should compute dashboard statistics from build rows."""
    builds = [
        Build(
            pipeline_name="ci",
            build_number=1,
            workflow_name="CI",
            status="success",
            duration=120,
            branch="main",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ),
        Build(
            pipeline_name="ci",
            build_number=2,
            workflow_name="CI",
            status="failure",
            duration=300,
            branch="main",
            created_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
        ),
        Build(
            pipeline_name="ci",
            build_number=3,
            workflow_name="CI",
            status="in_progress",
            duration=None,
            branch="main",
            created_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
        ),
    ]

    metrics = MetricsService.build_dashboard_metrics(builds)

    assert metrics["total_builds"] == 3
    assert metrics["success_rate"] == 33.33
    assert metrics["failure_rate"] == 33.33
    assert metrics["average_build_duration"] == 140.0
    assert metrics["successful_builds"] == 1
    assert metrics["failed_builds"] == 1
    assert metrics["running_builds"] == 1
    assert metrics["last_build_status"] == "in_progress"
