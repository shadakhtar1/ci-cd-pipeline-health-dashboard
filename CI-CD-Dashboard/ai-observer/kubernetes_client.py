"""Kubernetes client wrapper for cluster inspection and operations."""

from __future__ import annotations

from typing import Any

from kubernetes import client, config


class KubernetesClient:
    """Wrap Kubernetes API access for the observer."""

    def __init__(self, config_data: Any | None = None) -> None:
        """Initialize the client with cluster configuration."""
        self.config_data = config_data
        self._load_configuration()
        self.api = client.CoreV1Api()

    def _load_configuration(self) -> None:
        """Load cluster configuration from in-cluster or local kubeconfig."""
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

    def get_failed_pods(self, namespace: str | None = None) -> list[dict[str, Any]]:
        """Return pods whose containers are in a failed waiting/terminated state."""
        failed_pods: list[dict[str, Any]] = []
        failed_reasons = {
            "CrashLoopBackOff",
            "ImagePullBackOff",
            "ErrImagePull",
            "Error",
            "OOMKilled",
        }

        if namespace:
            pod_list = self.api.list_namespaced_pod(namespace)
        else:
            pod_list = self.api.list_pod_for_all_namespaces()

        for pod in pod_list.items:
            pod_namespace = pod.metadata.namespace or "default"
            pod_name = pod.metadata.name or "unknown"
            statuses = pod.status.container_statuses or []

            for container_status in statuses:
                state = container_status.state
                if state.waiting and state.waiting.reason in failed_reasons:
                    failed_pods.append(
                        {
                            "namespace": pod_namespace,
                            "pod_name": pod_name,
                            "container_name": container_status.name,
                            "reason": state.waiting.reason,
                            "restart_count": container_status.restart_count,
                        }
                    )
                    continue

                if state.terminated and state.terminated.reason in failed_reasons:
                    failed_pods.append(
                        {
                            "namespace": pod_namespace,
                            "pod_name": pod_name,
                            "container_name": container_status.name,
                            "reason": state.terminated.reason,
                            "restart_count": container_status.restart_count,
                        }
                    )

        return failed_pods
