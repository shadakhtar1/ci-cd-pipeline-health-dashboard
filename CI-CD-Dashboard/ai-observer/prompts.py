"""Prompt templates for the AI observer workflow."""

from __future__ import annotations


def build_incident_prompt(context: dict[str, str]) -> str:
    """Build a compact incident prompt from diagnostic context."""
    lines = ["You are a Senior Kubernetes SRE. Analyze the incident context below."]
    for key, value in context.items():
        if value:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)
