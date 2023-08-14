import logging

logger = logging.getLogger(__name__)

from .common import KubernetesResource, kgenlib


@kgenlib.register_generator(
    path="generators.prometheus.gen_pod_monitoring",
    apply_patches=["generators.prometheus.defaults.gen_pod_monitoring"],
)
class PodMonitoring(KubernetesResource):
    kind = "PodMonitoring"
    api_version = "monitoring.googleapis.com/v1"

    def body(self):
        super().body()
        self.root.spec = self.config


class PrometheusRule(KubernetesResource):
    kind = "PrometheusRule"
    api_version = "monitoring.coreos.com/v1"

    def body(self):
        super().body()
        name = self.name
        config = self.config
        self.root.spec.setdefault("groups", []).append(
            {"name": name, "rules": config.prometheus_rules.rules}
        )


class ServiceMonitor(KubernetesResource):
    kind = "ServiceMonitor"
    api_version = "monitoring.coreos.com/v1"

    def new(self):
        super().new()

    def body(self):
        name = self.name
        workload = self.workload
        self.name = "{}-metrics".format(name)

        super().body()
        name = self.name
        config = self.config
        self.root.spec.endpoints = config.service_monitors.endpoints
        self.root.spec.jobLabel = name
        self.root.spec.namespaceSelector.matchNames = [self.namespace]
        self.root.spec.selector.matchLabels = (
            workload.root.spec.template.metadata.labels
        )
