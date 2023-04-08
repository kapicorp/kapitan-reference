from kapitan.inputs.kadet import load_from_search_paths

from .common import KubernetesResource, ResourceTypes

kgenlib = load_from_search_paths("generators")


class NetworkPolicy(KubernetesResource):
    resource_type = ResourceTypes.NETWORK_POLICY.value

    def new(self):
        super().new()

    def body(self):
        super().body()
        policy = self.config
        workload = self.workload
        self.root.spec.podSelector.matchLabels = workload.root.metadata.labels
        self.root.spec.ingress = policy.ingress
        self.root.spec.egress = policy.egress
        if self.root.spec.ingress:
            self.root.spec.setdefault("policyTypes", []).append("Ingress")

        if self.root.spec.egress:
            self.root.spec.setdefault("policyTypes", []).append("Egress")
