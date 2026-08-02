from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.build import Build
from app.services.github_service import GitHubService


def test_github_service_parses_run_payload() -> None:
    """The GitHub service should map GitHub workflow payloads into the expected internal shape."""
    service = GitHubService()
    payload = {
        "name": "CI",
        "run_number": 7,
        "head_branch": "main",
        "head_sha": "abc123",
        "conclusion": "success",
        "run_started_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:05:00Z",
        "head_commit": {"message": "Ship", "author": {"name": "Alice"}},
        "logs_url": "https://example.com/logs",
    }

    result = service.parse_run(payload)

    assert result["pipeline_name"] == "CI"
    assert result["build_number"] == 7
    assert result["status"] == "success"
    assert result["branch"] == "main"


def test_github_service_only_notifies_for_newly_inserted_failed_runs() -> None:
    """The GitHub service should notify only when a newly inserted run is a failure."""
    service = GitHubService()
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        session.add(
            Build(
                pipeline_name="CI",
                build_number=42,
                workflow_name="CI",
                status="success",
                duration=120,
                branch="main",
                commit_id="abc123",
                commit_message="Ship",
                author="Alice",
                started_at=None,
                completed_at=None,
                logs=None,
            )
        )
        session.commit()

        payload = {
            "id": 42,
            "name": "CI",
            "run_number": 42,
            "head_branch": "main",
            "head_sha": "abc123",
            "conclusion": "failure",
            "run_started_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:05:00Z",
            "head_commit": {"message": "Ship", "author": {"name": "Alice"}},
            "logs_url": "https://example.com/logs",
            "html_url": "https://github.example/runs/42",
        }

        with patch.object(service, "list_workflow_runs", return_value=[payload]):
            service.sync_workflow_runs_to_db(session, owner="octo", repo="demo", per_page=10, max_pages=1)
            assert len(service.last_sync_stats["failed_builds"]) == 0

            payload["run_number"] = 43
            payload["id"] = 43
            payload["conclusion"] = "failure"
            service.sync_workflow_runs_to_db(session, owner="octo", repo="demo", per_page=10, max_pages=1)
            assert len(service.last_sync_stats["failed_builds"]) == 1
