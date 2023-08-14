import logging

logger = logging.getLogger(__name__)

from .common import KubernetesResource, kgenlib


@kgenlib.register_generator(path="certmanager.issuer")
class CertManagerIssuer(KubernetesResource):
    kind = "Issuer"
    api_version = "cert-manager.io/v1"

    def body(self):
        config = self.config
        super().body()
        self.root.spec = config.get("spec")


@kgenlib.register_generator(path="certmanager.cluster_issuer")
class CertManagerClusterIssuer(KubernetesResource):
    kind = "ClusterIssuer"
    api_version = "cert-manager.io/v1"

    def body(self):
        config = self.config
        super().body()
        self.root.spec = config.get("spec")


@kgenlib.register_generator(path="certmanager.certificate")
class CertManagerCertificate(KubernetesResource):
    kind = "Certificate"
    api_version = "cert-manager.io/v1"

    def body(self):
        config = self.config
        super().body()
        self.root.spec = config.get("spec")
