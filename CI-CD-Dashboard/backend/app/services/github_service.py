from __future__ import annotations

import time
from datetime import datetime
from typing import Any

import requests
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.models.build import Build

logger = get_logger(__name__)
settings = get_settings()


class GitHubService:
    """Service for fetching workflow run data from the GitHub REST API."""

    def __init__(self) -> None:
        self.base_url = "https://api.github.com"
        self.token = settings.github_token or ""
        self.owner = settings.github_owner or ""
        self.repo = settings.github_repo or ""
        self.last_sync_stats: dict[str, Any] | None = None

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, url: str, *, params: dict[str, Any] | None = None, retries: int = 3) -> dict[str, Any]:
        if not self.token:
            logger.warning("GitHub token is missing; continuing without authentication")

        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=self._build_headers(), params=params, timeout=15)
                if response.status_code == 401:
                    logger.error("GitHub authentication failed", extra={"status_code": response.status_code})
                    raise PermissionError("GitHub authentication failed")
                if response.status_code == 403:
                    if response.headers.get("X-RateLimit-Remaining") == "0":
                        logger.warning(
                            "GitHub rate limit reached",
                            extra={"reset_time": response.headers.get("X-RateLimit-Reset")},
                        )
                        raise TimeoutError("GitHub rate limit exceeded")
                    logger.warning("GitHub access forbidden", extra={"status_code": response.status_code})
                    raise PermissionError("GitHub access forbidden")
                if response.status_code >= 400:
                    logger.warning(
                        "GitHub API request failed",
                        extra={"status_code": response.status_code, "body": response.text[:500]},
                    )
                    raise RuntimeError(f"GitHub API request failed with status {response.status_code}")

                return response.json()
            except requests.Timeout as exc:
                last_error = exc
                logger.warning("GitHub request timed out, retrying", extra={"attempt": attempt + 1})
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
            except (PermissionError, TimeoutError, RuntimeError) as exc:
                last_error = exc
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("GitHub request failed")

    def list_workflow_runs(self, owner: str, repo: str, *, per_page: int = 10, max_pages: int = 1) -> list[dict[str, Any]]:
        all_runs: list[dict[str, Any]] = []
        page = 1
        while page <= max_pages:
            url = f"{self.base_url}/repos/{owner}/{repo}/actions/runs"
            params = {"per_page": per_page, "page": page}
            payload = self._request(url, params=params)
            runs = payload.get("workflow_runs", [])
            if not runs:
                break
            all_runs.extend(runs)
            page += 1

        logger.info(
            "Fetched workflow runs",
            extra={"owner": owner, "repo": repo, "count": len(all_runs)},
        )
        return all_runs

    def parse_run(self, run: dict[str, Any]) -> dict[str, Any]:
        started_at = self._parse_datetime(run.get("run_started_at"))
        completed_at = self._parse_datetime(run.get("updated_at"))
        head_commit = run.get("head_commit") if isinstance(run.get("head_commit"), dict) else {}
        author_name = None
        if isinstance(head_commit.get("author"), dict):
            author_name = head_commit["author"].get("name")

        duration_ms = run.get("run_duration_ms")
        duration = None
        if isinstance(duration_ms, (int, float)) and duration_ms is not None:
            duration = int(duration_ms / 1000)

        return {
            "id": run.get("id"),
            "pipeline_name": run.get("name") or run.get("head_branch") or "unknown",
            "build_number": run.get("run_number"),
            "workflow_name": run.get("name"),
            "status": (run.get("conclusion") or run.get("status") or "unknown").lower(),
            "duration": duration,
            "branch": run.get("head_branch"),
            "commit_id": run.get("head_sha"),
            "commit_message": head_commit.get("message"),
            "author": author_name,
            "started_at": started_at,
            "completed_at": completed_at,
            "logs_url": run.get("logs_url"),
            "build_url": run.get("html_url"),
        }

    def sync_workflow_runs_to_db(self, db: Session, *, owner: str | None = None, repo: str | None = None, per_page: int = 10, max_pages: int = 1) -> int:
        owner = owner or self.owner
        repo = repo or self.repo
        if not owner or not repo:
            logger.error("GitHub owner or repository is not configured")
            raise ValueError("GitHub owner and repository must be configured")

        runs = self.list_workflow_runs(owner, repo, per_page=per_page, max_pages=max_pages)
        inserted = 0
        updated = 0
        skipped = 0
        failed_builds: list[dict[str, Any]] = []

        for run in runs:
            parsed = self.parse_run(run)
            parsed["repository"] = f"{owner}/{repo}"
            existing = db.query(Build).filter(Build.build_number == parsed["build_number"]).first()
            should_notify_failure = False

            if existing is None:
                build = Build(
                    pipeline_name=parsed["pipeline_name"],
                    build_number=parsed["build_number"],
                    workflow_name=parsed["workflow_name"],
                    status=parsed["status"],
                    duration=parsed["duration"],
                    branch=parsed["branch"],
                    commit_id=parsed["commit_id"],
                    commit_message=parsed["commit_message"],
                    author=parsed["author"],
                    started_at=parsed["started_at"],
                    completed_at=parsed["completed_at"],
                    logs=parsed.get("logs_url"),
                )
                db.add(build)
                inserted += 1
                should_notify_failure = parsed["status"] == "failure"
            else:
                existing.pipeline_name = parsed["pipeline_name"]
                existing.workflow_name = parsed["workflow_name"]
                existing.status = parsed["status"]
                existing.duration = parsed["duration"]
                existing.branch = parsed["branch"]
                existing.commit_id = parsed["commit_id"]
                existing.commit_message = parsed["commit_message"]
                existing.author = parsed["author"]
                existing.started_at = parsed["started_at"]
                existing.completed_at = parsed["completed_at"]
                existing.logs = parsed.get("logs_url")
                updated += 1

            if should_notify_failure:
                failed_builds.append(parsed)

        db.commit()
        self.last_sync_stats = {
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "failed_builds": failed_builds,
        }
        logger.info(
            "Synced workflow runs to database",
            extra={"inserted": inserted, "updated": updated, "skipped": skipped},
        )
        return inserted + updated

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None
