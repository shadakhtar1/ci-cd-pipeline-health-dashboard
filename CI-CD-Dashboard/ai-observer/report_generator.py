"""Generate Markdown incident reports for AI observer analyses."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


class IncidentReportGenerator:
    """Create professional Markdown incident reports from diagnostics and analysis."""

    def __init__(self, reports_dir: str | Path | None = None) -> None:
        """Initialize the generator with a reports output directory."""
        default_reports_dir = Path(__file__).resolve().parent / "reports"
        self.reports_dir = Path(reports_dir) if reports_dir is not None else default_reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        diagnostics: dict[str, Any],
        analysis: dict[str, Any],
        remediation_result: dict[str, Any] | None = None,
    ) -> str:
        """Create a Markdown incident report and save it to the reports directory."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_path = self.reports_dir / f"incident-{timestamp}.md"

        incident_timestamp = diagnostics.get("timestamp", datetime.now().isoformat())
        namespace = diagnostics.get("namespace", "unknown")
        pod = diagnostics.get("pod", "unknown")
        container = diagnostics.get("container", "unknown")
        events = diagnostics.get("events", "")
        logs = diagnostics.get("logs", "")

        summary = analysis.get("summary", "N/A")
        root_cause = analysis.get("root_cause", "N/A")
        severity = analysis.get("severity", "Unknown")
        confidence = analysis.get("confidence", "N/A")
        recommended_actions = analysis.get("recommended_actions", [])

        remediation_status = "Skipped"
        remediation_details = "No remediation executed."
        remediation_action = "None"

        if remediation_result is not None:
            remediation_action = remediation_result.get("action", "None")
            remediation_status = remediation_result.get("status", "Unknown")
            remediation_details = remediation_result.get("details", "No details provided.")

        report_lines: list[str] = []
        report_lines.append("# AI Incident Report")
        report_lines.append("")
        report_lines.append("## Incident Details")
        report_lines.append("")
        report_lines.append(f"- Timestamp: {incident_timestamp}")
        report_lines.append(f"- Namespace: {namespace}")
        report_lines.append(f"- Pod: {pod}")
        report_lines.append(f"- Container: {container}")
        report_lines.append("")
        report_lines.append("## AI Summary")
        report_lines.append("")
        report_lines.append(f"- Summary: {summary}")
        report_lines.append(f"- Root Cause: {root_cause}")
        report_lines.append(f"- Severity: {severity}")
        report_lines.append(f"- Confidence: {confidence}")
        report_lines.append("")
        report_lines.append("## Kubernetes Events")
        report_lines.append("")
        report_lines.append(events or "No warning events collected.")
        report_lines.append("")
        report_lines.append("## Recent Pod Logs")
        report_lines.append("")
        report_lines.append("```text")
        report_lines.append(logs or "No logs collected.")
        report_lines.append("```")
        report_lines.append("")
        report_lines.append("## Recommended Actions")
        report_lines.append("")
        if recommended_actions:
            for action in recommended_actions:
                report_lines.append(f"- {action}")
        else:
            report_lines.append("- None provided.")
        report_lines.append("")
        report_lines.append("## Auto Remediation")
        report_lines.append("")
        report_lines.append(
            f"- Executed: {'Yes' if remediation_result is not None else 'No'}"
        )
        report_lines.append(f"- Skipped: {'Yes' if remediation_result is None else 'No'}")
        report_lines.append(f"- Failed: {'No' if remediation_result is None else 'No'}")
        report_lines.append("")
        if remediation_result is not None:
            report_lines.append(f"- Action: {remediation_action}")
            report_lines.append(f"- Status: {remediation_status}")
            report_lines.append(f"- Details: {remediation_details}")

        report_content = "\n".join(report_lines) + "\n"
        report_path.write_text(report_content, encoding="utf-8")
        return str(report_path)
