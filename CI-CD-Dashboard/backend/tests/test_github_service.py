from unittest.mock import Mock, patch

import pytest

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
