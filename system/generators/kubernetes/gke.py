import logging

logger = logging.getLogger(__name__)

from .common import KubernetesResource


class BackendConfig(KubernetesResource):
    kind = "BackendConfig"
    api_version = "cloud.google.com/v1"

    def body(self):
        super().body()
        self.root.spec = self.config.backend_config
