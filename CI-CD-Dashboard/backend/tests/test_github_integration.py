from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.build import Build
from app.services.github_service import GitHubService


def test_sync_workflow_runs_persists_builds_to_sqlite() -> None:
    """The GitHub integration service should store fetched workflow runs into SQLite."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    service = GitHubService()
    first_page = {
        "workflow_runs": [
            {
                "name": "CI",
                "run_number": 101,
                "head_branch": "main",
                "head_sha": "abc123",
                "conclusion": "success",
                "status": "completed",
                "run_started_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:05:00Z",
                "head_commit": {"message": "Ship it", "author": {"name": "Alice"}},
                "logs_url": "https://example.com/logs/101",
            }
        ]
    }

    with patch.object(service, "list_workflow_runs", return_value=first_page["workflow_runs"]):
        with Session(engine) as session:
            stored_count = service.sync_workflow_runs_to_db(session, owner="octocat", repo="hello-world")
            saved = session.query(Build).filter(Build.build_number == 101).first()

    assert stored_count == 1
    assert saved is not None
    assert saved.pipeline_name == "CI"
    assert saved.status == "success"


def test_list_workflow_runs_handles_pagination() -> None:
    """The GitHub service should follow pagination to collect all workflow runs."""
    service = GitHubService()

    page_one_response = Mock(status_code=200)
    page_one_response.json.return_value = {
        "workflow_runs": [{"id": 1, "name": "CI"}],
    }
    page_one_response.headers = {}

    page_two_response = Mock(status_code=200)
    page_two_response.json.return_value = {
        "workflow_runs": [{"id": 2, "name": "CD"}],
    }
    page_two_response.headers = {}

    with patch("app.services.github_service.requests.get", side_effect=[page_one_response, page_two_response]) as mocked_get:
        runs = service.list_workflow_runs(owner="octocat", repo="hello-world", per_page=1, max_pages=2)

    assert len(runs) == 2
    assert mocked_get.call_count == 2
