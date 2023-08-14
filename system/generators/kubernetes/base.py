import logging

logger = logging.getLogger(__name__)

from .common import KubernetesResource, kgenlib


class MutatingWebhookConfiguration(KubernetesResource):
    kind = "MutatingWebhookConfiguration"
    api_version = "admissionregistration.k8s.io/v1"

    def new(self):
        super().new()

    def body(self):
        super().body()
        name = self.name
        config = self.config
        self.root.webhooks = config.webhooks


class PriorityClass(KubernetesResource):
    kind = "PriorityClass"
    api_version = "scheduling.k8s.io/v1"
    priority: int

    def body(self):
        super().body()
        config = self.config
        self.root.value = self.priority
        self.root.globalDefault = False


class Namespace(KubernetesResource):
    kind = "Namespace"
    api_version = "v1"

    def body(self):
        super().body()
        config = self.config
        labels = config.get("labels", {})
        annotations = config.get("annotations", {})
        self.add_labels(labels)
        self.add_annotations(annotations)


@kgenlib.register_generator(path="generators.kubernetes.namespace")
class NamespaceGenerator(kgenlib.BaseStore):
    def body(self):
        name = self.config.get("name", self.name)
        self.add(Namespace(name=name, config=self.config))
