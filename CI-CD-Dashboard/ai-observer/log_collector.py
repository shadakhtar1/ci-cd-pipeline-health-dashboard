"""Log collection utilities for workload and cluster diagnostics."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from kubernetes import client, config
from rich.console import Console


class LogCollector:
    """Collect pod logs, warning events, and diagnostic summaries."""

    def __init__(self, config: Any | None = None) -> None:
        """Initialize the collector with Kubernetes client configuration."""
        self.config = config
        self.console = Console()
        self._load_configuration()
        self.api = client.CoreV1Api()

    def _load_configuration(self) -> None:
        """Load cluster configuration from in-cluster or local kubeconfig."""
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

    def collect_logs(self, namespace: str, pod_name: str) -> str:
        """Return the last 200 log lines from all containers in a pod."""
        self.console.print("[cyan]Collecting logs...[/cyan]")
        try:
            pod = self.api.read_namespaced_pod(name=pod_name, namespace=namespace)
            container_names = [container.name for container in pod.spec.containers]

            if not container_names:
                return "No containers found for the pod."

            log_sections: list[str] = []
            total_lines = 0

            for container_name in container_names:
                logs = self.api.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=namespace,
                    container=container_name,
                    tail_lines=200,
                )
                lines = logs.splitlines()
                total_lines += len(lines)
                header = (
                    f"========================\n"
                    f"Container: {container_name}\n"
                    f"========================"
                )
                log_sections.append(header)
                log_sections.append("\n".join(lines))

            combined_logs = "\n\n".join(log_sections)
            combined_logs = self._limit_output(combined_logs)

            self.console.print(f"[green]Collected {total_lines} log lines[/green]")
            return combined_logs
        except Exception as exc:  # noqa: BLE001
            message = f"Unable to retrieve logs:\n{exc}"
            self.console.print(f"[yellow]{message}[/yellow]")
            return message

    def collect_events(self, namespace: str, pod_name: str) -> str:
        """Return warning events related to the specified pod."""
        try:
            events = self.api.list_namespaced_event(namespace)
            warning_events: list[str] = []

            for event in events.items:
                if getattr(event, "type", None) != "Warning":
                    continue
                involved_object = getattr(event.involved_object, "name", None)
                if involved_object != pod_name:
                    continue
                warning_events.append(
                    f"{event.metadata.creation_timestamp} {event.reason}: {event.message}"
                )

            if warning_events:
                self.console.print(
                    f"[green]Collected {len(warning_events)} warning events[/green]"
                )
                return "\n".join(warning_events)

            return "No warning events found."
        except Exception as exc:  # noqa: BLE001
            message = f"Unable to retrieve events:\n{exc}"
            self.console.print(f"[yellow]{message}[/yellow]")
            return message

    def collect_diagnostics(
        self, namespace: str, pod_name: str
    ) -> dict[str, str]:
        """Return structured diagnostic information for a pod."""
        return {
            "logs": self.collect_logs(namespace, pod_name),
            "events": self.collect_events(namespace, pod_name),
            "timestamp": datetime.now().isoformat(),
            "namespace": namespace,
            "pod": pod_name,
        }

    def _limit_output(self, content: str, max_bytes: int = 12 * 1024) -> str:
        """Trim output to the requested size while preserving readability."""
        if len(content.encode("utf-8")) <= max_bytes:
            return content

        trimmed = content.encode("utf-8")[:max_bytes]
        return trimmed.decode("utf-8", errors="ignore")
