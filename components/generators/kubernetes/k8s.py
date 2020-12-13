import base64

from kapitan.inputs.kadet import BaseObj, inventory
from kapitan.utils import render_jinja2_file
from kapitan.cached import args

search_paths = args.get("search_paths")
inv = inventory()


class Base(BaseObj):
    def new(self):
        self.need("apiVersion")
        self.need("kind")
        self.need("name")

    def body(self):
        self.root.apiVersion = self.kwargs.apiVersion
        self.root.kind = self.kwargs.kind
        self.root.metadata.name = self.kwargs.name
        self.add_label('name', self.kwargs.name)

    def add_labels(self, labels):
        for key, value in labels.items():
            self.add_label(key, value)

    def add_label(self, key, value):
        self.root.metadata.labels[key] = value

    def add_namespace(self, namespace):
        self.root.metadata.namespace = namespace

    def add_annotations(self, annotations):
        self.root.metadata.annotations = annotations





def j2(filename, ctx):
    return render_jinja2_file(filename, ctx, search_paths=search_paths)


def merge(source, destination):
    """
    run me with nosetests --with-doctest file.py

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = destination.setdefault(key, value)

    return destination


class WorkloadCommon(BaseObj):
    def set_replicas(self, replicas):
        self.root.spec.replicas = replicas

    def add_containers(self, containers):
        self.root.spec.template.spec.containers += [container.root for container in containers]

    def add_volumes(self, volumes):
        for key, value in volumes.items():
            merge({"name": key}, value)
            self.root.spec.template.spec.volumes += [value]

    def add_volume_claims(self, volume_claims):
        for key, value in volume_claims.items():
            merge({"metadata": {"name": key, "labels": {"name": key}}}, value)
            self.root.spec.volumeClaimTemplates += [value]

    def add_volumes_from_config(self):
        component = self.kwargs.component
        component_name = self.kwargs.name

        configs = component.config_maps.items()
        secrets = component.secrets.items()

        for name, spec in configs:
            reference_name = name
            if len(component.config_maps) == 1:
                name = component_name
            else:
                name = "{}-{}".format(component_name, name)
            self.root.spec.template.spec.volumes += [{
                "name": reference_name,
                "configMap": {
                    "defaultMode": 420,
                    "name": name,
                    "items": [{"key": value, "path": value} for value in spec.get('items', [])]
                }
            }]
        for name, spec in secrets:
            reference_name = name
            if len(component.secrets) == 1:
                name = component_name
            else:
                name = "{}-{}".format(component_name, name)
            self.root.spec.template.spec.volumes += [{
                "name": reference_name,
                "secret": {
                    "defaultMode": 420,
                    "secretName": name,
                    "items": [{"key": value, "path": value} for value in spec.get('items', [])]
                }
            }]


class NetworkPolicy(Base):
    def new(self):
        self.kwargs.apiVersion = "networking.k8s.io/v1"
        self.kwargs.kind = "NetworkPolicy"
        super().new()
        self.need("policy")

    def body(self):
        super().body()
        policy = self.kwargs.policy
        self.root.spec.podSelector = policy.pod_selector
        self.root.spec.ingress = policy.ingress
        self.root.spec.egress = policy.egress
        if self.root.spec.ingress:
            self.root.spec.policyTypes += ["Ingress"]

        if self.root.spec.egress:
            self.root.spec.policyTypes += ["Egress"]


class ServiceAccount(Base):
    def new(self):
        self.kwargs.apiVersion = "v1"
        self.kwargs.kind = "ServiceAccount"
        super().new()

    def body(self):
        super().body()
        self.add_namespace(inv.parameters.namespace)


class ConfigMap(Base):
    def new(self):
        self.kwargs.apiVersion = "v1"
        self.kwargs.kind = "ConfigMap"
        super().new()
        self.need("config")
        self.need("component")

    def body(self):
        super().body()
        self.add_namespace(inv.parameters.namespace)
        config = self.kwargs.config
        component = self.kwargs.component
        self.add_labels(component.globals.config_maps.labels)

        for key, config_spec in config.data.items():
            if "value" in config_spec:
                self.root.data[key] = config_spec.get('value')
            if "template" in config_spec:
                self.root.data[key] = j2(config_spec.template, config_spec.get('values', {}))


class Secret(Base):
    def new(self):
        self.kwargs.apiVersion = "v1"
        self.kwargs.kind = "Secret"
        super().new()
        self.need("config")
        self.need("component")

    @staticmethod
    def encode_string(unencoded_string, use_tesoro=inv.parameters.use_tesoro):
        if use_tesoro:
            return unencoded_string
        else:
            return base64.b64encode(unencoded_string.encode('ascii')).decode('ascii')

    def body(self):
        super().body()
        self.root.type = "Opaque"
        self.add_namespace(inv.parameters.namespace)
        use_tesoro = inv.parameters.use_tesoro
        config = self.kwargs.config
        component = self.kwargs.component
        self.add_labels(component.globals.secrets.labels)

        if use_tesoro:
            data = self.root.stringData
        else:
            data = self.root.data

        for key, spec in config.data.items():
            if "value" in spec:
                if spec.get('b64_encode', False):
                    data[key] = Secret.encode_string(spec.get('value'), use_tesoro)
                else:
                    data[key] = spec.get('value')
            if "template" in spec:
                self.root.data[key] = j2(spec.template, spec.get('values', {}))


class Service(Base):
    def new(self):
        self.kwargs.apiVersion = "v1"
        self.kwargs.kind = "Service"
        super().new()
        self.need("component")
        self.need("workload")

    def body(self):
        super().body()
        self.add_namespace(inv.parameters.namespace)
        component = self.kwargs.component
        workload = self.kwargs.workload
        self.add_labels(component.get('labels', {}))
        self.root.spec.selector = workload.spec.template.metadata.labels
        self.root.spec.type = component.service.type
        self.root.spec.sessionAffinity = component.service.get("session_affinity", "None")
        all_ports = [component.ports] + [container.ports for container in component.additional_containers.values()]

        for port_name, port_spec in all_ports.pop().items():
            if "service_port" in port_spec:
                self.root.spec.ports += [{
                    "name": port_name,
                    "port": port_spec.service_port,
                    "targetPort": port_name,
                    "protocol": port_spec.get("protocol", "TCP")
                }]


class Deployment(Base, WorkloadCommon):
    def new(self):
        self.kwargs.apiVersion = "apps/v1"
        self.kwargs.kind = "Deployment"
        super().new()
        self.need("component")

    def body(self):
        default_strategy = {
            "type": "RollingUpdate",
            "rollingUpdate": {
                "maxSurge": "25%",
                "maxUnavailable": "25%"
            }
        }
        super().body()
        component = self.kwargs.component
        self.root.spec.template.metadata.labels = self.root.metadata.labels
        self.root.spec.selector.matchLabels = self.root.metadata.labels
        self.root.spec.template.spec.restartPolicy = component.get("restart_policy", "Always")
        self.root.spec.template.spec.terminationGracePeriodSeconds = component.get("grace_period", 30)
        self.root.spec.strategy = component.get("strategy", default_strategy)


class StatefulSet(Base, WorkloadCommon):
    def new(self):
        self.kwargs.apiVersion = "apps/v1"
        self.kwargs.kind = "StatefulSet"
        super().new()
        self.need("component")

    def body(self):
        default_strategy = {}
        update_strategy = {"rollingUpdate":
                               {"partition": 0},
                           "type": "RollingUpdate"}

        super().body()
        name = self.kwargs.name
        component = self.kwargs.component
        self.root.spec.template.metadata.labels = self.root.metadata.labels
        self.root.spec.selector.matchLabels = self.root.metadata.labels
        self.root.spec.template.spec.restartPolicy = component.get("restart_policy", "Always")
        self.root.spec.template.spec.terminationGracePeriodSeconds = component.get("grace_period", 30)
        self.root.spec.strategy = component.get("strategy", default_strategy)
        self.root.spec.updateStrategy = component.get("update_strategy", update_strategy)
        self.root.spec.serviceName = name


class Container(BaseObj):
    def new(self):
        self.need("name")
        self.need("container")

    def process_envs(self, container):
        for name, value in sorted(container.env.items()):
            if isinstance(value, dict):
                if "secretKeyRef" in value:
                    value["secretKeyRef"]["name"] = self.kwargs.name
                    self.root.env += [{"name": name, "valueFrom": value}]
            else:
                self.root.env += [{"name": name, "value": str(value)}]

    def add_volume_mounts_from_configs(self):
        name = self.kwargs.name
        container = self.kwargs.container
        configs = container.config_maps.items()
        secrets = container.secrets.items()
        for name, spec in configs:
            if "mount" in spec:
                self.root.volumeMounts += [{
                    "mountPath": spec.mount,
                    "readOnly": True,
                    "name": name,
                    "subPath": spec.subPath
                }]
        for name, spec in secrets:
            if "mount" in spec:
                self.root.volumeMounts += [{
                    "mountPath": spec.mount,
                    "readOnly": True,
                    "name": name,
                    "subPath": spec.subPath
                }]

    def add_volume_mounts(self, volume_mounts):
        for key, value in volume_mounts.items():
            merge({"name": key}, value)
            self.root.volumeMounts += [value]

    @staticmethod
    def create_probe(probe_definition):
        probe = BaseObj()
        if "type" in probe_definition:
            probe.root.initialDelaySeconds = probe_definition.get('initial_delay_seconds', 0)
            probe.root.periodSeconds = probe_definition.get('period_seconds', 10)
            probe.root.timeoutSeconds = probe_definition.get('timeout_seconds', 5)
            probe.root.successThreshold = probe_definition.get('success_threshold', 1)
            probe.root.failureThreshold = probe_definition.get('failure_threshold', 3)

            if probe_definition.type == "http":
                probe.root.httpGet.scheme = probe_definition.get('scheme', "HTTP")
                probe.root.httpGet.port = probe_definition.port
                probe.root.httpGet.path = probe_definition.path
                probe.root.httpGet.httpHeaders = probe_definition.httpHeaders
            if probe_definition.type == "tcp":
                probe.root.tcpSocket.port = probe_definition.port
            if probe_definition.type == "command":
                probe.root.exec.command = probe_definition.command
        return probe.root

    def body(self):
        name = self.kwargs.name
        container = self.kwargs.container

        self.root.name = name
        self.root.image = container.image
        self.root.imagePullPolicy = container.get('pull_policy', 'IfNotPresent')
        self.root.resources = container.resources
        self.root.args = container.args
        self.root.command = container.command
        # legacy container.security
        if container.security:
            self.root.securityContext.allowPrivilegeEscalation = container.security.allow_privilege_escalation
            self.root.securityContext.runAsUser = container.security.user_id
        else:
            self.root.securityContext = container.security_context
        self.add_volume_mounts_from_configs()
        self.add_volume_mounts(container.volume_mounts)

        for name, port in container.ports.items():
            self.root.ports += [{
                "containerPort": port.get('container_port', port.service_port),
                "name": name,
                "protocol": port.get("protocol", "TCP")
            }]

        self.root.livenessProbe = self.create_probe(container.healthcheck.liveness)
        self.root.readinessProbe = self.create_probe(container.healthcheck.readiness)
        self.process_envs(container)


class PrometheusRule(Base):
    def new(self):
        self.kwargs.apiVersion = "monitoring.coreos.com/v1"
        self.kwargs.kind = "PrometheusRule"
        super().new()
        self.need("component")

    def body(self):
        # TODO(ademaria) This name mangling is here just to simplify diff.
        # Change it once done
        component_name = self.kwargs.name
        self.kwargs.name = "{}.rules".format(component_name)
        super().body()
        name = self.kwargs.name
        component = self.kwargs.component
        self.add_namespace(inv.parameters.namespace)

        # TODO(ademaria): use `name` instead of `tesoro.rules`
        self.root.spec.groups += [{"name": "tesoro.rules", "rules": component.prometheus_rules.rules}]


class ServiceMonitor(Base):
    def new(self):
        self.kwargs.apiVersion = "monitoring.coreos.com/v1"
        self.kwargs.kind = "ServiceMonitor"
        super().new()
        self.need("component")

    def body(self):
        # TODO(ademaria) This name mangling is here just to simplify diff.
        # Change it once done
        component_name = self.kwargs.name
        self.kwargs.name = "{}-metrics".format(component_name)

        super().body()
        name = self.kwargs.name
        component = self.kwargs.component
        self.add_namespace(inv.parameters.namespace)
        self.root.spec.endpoints = component.service_monitors.endpoints
        self.root.spec.jobLabel = name
        self.root.spec.namespaceSelector.matchNames = [component_name]
        self.root.spec.selector.matchLabels["name"] = component_name


class MutatingWebhookConfiguration(Base):
    def new(self):
        self.kwargs.apiVersion = "admissionregistration.k8s.io/v1beta1"
        self.kwargs.kind = "MutatingWebhookConfiguration"
        super().new()
        self.need("component")

    def body(self):
        super().body()
        name = self.kwargs.name
        component = self.kwargs.component
        self.root.webhooks = component.webhooks


class ClusterRole(Base):
    def new(self):
        self.kwargs.apiVersion = "rbac.authorization.k8s.io/v1beta1"
        self.kwargs.kind = "ClusterRole"
        super().new()
        self.need("component")

    def body(self):
        super().body()
        name = self.kwargs.name
        component = self.kwargs.component
        self.root.rules = component.cluster_role.rules


class ClusterRoleBinding(Base):
    def new(self):
        self.kwargs.apiVersion = "rbac.authorization.k8s.io/v1beta1"
        self.kwargs.kind = "ClusterRoleBinding"
        super().new()
        self.need("component")

    def body(self):
        super().body()
        name = self.kwargs.name
        component = self.kwargs.component
        self.root.roleRef = component.cluster_role.binding.roleRef
        self.root.subjects = component.cluster_role.binding.subjects