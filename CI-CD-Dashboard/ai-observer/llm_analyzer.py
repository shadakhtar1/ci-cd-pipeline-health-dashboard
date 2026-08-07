"""LLM-based analysis helpers for incident interpretation."""

from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console


class LLMAnalyzer:
    """Analyze pod diagnostics using the OpenAI Responses API."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        """Initialize the analyzer with configuration from the environment."""
        load_dotenv()

        resolved_api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required. Configure it in the environment or .env."
            )

        resolved_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        self.api_key = resolved_api_key
        self.model = resolved_model
        self.console = Console()
        self.client = OpenAI(api_key=self.api_key)

    def analyze(self, diagnostics: dict[str, Any]) -> dict[str, Any]:
        """Send diagnostics to the LLM and return a parsed RCA payload."""
        self.console.print("[cyan]Analyzing incident...[/cyan]")
        self.console.print("[cyan]Sending diagnostics to LLM...[/cyan]")

        prompt = self._build_prompt(diagnostics)

        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
                temperature=0.2,
            )
            content = self._extract_response_text(response)
            parsed = self._parse_json_response(content)
            if parsed is None:
                return {
                    "summary": "Unable to parse LLM response",
                    "raw_response": content,
                }
            self.console.print("[green]Analysis completed.[/green]")
            return parsed
        except Exception as exc:  # noqa: BLE001
            self.console.print(f"[yellow]LLM analysis failed: {exc}[/yellow]")
            return {
                "summary": "Unable to parse LLM response",
                "raw_response": str(exc),
            }

    def _build_prompt(self, diagnostics: dict[str, Any]) -> str:
        """Construct the incident analysis prompt for the LLM."""
        return (
            "You are a Senior Kubernetes SRE and DevOps Engineer. "
            "Analyze the following pod incident diagnostics and produce a structured "
            "Root Cause Analysis. Return ONLY valid JSON matching this schema:\n"
            "{\n"
            '  "summary": "...",\n'
            '  "root_cause": "...",\n'
            '  "severity": "Critical | High | Medium | Low",\n'
            '  "confidence": 0-100,\n'
            '  "recommended_actions": ["...", "..."],\n'
            '  "safe_auto_remediation": true,\n'
            '  "explanation": "..."\n'
            "}\n\n"
            f"Namespace: {diagnostics.get('namespace', '')}\n"
            f"Pod: {diagnostics.get('pod', '')}\n"
            f"Timestamp: {diagnostics.get('timestamp', '')}\n"
            "Diagnostics:\n"
            f"Logs:\n{diagnostics.get('logs', '')}\n\n"
            f"Events:\n{diagnostics.get('events', '')}"
        )

    def _extract_response_text(self, response: Any) -> str:
        """Extract plain text content from the OpenAI response object."""
        if hasattr(response, "output_text") and response.output_text:
            return response.output_text

        if hasattr(response, "output") and response.output:
            pieces: list[str] = []
            for item in response.output:
                if hasattr(item, "content"):
                    for content_item in item.content:
                        if hasattr(content_item, "text"):
                            pieces.append(content_item.text)
            if pieces:
                return "".join(pieces)

        return ""

    def _parse_json_response(self, content: str) -> dict[str, Any] | None:
        """Parse the LLM response as JSON when possible."""
        if not content:
            return None

        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            try:
                start = cleaned.find("{")
                end = cleaned.rfind("}")
                if start != -1 and end != -1 and end > start:
                    candidate = cleaned[start : end + 1]
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict):
                        return parsed
            except json.JSONDecodeError:
                return None

        return None
