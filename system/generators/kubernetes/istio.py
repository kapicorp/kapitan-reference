import logging

logger = logging.getLogger(__name__)

from .common import KubernetesResource


class IstioPolicy(KubernetesResource):
    kind = "IstioPolicy"
    api_version = "authentication.istio.io/v1alpha1"

    def body(self):
        super().body()
        config = self.config
        name = self.name
        self.root.spec.origins = config.istio_policy.policies.origins
        self.root.spec.principalBinding = "USE_ORIGIN"
        self.root.spec.targets = [{"name": name}]
