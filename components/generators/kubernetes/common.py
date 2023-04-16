from enum import Enum

from kapitan.inputs.kadet import BaseModel, BaseObj, Dict, load_from_search_paths

kgenlib = load_from_search_paths("generators")


class ResourceType(BaseModel):
    kind: str
    id: str
    api_version: str


class ResourceTypes(Enum):
    VERTICAL_POD_AUTOSCALER = ResourceType(kind="VerticalPodAutoscaler", api_version="autoscaling.k8s.io/v1beta2", id="vertical_pod_autoscaler")
    MUTATING_WEBHOOK_CONFIGURATION = ResourceType(kind="MutatingWebhookConfiguration", api_version="admissionregistration.k8s.io/v1", id="mutating_webhook_configuration")
    BACKEND_CONFIG = ResourceType(kind="BackendConfig", api_version="cloud.google.com/v1", id="backend_config")
    PROMETHEUS_RULE = ResourceType(kind="PrometheusRule", api_version="monitoring.coreos.com/v1", id="prometheus_rule")
    HORIZONTAL_POD_AUTOSCALER = ResourceType(kind="HorizontalPodAutoscaler", api_version="autoscaling.k8s.io/v2beta2", id="horizontal_pod_autoscaler")
    SERVICE_MONITOR = ResourceType(kind="ServiceMonitor", api_version="monitoring.coreos.com/v1", id="service_monitor")
    POD_DISRUPTION_BUDGET = ResourceType(kind="PodDisruptionBudget", api_version="policy/v1beta1", id="pod_disruption_budget")
    NAMESPACE = ResourceType(kind="Namespace", api_version="v1", id="namespace")
    INGRESS = ResourceType(kind="Ingress", api_version="networking.k8s.io/v1", id="ingress")
    DEPLOYMENT = ResourceType(kind="Deployment", api_version="apps/v1", id="deployment")
    DAEMON_SET = ResourceType(kind="DaemonSet", api_version="apps/v1", id="daemon_set")
    GOOGLE_MANAGED_CERTIFICATE = ResourceType(kind="ManagedCertificate", api_version="networking.gke.io/v1beta1", id="google_managed_certificate")
    POD_SECURITY_POLICY = ResourceType(kind="PodSecurityPolicy", api_version="policy/v1beta1", id="pod_security_policy")
    JOB = ResourceType(kind="Job", api_version="batch/v1", id="job")
    CRON_JOB = ResourceType(kind="Job", api_version="batch/v1beta1", id="cronjob")
    STATEFUL_SET = ResourceType(kind="StatefulSet", api_version="apps/v1", id="stateful_set")
    SERVICE_ACCOUNT = ResourceType(kind="ServiceAccount", api_version="v1", id="service_account")
    SERVICE = ResourceType(kind="Service", api_version="v1", id="service")
    CLUSTER_ROLE_BINDING = ResourceType(
        kind="ClusterRoleBinding",
        api_version="rbac.authorization.k8s.io/v1",
        id="cluster_role_binding",
    )
    CLUSTER_ROLE = ResourceType(
        kind="ClusterRole",
        api_version="rbac.authorization.k8s.io/v1",
        id="cluster_role",
    )
    ROLE_BINDING = ResourceType(
        kind="RoleBinding",
        api_version="rbac.authorization.k8s.io/v1",
        id="role_binding",
    )
    ROLE = ResourceType(
        kind="Role", api_version="rbac.authorization.k8s.io/v1", id="role"
    )
    NETWORK_POLICY = ResourceType(
        kind="NetworkPolicy", api_version="networking.k8s.io/v1", id="network_policy"
    )


class KubernetesResource(kgenlib.BaseContent):
    resource_type: ResourceType
    name: str
    api_version: str = None
    kind: str = None
    rendered_name: str = None
    id: str = None

    
    @property
    def component_name(self):
        return self.root.metadata.labels.get("app.kapicorp.dev/component", self.name)

    def new(self):
        self.kind = self.resource_type.kind
        self.api_version = self.resource_type.api_version
        self.id = self.resource_type.id
        self.namespace = self.config.get("namespace", None)

    def body(self):
        self.root.apiVersion = self.api_version
        self.root.kind = self.kind
        self.name = self.name
        self.rendered_name = self.config.get("rendered_name", self.name)
        self.root.metadata.namespace = self.namespace
        self.root.metadata.name = self.rendered_name
        self.add_label("name", self.name)

    def add_label(self, key: str, value: str):
        self.root.metadata.labels[key] = value

    def add_labels(self, labels: dict):
        for key, value in labels.items():
            self.add_label(key, value)

    def add_annotation(self, key: str, value: str):
        self.root.metadata.annotations[key] = value

    def add_annotations(self, annotations: dict):
        for key, value in annotations.items():
            self.add_annotation(key, value)

    def add_namespace(self, namespace: str):
        self.root.metadata.namespace = namespace

    def set_labels(self, labels: dict):
        self.root.metadata.labels = labels

    def set_annotations(self, annotations: dict):
        self.root.metadata.annotations = annotations

    def setup_global_defaults(self, inventory):
        try:
            globals = (
                inventory.parameters.generators.manifest.default_config.globals.get(
                    self.id, {}
                )
            )
            self.add_annotations(globals.get("annotations", {}))
            self.add_labels(globals.get("labels", {}))
        except AttributeError:
            pass


class Base(BaseObj):
    def new(self):
        self.need("apiVersion")
        self.need("kind")
        self.need("name")

    def body(self):
        self.root.apiVersion = self.kwargs.apiVersion
        self.root.kind = self.kwargs.kind
        self.name = self.kwargs.name
        self.root.metadata.name = self.kwargs.get("rendered_name", self.name)
        self.add_label("name", self.root.metadata.name)

    def add_labels(self, labels):
        for key, value in labels.items():
            self.add_label(key, value)

    def add_label(self, key, value):
        self.root.metadata.labels[key] = value

    def add_namespace(self, namespace):
        self.root.metadata.namespace = namespace

    def add_annotations(self, annotations):
        for key, value in annotations.items():
            self.add_annotation(key, value)

    def add_annotation(self, key, value):
        self.root.metadata.annotations[key] = value
