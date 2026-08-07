"""Observer orchestration module for AI-native DevOps monitoring."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.panel import Panel

from config import AppConfig
from kubernetes_client import KubernetesClient
from llm_analyzer import LLMAnalyzer
from log_collector import LogCollector
from notification_service import NotificationService
from remediation_engine import RemediationEngine
from report_generator import IncidentReportGenerator


class Observer:
    """Monitor Kubernetes pods and report failed containers."""

    def __init__(
        self,
        config: Any | None = None,
        client: KubernetesClient | None = None,
        log_collector: LogCollector | None = None,
        llm_analyzer: LLMAnalyzer | None = None,
        remediation_engine: RemediationEngine | None = None,
        report_generator: IncidentReportGenerator | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        """Initialize the observer with runtime configuration and dependencies."""
        self.config = config or AppConfig.from_env()
        self.client = client
        self.log_collector = log_collector
        self.llm_analyzer = llm_analyzer
        self.remediation_engine = remediation_engine
        self.report_generator = report_generator
        self.notification_service = notification_service
        self.console = Console()
        self._reported_failures: dict[tuple[str, str, str], dict[str, Any]] = {}

    def _initialize_dependencies(self) -> None:
        """Initialize optional services without crashing the observer."""
        if self.client is None:
            try:
                self.client = KubernetesClient(self.config)
            except Exception as exc:  # noqa: BLE001
                self.console.print(
                    f"[yellow]Kubernetes client unavailable: {exc}[/yellow]"
                )

        if self.log_collector is None:
            try:
                self.log_collector = LogCollector(self.config)
            except Exception as exc:  # noqa: BLE001
                self.console.print(f"[yellow]Log collector unavailable: {exc}[/yellow]")

        if self.llm_analyzer is None:
            try:
                self.llm_analyzer = LLMAnalyzer()
            except Exception as exc:  # noqa: BLE001
                self.console.print(f"[yellow]LLM analyzer unavailable: {exc}[/yellow]")

        if self.remediation_engine is None:
            try:
                self.remediation_engine = RemediationEngine(self.config)
            except Exception as exc:  # noqa: BLE001
                self.console.print(
                    f"[yellow]Remediation engine unavailable: {exc}[/yellow]"
                )

        if self.report_generator is None:
            try:
                self.report_generator = IncidentReportGenerator()
            except Exception as exc:  # noqa: BLE001
                self.console.print(f"[yellow]Report generator unavailable: {exc}[/yellow]")

        if self.notification_service is None:
            try:
                self.notification_service = NotificationService()
            except Exception as exc:  # noqa: BLE001
                self.console.print(
                    f"[yellow]Notification service unavailable: {exc}[/yellow]"
                )

    def run(self) -> None:
        """Continuously observe pods and report failures every 10 seconds."""
        try:
            self._initialize_dependencies()
            while True:
                scan_started_at = time.perf_counter()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.console.print("\nScanning cluster...")
                self.console.print(timestamp)

                if self.client is None:
                    self.console.print(
                        "[yellow]Kubernetes client unavailable. Skipping scan.[/yellow]"
                    )
                    time.sleep(10)
                    continue

                failed_pods = self.client.get_failed_pods()
                current_failures = {
                    (
                        pod["namespace"],
                        pod["pod_name"],
                        pod["reason"],
                    )
                    for pod in failed_pods
                }

                for key in list(self._reported_failures):
                    if key not in current_failures:
                        self.console.print(
                            f"[yellow]✓ Pod {key[1]} recovered[/yellow]"
                        )
                        del self._reported_failures[key]

                if failed_pods:
                    for pod in failed_pods:
                        failure_key = (
                            pod["namespace"],
                            pod["pod_name"],
                            pod["reason"],
                        )
                        if failure_key in self._reported_failures:
                            continue

                        self._reported_failures[failure_key] = {
                            "first_seen": timestamp,
                            "restart_count": pod["restart_count"],
                        }

                        content = (
                            f"Namespace      : {pod['namespace']}\n"
                            f"Pod            : {pod['pod_name']}\n"
                            f"Container      : {pod['container_name']}\n"
                            f"Reason         : {pod['reason']}\n"
                            f"Restart Count  : {pod['restart_count']}"
                        )
                        panel = Panel(
                            content,
                            title="🚨 Failed Pod Detected",
                            border_style="red",
                        )
                        self.console.print(panel)

                        try:
                            if self.log_collector is None:
                                raise RuntimeError("Log collector unavailable")
                            diagnostics = self.log_collector.collect_diagnostics(
                                pod["namespace"],
                                pod["pod_name"],
                            )
                            self.console.print(
                                Panel.fit(
                                    "AI analysis in progress...",
                                    title="🤖 AI Analysis",
                                    border_style="cyan",
                                )
                            )
                            if self.llm_analyzer is None:
                                raise RuntimeError("LLM analyzer unavailable")
                            analysis = self.llm_analyzer.analyze(diagnostics)
                            summary = analysis.get("summary", "No summary provided")
                            self.console.print(f"[cyan]AI Summary: {summary}[/cyan]")

                            remediation_result: dict[str, Any] | None = None
                            if analysis.get("safe_auto_remediation", False):
                                if self.remediation_engine is None:
                                    raise RuntimeError("Remediation engine unavailable")
                                self.console.print(
                                    Panel.fit(
                                        "Executing remediation...",
                                        title="🛠️ Remediation",
                                        border_style="yellow",
                                    )
                                )
                                self.remediation_engine.execute(analysis)
                                remediation_result = {
                                    "action": "Automated remediation",
                                    "status": "Executed",
                                    "details": "Remediation engine completed.",
                                }

                            if self.report_generator is None:
                                raise RuntimeError("Report generator unavailable")
                            report_path = self.report_generator.generate(
                                diagnostics,
                                analysis,
                                remediation_result,
                            )
                            self.console.print(
                                Panel.fit(
                                    f"Report generated: {report_path}",
                                    title="📝 Report Generated",
                                    border_style="green",
                                )
                            )

                            if self.notification_service is None:
                                raise RuntimeError("Notification service unavailable")
                            email_sent = self.notification_service.send_email(
                                subject=f"Incident Report: {pod['pod_name']}",
                                body="Incident report attached.",
                                attachment=report_path,
                            )
                            if email_sent:
                                self.console.print(
                                    Panel.fit(
                                        "Email sent successfully.",
                                        title="📧 Email Sent",
                                        border_style="magenta",
                                    )
                                )
                            else:
                                self.console.print(
                                    Panel.fit(
                                        "Email delivery failed.",
                                        title="📧 Email Sent",
                                        border_style="magenta",
                                    )
                                )
                        except Exception as exc:  # noqa: BLE001
                            self.console.print(
                                Panel.fit(
                                    str(exc),
                                    title="⚠️ Incident Handling Error",
                                    border_style="red",
                                )
                            )
                else:
                    self.console.print("[green]✓ No failed pods detected.[/green]")

                scan_duration = time.perf_counter() - scan_started_at
                self.console.print(
                    f"[dim]Number of failed pods: {len(failed_pods)}[/dim]"
                )
                self.console.print(
                    f"[dim]Number of cached alerts: {len(self._reported_failures)}[/dim]"
                )
                self.console.print(
                    f"[dim]Time taken for scan: {scan_duration:.2f}s[/dim]"
                )
                time.sleep(10)
        except KeyboardInterrupt:
            self.console.print("\n[bold yellow]Monitoring stopped.[/bold yellow]")
        except Exception as exc:
            self.console.print(
                Panel.fit(
                    f"{exc}",
                    title="⚠️ Observer Error",
                    border_style="red",
                )
            )
            time.sleep(10)


if __name__ == "__main__":
    observer = Observer()
    observer.run()
