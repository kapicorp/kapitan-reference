import base64
import copy
import os
import json
import hashlib

from kapitan.inputs.kadet import BaseObj, inventory, CompileError
from kapitan.utils import render_jinja2_file
from kapitan.cached import args

from . import k8s

search_paths = args.get("search_paths")

inv = inventory()


def j2(filename, ctx):
    return render_jinja2_file(filename, ctx, search_paths=search_paths)


def merge(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, value)
            if node is None:
                destination[key] = value
            else:
                merge(value, node)
        else:
            destination[key] = destination.setdefault(key, value)

    return destination


class WorkloadCommon(BaseObj):
    def set_replicas(self, replicas):
        self.root.spec.replicas = replicas

    def add_containers(self, containers):
        self.root.spec.template.spec.containers += [
            container.root for container in containers]

    def add_init_containers(self, containers):
        self.root.spec.template.spec.initContainers += [
            container.root for container in containers]

    def add_volumes(self, volumes):
        for key, value in volumes.items():
            merge({"name": key}, value)
            self.root.spec.template.spec.volumes += [value]

    def add_volume_claims(self, volume_claims):
        for key, value in volume_claims.items():
            merge({"metadata": {"name": key, "labels": {"name": key}}}, value)
            self.root.spec.volumeClaimTemplates += [value]

    def add_volumes_for_objects(self, objects):
        component = self.kwargs.component
        component_name = self.kwargs.name

        for object in objects.root:
            object_name = object.name
            rendered_name = object.root.metadata.name
        
            if type(object) == ConfigMap:
                key = "configMap"
                name_key = "name"
            else:
                key= "secret"
                name_key = "secretName"
            self.root.spec.template.spec.volumes += [{
                "name": object_name,
                key: {
                    "defaultMode": object.root.spec.get('default_mode', 420),
                    name_key: rendered_name,
                    "items": [{"key": value, "path": value} for value in object.items]
                }
            }]


