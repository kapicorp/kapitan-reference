import logging

logger = logging.getLogger(__name__)

from .common import KubernetesResource


class KedaScaledObject(KubernetesResource):
    kind = "ScaledObject"
    api_version = "keda.sh/v1alpha1"

    def body(self):
        super().body()
        config = self.config
        workload = self.workload
        self.root.spec.scaleTargetRef.name = workload.root.metadata.name
        self.root.spec.scaleTargetRef.kind = workload.root.kind
        self.root.spec.scaleTargetRef.apiVersion = workload.root.apiVersion
        self.root.spec.update(config.get("keda_scaled_object", {}))


class PodDisruptionBudget(KubernetesResource):
    kind = "PodDisruptionBudget"
    api_version = "policy/v1beta1"

    def body(self):
        super().body()
        config = self.config
        workload = self.workload
        if config.auto_pdb:
            self.root.spec.maxUnavailable = 1
        else:
            self.root.spec.minAvailable = config.pdb_min_available
        self.root.spec.selector.matchLabels = (
            workload.root.spec.template.metadata.labels
        )


class VerticalPodAutoscaler(KubernetesResource):
    kind = "VerticalPodAutoscaler"
    api_version = "autoscaling.k8s.io/v1"

    def body(self):
        super().body()
        config = self.config
        workload = self.workload
        self.add_labels(workload.root.metadata.labels)
        self.root.spec.targetRef.apiVersion = workload.api_version
        self.root.spec.targetRef.kind = workload.kind
        self.root.spec.targetRef.name = workload.name
        self.root.spec.updatePolicy.updateMode = config.vpa.get("update_mode", "Auto")
        self.root.spec.resourcePolicy = config.vpa.get("resource_policy", {})


class HorizontalPodAutoscaler(KubernetesResource):
    kind = "HorizontalPodAutoscaler"
    api_version = "autoscaling.k8s.io/v2beta2"

    def body(self):
        super().body()
        config = self.config
        workload = self.workload
        self.add_labels(workload.root.metadata.labels)
        self.root.spec.scaleTargetRef.apiVersion = workload.api_version
        self.root.spec.scaleTargetRef.kind = workload.kind
        self.root.spec.scaleTargetRef.name = workload.name
        self.root.spec.minReplicas = config.hpa.min_replicas
        self.root.spec.maxReplicas = config.hpa.max_replicas
        self.root.spec.metrics = config.hpa.metrics
