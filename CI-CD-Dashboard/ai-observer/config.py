"""Configuration helpers for the AI observer project."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class AppConfig:
    """Runtime configuration for the observer."""

    namespace: str = "default"
    cluster_context: str | None = None
    llm_model: str = "gpt-4o-mini"
    log_tail_lines: int = 200
    openai_api_key: str | None = None

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration values from environment variables."""
        load_dotenv()
        return cls(
            namespace=os.getenv("OBS_NAMESPACE", "default"),
            cluster_context=os.getenv("CLUSTER_CONTEXT"),
            llm_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            log_tail_lines=int(os.getenv("LOG_TAIL_LINES", "200")),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )
