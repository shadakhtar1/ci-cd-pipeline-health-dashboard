"""Safe Kubernetes remediation actions for the AI observer."""

from __future__ import annotations

from typing import Any

from kubernetes import client, config
from rich.console import Console


class RemediationEngine:
    """Execute predefined remediation actions against Kubernetes resources."""

    def __init__(self, config: Any | None = None) -> None:
        """Initialize the remediation engine with Kubernetes client access."""
        self.config = config
        self.console = Console()
        self._load_configuration()
        self.apps_api = client.AppsV1Api()

    def _load_configuration(self) -> None:
        """Load cluster configuration from in-cluster or local kubeconfig."""
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

    def restart_deployment(self, namespace: str, deployment_name: str) -> None:
        """Trigger a rollout restart for a deployment via a patch action."""
        self.console.print("[cyan]Restarting deployment...[/cyan]")
        try:
            deployment = self.apps_api.read_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
            )
            if deployment.spec.template.metadata.annotations is None:
                deployment.spec.template.metadata.annotations = {}
            deployment.spec.template.metadata.annotations["kubectl.kubernetes.io/restartedAt"] = (
                "now"
            )
            self.apps_api.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=deployment,
            )
            self.console.print(
                f"[green]Deployment {deployment_name} restarted.[/green]"
            )
        except Exception as exc:  # noqa: BLE001
            self.console.print(f"[yellow]Failed to restart deployment: {exc}[/yellow]")

    def rollback_argocd(self, application_name: str) -> None:
        """Log a placeholder rollback action for an Argo CD application."""
        self.console.print("[cyan]Rolling back Argo CD application...[/cyan]")
        self.console.print(
            f"[yellow]Argo CD rollback would be executed for {application_name}.[/yellow]"
        )

    def scale_deployment(self, namespace: str, deployment_name: str, replicas: int) -> None:
        """Scale a deployment to the requested replica count."""
        self.console.print("[cyan]Scaling deployment...[/cyan]")
        try:
            self.apps_api.patch_namespaced_deployment_scale(
                name=deployment_name,
                namespace=namespace,
                body={"spec": {"replicas": replicas}},
            )
            self.console.print(
                f"[green]Deployment {deployment_name} scaled to {replicas} replicas.[/green]"
            )
        except Exception as exc:  # noqa: BLE001
            self.console.print(f"[yellow]Failed to scale deployment: {exc}[/yellow]")

    def execute(self, ai_result: dict[str, Any]) -> None:
        """Execute only the predefined remediation actions allowed by the AI result."""
        self.console.print("[cyan]Executing remediation...[/cyan]")

        if not ai_result.get("safe_auto_remediation", False):
            self.console.print("[yellow]Auto-remediation skipped.[/yellow]")
            return

        actions = ai_result.get("recommended_actions", [])
        namespace = str(ai_result.get("namespace", "default") or "default").strip()
        deployment = str(ai_result.get("deployment", "") or "").strip()
        replicas = ai_result.get("replicas", 1)

        if not deployment and any(
            action.lower() in {"restart deployment", "restart application", "scale deployment"}
            for action in actions
        ):
            self.console.print(
                "[yellow]Skipping remediation because no deployment name was supplied.[/yellow]"
            )
            return

        for action in actions:
            normalized_action = str(action).strip().lower()
            if normalized_action in {"restart deployment", "restart application"}:
                self.restart_deployment(namespace, deployment)
            elif normalized_action == "scale deployment":
                self.scale_deployment(namespace, deployment, int(replicas))
            elif normalized_action == "rollback argocd":
                self.rollback_argocd(str(ai_result.get("application_name", "")))
            else:
                self.console.print(
                    f"[yellow]Ignoring unknown action: {action}[/yellow]"
                )

        self.console.print("[green]Remediation completed.[/green]")