class NetworkPolicy(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "networking.k8s.io/v1"
        self.kwargs.kind = "NetworkPolicy"
        super().new()
        self.need("config")
        self.need("workload")

    def body(self):
        super().body()
        policy = self.kwargs.config
        workload = self.kwargs.workload
        self.root.spec.podSelector.matchLabels = workload.metadata.labels
        self.root.spec.ingress = policy.ingress
        self.root.spec.egress = policy.egress
        if self.root.spec.ingress:
            self.root.spec.policyTypes += ["Ingress"]

        if self.root.spec.egress:
            self.root.spec.policyTypes += ["Egress"]


class ServiceAccount(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "v1"
        self.kwargs.kind = "ServiceAccount"
        super().new()
        self.need("component")

    def body(self):
        super().body()
        component = self.kwargs.component
        self.add_namespace(inv.parameters.namespace)
        self.add_annotations(component.service_account.annotations)
        if component.image_pull_secrets or inv.parameters.pull_secret.name:
            self.root.imagePullSecrets = [
                {"name": component.get('image_pull_secrets', inv.parameters.pull_secret.name)}]


class ConfigMap(k8s.Base):
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

        self.items = config["items"]
        if component.globals:
            self.add_labels(component.globals.config_maps.labels)
            self.add_annotations(component.globals.config_maps.annotations)

        if "data" in config:
            for key, config_spec in config.data.items():
                if "value" in config_spec:
                    self.root.data[key] = config_spec.get('value')
                if "template" in config_spec:
                    self.root.data[key] = j2(
                        config_spec.template, config_spec.get('values', {}))
                if "file" in config_spec:
                    with open(config_spec.file, 'r') as f:
                        self.root.data[key] = f.read()
        elif "directory" in config:
            for filename in os.listdir(config.directory):
                with open(f"{config.directory}/{filename}", "r") as f:
                    self.root.data[filename] = f.read()

        if config.get("versioned", False):
            self.hash = hashlib.sha256(str(self.to_dict()).encode()).hexdigest()[:8]
            self.root.metadata.name += f"-{self.hash}"

        


class Secret(k8s.Base):
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

        self.items = config["items"]

        if component.globals:
            self.add_labels(component.globals.secrets.labels)
            self.add_annotations(component.globals.secrets.annotations)

        if use_tesoro:
            data = self.root.stringData
        else:
            data = self.root.data

        for key, spec in config.data.items():
            if "value" in spec:
                if spec.get('b64_encode', False):
                    data[key] = Secret.encode_string(
                        spec.get('value'), use_tesoro)
                else:
                    data[key] = spec.get('value')
            if "template" in spec:
                data[key] = j2(spec.template, spec.get('values', {}))
                
        if config.get("versioned", False):          
            self.hash = hashlib.sha256(str(self.to_dict()).encode()).hexdigest()[:8]
            self.root.metadata.name += f"-{self.hash}"



class Service(k8s.Base):
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
        self.add_annotations(component.service.annotations)
        self.root.spec.selector = workload.spec.template.metadata.labels
        self.root.spec.type = component.service.type
        self.root.spec.sessionAffinity = component.service.get(
            "session_affinity", "None")
        all_ports = [component.ports] + [container.ports for container in component.additional_containers.values()
                                         if 'ports' in container]

        for port_name, port_spec in sorted(all_ports.pop().items()):
            if "service_port" in port_spec:
                self.root.spec.ports += [{
                    "name": port_name,
                    "port": port_spec.service_port,
                    "targetPort": port_name,
                    "protocol": port_spec.get("protocol", "TCP")
                }]


class NameSpace(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "v1"
        self.kwargs.kind = "Namespace"
        super().new()
        self.need("name")

    def body(self):
        super().body()
        name = self.kwargs.name
        labels = inv.parameters.generators.kubernetes.namespace.labels
        self.add_labels(labels)


class Deployment(k8s.Base, WorkloadCommon):
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
        self.root.spec.template.spec.restartPolicy = component.get(
            "restart_policy", "Always")
        self.root.spec.template.spec.hostNetwork = component.get(
            "host_network", "false")
        self.root.spec.strategy = component.get(
            "update_strategy", default_strategy)
        self.root.spec.revisionHistoryLimit = component.revision_history_limit
        self.root.spec.progressDeadlineSeconds = component.deployment_progress_deadline_seconds
        self.set_replicas(component.get('replicas', 1))


class StatefulSet(k8s.Base, WorkloadCommon):
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
        self.root.spec.template.spec.restartPolicy = component.get(
            "restart_policy", "Always")
        self.root.spec.template.spec.hostNetwork = component.get(
            "host_network", "false")
        self.root.spec.revisionHistoryLimit = component.revision_history_limit
        self.root.spec.strategy = component.get("strategy", default_strategy)
        self.root.spec.updateStrategy = component.get(
            "update_strategy", update_strategy)
        self.root.spec.serviceName = name
        self.set_replicas(component.get('replicas', 1))

class DaemonSet(k8s.Base, WorkloadCommon):
    def new(self):
        self.kwargs.apiVersion = "apps/v1"
        self.kwargs.kind = "DaemonSet"
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
        self.root.spec.template.spec.restartPolicy = component.get(
            "restart_policy", "Always")
        self.root.spec.template.spec.hostNetwork = component.get(
            "host_network", "false")
        self.root.spec.revisionHistoryLimit = component.revision_history_limit
        self.root.spec.progressDeadlineSeconds = component.deployment_progress_deadline_seconds

class Job(k8s.Base, WorkloadCommon):
    def new(self):
        self.kwargs.apiVersion = "batch/v1"
        self.kwargs.kind = "Job"
        super().new()
        self.need("component")

    def body(self):
        super().body()
        name = self.kwargs.name
        component = self.kwargs.component
        self.root.spec.template.metadata.labels = self.root.metadata.labels
        self.root.spec.template.spec.restartPolicy = component.get(
            "restart_policy", "Never")
        self.root.spec.backoffLimit = component.get("backoff_limit", 1)
        self.root.spec.completions = component.get("completions", 1)
        self.root.spec.parallelism = component.get("parallelism", 1)


class CronJob(k8s.Base, WorkloadCommon):
    def new(self):
        self.kwargs.apiVersion = "batch/v1beta1"
        self.kwargs.kind = "CronJob"
        super().new()
        self.need("component")
        self.need("job")

    def body(self):
        super().body()
        component = self.kwargs.component
        job = self.kwargs.job
        self.root.metadata = job.root.metadata
        self.root.spec.jobTemplate.spec = job.root.spec
        self.root.spec.schedule = component.schedule


class Container(BaseObj):
    def new(self):
        self.need("name")
        self.need("container")

    @staticmethod
    def find_key_in_config(key, configs):
        for name, config in configs.items():
            if key in config.data.keys():
                return name
        raise (BaseException(
            "Unable to find key {} in your configs definitions".format(key)))

    def process_envs(self, container):
        for name, value in sorted(container.env.items()):
            if isinstance(value, dict):
                if "fieldRef" in value:
                    self.root.env += [{"name": name, "valueFrom": value}]
                elif "secretKeyRef" in value:
                    if "name" not in value["secretKeyRef"]:
                        config_name = self.find_key_in_config(
                            value["secretKeyRef"]["key"], container.secrets)
                        # TODO(ademaria) I keep repeating this logic. Refactor.
                        if len(container.secrets.keys()) == 1:
                            value["secretKeyRef"]["name"] = self.kwargs.name
                        else:
                            value["secretKeyRef"]["name"] = "{}-{}".format(
                                self.kwargs.name, config_name)

                    self.root.env += [{"name": name, "valueFrom": value}]
                if "configMapKeyRef" in value:
                    if "name" not in value["configMapKeyRef"]:
                        config_name = self.find_key_in_config(
                            value["configMapKeyRef"]["key"], container.config_maps)
                        # TODO(ademaria) I keep repeating this logic. Refactor.
                        if len(container.config_maps.keys()) == 1:
                            value["configMapKeyRef"]["name"] = self.kwargs.name
                        else:
                            value["configMapKeyRef"]["name"] = "{}-{}".format(
                                self.kwargs.name, config_name)

                    self.root.env += [{"name": name, "valueFrom": value}]
            else:
                self.root.env += [{"name": name, "value": str(value)}]

    def add_volume_mounts_from_configs(self):
        name = self.kwargs.name
        container = self.kwargs.container
        configs = container.config_maps.items()
        secrets = container.secrets.items()
        for object_name, spec in configs:
            if spec == None:
                raise CompileError(
                    f"error with '{object_name}' for component {name}: configuration cannot be empty!")

            if "mount" in spec:
                self.root.volumeMounts += [{
                    "mountPath": spec.mount,
                    "readOnly": spec.readOnly,
                    "name": object_name,
                    "subPath": spec.subPath
                }]
        for object_name, spec in secrets:
            if spec == None:
                raise CompileError(
                    f"error with '{object_name}' for component {name}: configuration cannot be empty!")

            if "mount" in spec:
                self.root.volumeMounts += [{
                    "mountPath": spec.mount,
                    "readOnly": spec.readOnly,
                    "name": object_name,
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
            probe.root.initialDelaySeconds = probe_definition.get(
                'initial_delay_seconds', 0)
            probe.root.periodSeconds = probe_definition.get(
                'period_seconds', 10)
            probe.root.timeoutSeconds = probe_definition.get(
                'timeout_seconds', 5)
            probe.root.successThreshold = probe_definition.get(
                'success_threshold', 1)
            probe.root.failureThreshold = probe_definition.get(
                'failure_threshold', 3)

            if probe_definition.type == "http":
                probe.root.httpGet.scheme = probe_definition.get(
                    'scheme', "HTTP")
                probe.root.httpGet.port = probe_definition.get("port", 80)
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
        self.root.imagePullPolicy = container.get(
            'pull_policy', 'IfNotPresent')
        if container.lifecycle:
            self.root.lifecycle = container.lifecycle
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

        for name, port in sorted(container.ports.items()):
            self.root.ports += [{
                "containerPort": port.get('container_port', port.service_port),
                "name": name,
                "protocol": port.get("protocol", "TCP")
            }]

        self.root.livenessProbe = self.create_probe(
            container.healthcheck.liveness)
        self.root.readinessProbe = self.create_probe(
            container.healthcheck.readiness)
        self.process_envs(container)


class Workload(WorkloadCommon):
    def new(self):
        self.need("name")
        self.need("component")

    def body(self):
        component = self.kwargs.component
        name = self.kwargs.name
        if component.type == "deployment":
            workload = Deployment(name=name, component=self.kwargs.component)
        elif component.type == "statefulset":
            workload = StatefulSet(name=name, component=self.kwargs.component)
        elif component.type == "daemonset":
            workload = DaemonSet(name=name, component=self.kwargs.component)
        elif component.type == "job":
            workload = Job(name=name, component=self.kwargs.component)
        else:
            raise ()

        workload.add_namespace(inv.parameters.namespace)
        workload.add_annotations(component.get('annotations', {}))
        workload.root.spec.template.metadata.annotations = component.get(
            'pod_annotations', {})
        workload.add_labels(component.get('labels', {}))
        workload.add_volumes(component.volumes)
        workload.add_volume_claims(component.volume_claims)
        workload.root.spec.template.spec.securityContext = component.workload_security_context
        workload.root.spec.minReadySeconds = component.min_ready_seconds
        if component.service_account.enabled:
            workload.root.spec.template.spec.serviceAccountName = component.service_account.get(
                "name", name)

        container = Container(name=name, container=component)
        additional_containers = [Container(name=name, container=component) for name, component in
                                 component.additional_containers.items()]
        workload.add_containers([container])
        workload.add_containers(additional_containers)

        init_containers = [Container(name=name, container=component) for name, component in
                            component.init_containers.items()]

        workload.add_init_containers(init_containers)
        workload.root.spec.template.spec.imagePullSecrets = component.image_pull_secrets
        workload.root.spec.template.spec.dnsPolicy = component.dns_policy
        workload.root.spec.template.spec.terminationGracePeriodSeconds = component.get(
            "grace_period", 30)

        if component.prefer_pods_in_node_with_expression:
            workload.root.spec.template.spec.affinity.nodeAffinity.preferredDuringSchedulingIgnoredDuringExecution += [
                {
                    "preference":
                        {

                            "matchExpressions": [component.prefer_pods_in_node_with_expression]
                        }, "weight": 1
                }
            ]

        if component.prefer_pods_in_different_nodes:
            workload.root.spec.template.spec.affinity.podAntiAffinity.preferredDuringSchedulingIgnoredDuringExecution += [
                {
                    "podAffinityTerm": {
                        "labelSelector": {
                            "matchExpressions":
                                [{
                                    "key": "app",
                                    "operator": "In",
                                    "values": [name]
                                }]
                        },
                        "topologyKey": "kubernetes.io/hostname"
                    },
                    "weight": 1
                }]

        if component.prefer_pods_in_different_zones:
            workload.root.spec.template.spec.affinity.podAntiAffinity.preferredDuringSchedulingIgnoredDuringExecution += [
                {
                    "podAffinityTerm": {
                        "labelSelector": {
                            "matchExpressions":
                                [{
                                    "key": "app",
                                    "operator": "In",
                                    "values": [name]
                                }]
                        },
                        "topologyKey": "failure-domain.beta.kubernetes.io/zone"
                    },
                    "weight": 1
                }]

        self.root = workload.root


class GenerateMultipleObjectsForClass(BaseObj):
    """Helper to generate multiple classes

    As a convention for generators we have that if you define only one policy/config/secret configuration
    for your component, then the name of that resource will be the component {name} itself.

    However if there are multiple objects being defined, then we call them: {name}-{object_name}

    This class helps achieve that for policies/config/secrets to avoid duplication.
    """

    def new(self):
        self.need("name")
        self.need("component")
        self.need("objects")
        self.need("generating_class")
        self.need("workload")

    def body(self):
        objects = self.kwargs.objects
        name = self.kwargs.name
        component = self.kwargs.component
        generating_class = self.kwargs.generating_class
        workload = self.kwargs.workload

        for object_name, object_config in objects.items():
            if object_config == None:
                raise CompileError(
                    f"error with '{object_name}' for component {name}: configuration cannot be empty!")

            if len(objects.items()) == 1:
                rendered_name = f"{name}"
            else:
                rendered_name = f"{name}-{object_name}"

            self.root += [generating_class(name=object_name, rendered_name=rendered_name,
                                           config=object_config, component=component, workload=workload)]


class PrometheusRule(k8s.Base):
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
        self.root.spec.groups += [{"name": "tesoro.rules",
                                   "rules": component.prometheus_rules.rules}]


class BackendConfig(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "cloud.google.com/v1"
        self.kwargs.kind = "BackendConfig"
        super().new()
        self.need("component")

    def body(self):
        component_name = self.kwargs.name
        self.kwargs.name = f"{component_name}-backend-config"
        super().body()
        name = self.kwargs.name
        component = self.kwargs.component
        self.add_namespace(inv.parameters.namespace)
        self.root.spec = component.backend_config


class ServiceMonitor(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "monitoring.coreos.com/v1"
        self.kwargs.kind = "ServiceMonitor"
        super().new()
        self.need("component")
        self.need("workload")

    def body(self):
        # TODO(ademaria) This name mangling is here just to simplify diff.
        # Change it once done
        component_name = self.kwargs.name
        workload = self.kwargs.workload
        self.kwargs.name = "{}-metrics".format(component_name)

        super().body()
        name = self.kwargs.name
        component = self.kwargs.component
        self.add_namespace(inv.parameters.namespace)
        self.root.spec.endpoints = component.service_monitors.endpoints
        self.root.spec.jobLabel = name
        self.root.spec.namespaceSelector.matchNames = [
            inv.parameters.namespace]
        self.root.spec.selector.matchLabels = workload.spec.template.metadata.labels


class MutatingWebhookConfiguration(k8s.Base):
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


class ClusterRole(k8s.Base):
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


class ClusterRoleBinding(k8s.Base):
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


class PodDisruptionBudget(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "policy/v1beta1"
        self.kwargs.kind = "PodDisruptionBudget"
        super().new()
        self.need("component")
        self.need("workload")

    def body(self):
        super().body()
        component = self.kwargs.component
        workload = self.kwargs.workload
        self.add_namespace(inv.parameters.namespace)
        self.root.spec.minAvailable = component.pdb_min_available
        self.root.spec.selector.matchLabels = workload.spec.template.metadata.labels


class VerticalPodAutoscaler(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "autoscaling.k8s.io/v1beta2"
        self.kwargs.kind = "VerticalPodAutoscaler"
        super().new()
        self.need("component")
        self.need("workload")

    def body(self):
        super().body()
        component = self.kwargs.component
        workload = self.kwargs.workload
        self.add_namespace(inv.parameters.namespace)
        self.add_labels(workload.metadata.labels)
        self.root.spec.targetRef.apiVersion = workload.apiVersion
        self.root.spec.targetRef.kind = workload.kind
        self.root.spec.targetRef.name = workload.metadata.name
        self.root.spec.updatePolicy.updateMode = component.vpa

        # TODO(ademaria) Istio blacklist is always desirable but add way to make it configurable.
        self.root.spec.resourcePolicy.containerPolicies = [
            {"containerName": "istio-proxy", "mode": "Off"}]


def get_components():
    if 'components' in inv.parameters:
        generator_defaults = inv.parameters.generators.manifest.default_config

        for name, component in inv.parameters.components.items():
            if component.get("enabled", True):
                if "application" in component:
                    application_defaults = inv.parameters.applications.get(
                        component.application, {}).get(
                        'component_defaults', {})
                    merge(generator_defaults, application_defaults)
                    if component.get("type", "undefined") in component.globals:
                        merge(application_defaults,
                              component.globals.get(component.type, {}))
                    merge(application_defaults, component)

                merge(generator_defaults, component)
                component_type = component.get("type", generator_defaults.type)
                if component_type in inv.parameters.generators.manifest.resource_defaults:
                    component_defaults = inv.parameters.generators.manifest.resource_defaults[
                        component_type]
                    merge(component_defaults, component)

                component.name = name
                yield name, component


def generate_docs(input_params):
    obj = BaseObj()
    template = input_params.get("template_path", None)
    if template:
        for name, component in get_components():
            obj.root["{}-readme.md".format(name)] = j2(template,
                                                       {"service_component": component.to_dict(),
                                                        "inventory": inv.parameters.to_dict()})
    return obj


def generate_pre_deploy(input_params):
    obj = BaseObj()
    name = inv.parameters.namespace
    namespace = NameSpace(name=name)
    obj.root["{}-namespace".format(name)] = namespace

    return obj


def generate_manifests(input_params):
    obj = BaseObj()
    for name, component in get_components():
        bundle = []

        workload = Workload(name=name, component=component)

        if component.schedule:
            workload = CronJob(name=name, component=component, job=workload)

        workload_spec = workload.root

        bundle += [workload_spec]

        configs = GenerateMultipleObjectsForClass(
            name=name, component=component, generating_class=ConfigMap, objects=component.config_maps, workload=workload_spec)

        secrets = GenerateMultipleObjectsForClass(
            name=name, component=component, generating_class=Secret, objects=component.secrets, workload=workload_spec)

        workload.add_volumes_for_objects(configs)
        workload.add_volumes_for_objects(secrets)

        obj.root[f"{name}-config"] = configs.root
        obj.root[f"{name}-secret"] = secrets.root

        if component.vpa and component.type != "job":
            vpa = VerticalPodAutoscaler(
                name=name, component=component, workload=workload_spec).root
            bundle += [vpa]

        if component.pdb_min_available:
            pdb = PodDisruptionBudget(
                name=name, component=component, workload=workload_spec).root
            bundle += [pdb]

        if component.service:
            service = Service(name=name, component=component,
                              workload=workload_spec).root
            bundle += [service]

        if component.network_policies:

            policies = GenerateMultipleObjectsForClass(
                name=name, component=component, generating_class=NetworkPolicy, objects=component.network_policies, workload=workload_spec).root
            bundle += policies

        if component.webhooks:
            webhooks = MutatingWebhookConfiguration(
                name=name, component=component).root
            bundle += [webhooks]

        if component.service_monitors:
            service_monitor = ServiceMonitor(
                name=name, component=component, workload=workload_spec).root
            bundle += [service_monitor]

        if component.prometheus_rules:
            prometheus_rule = PrometheusRule(
                name=name, component=component).root
            bundle += [prometheus_rule]

        if component.cluster_role:
            cluster_role = ClusterRole(name=name, component=component).root
            bundle += [cluster_role]
            cluster_role_binding = ClusterRoleBinding(
                name=name, component=component).root
            bundle += [cluster_role_binding]

        if component.backend_config:
            backend_config = BackendConfig(name=name, component=component).root
            bundle += [backend_config]

        obj.root["{}-bundle".format(name)] = bundle

        if component.service_account.get('create', False):
            sa_name = component.service_account.get('name', name)
            sa = ServiceAccount(name=sa_name, component=component).root
            obj.root["{}-sa".format(name)] = sa
    return obj


def main(input_params):
    whitelisted_functions = ["generate_manifests",
                             "generate_docs", "generate_pre_deploy"]
    function = input_params.get("function", "generate_manifests")
    if function in whitelisted_functions:
        return globals()[function](input_params)
