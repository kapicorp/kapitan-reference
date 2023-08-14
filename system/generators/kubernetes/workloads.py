import logging

logger = logging.getLogger(__name__)

from typing import Any

from kapitan.inputs.kadet import BaseModel, BaseObj, CompileError

from .autoscaling import (
    HorizontalPodAutoscaler,
    KedaScaledObject,
    PodDisruptionBudget,
    VerticalPodAutoscaler,
)
from .base import MutatingWebhookConfiguration
from .common import KubernetesResource, kgenlib
from .networking import HealthCheckPolicy, NetworkPolicy, Service
from .prometheus import PrometheusRule, ServiceMonitor
from .rbac import ClusterRole, ClusterRoleBinding, Role, RoleBinding, ServiceAccount
from .storage import ComponentConfig, ComponentSecret


class GenerateMultipleObjectsForClass(kgenlib.BaseStore):
    """Helper to generate multiple classes

    As a convention for generators we have that if you define only one policy/config/secret configuration
    for your component, then the name of that resource will be the component {name} itself.

    However if there are multiple objects being defined, then we call them: {name}-{object_name}

    This class helps achieve that for policies/config/secrets to avoid duplication.
    """

    component_config: dict
    generating_class: Any
    workload: Any

    def body(self):
        component_config = self.component_config
        name = self.name
        objects_configs = self.config
        generating_class = self.generating_class
        workload = self.workload

        for object_name, object_config in objects_configs.items():
            if object_config == None:
                raise CompileError(
                    f"error with '{object_name}' for component {name}: configuration cannot be empty!"
                )

            if len(objects_configs.items()) == 1:
                name = f"{self.name}"
            else:
                name = f"{self.name}-{object_name}"

            generated_object = generating_class(
                name=name,
                object_name=object_name,
                config=object_config,
                component=component_config,
                workload=workload,
            )

            self.add(generated_object)


class Workload(KubernetesResource):
    @classmethod
    def create_workflow(cls, name, config):
        config = config
        name = name
        if config.type == "deployment":
            workload = Deployment(name=name, config=config)
        elif config.type == "statefulset":
            workload = StatefulSet(name=name, config=config)
        elif config.type == "daemonset":
            workload = DaemonSet(name=name, config=config)
        elif config.type == "job":
            workload = Job(name=name, config=config)
        else:
            raise ()

        workload.add_annotations(config.setdefault("annotations", {}))
        workload.root.spec.template.metadata.annotations = config.get(
            "pod_annotations", {}
        )
        workload.add_labels(config.setdefault("labels", {}))
        workload.add_volumes(config.setdefault("volumes", {}))
        workload.add_volume_claims(config.setdefault("volume_claims", {}))
        workload.root.spec.template.spec.securityContext = (
            config.workload_security_context
        )
        workload.root.spec.minReadySeconds = config.min_ready_seconds
        if config.service_account.enabled:
            workload.root.spec.template.spec.serviceAccountName = (
                config.service_account.get("name", name)
            )

        container = Container(name=name, config=config)
        additional_containers = [
            Container(name=name, config=config)
            for name, config in config.additional_containers.items()
        ]
        workload.add_containers([container])
        workload.add_containers(additional_containers)
        init_containers = [
            Container(name=name, config=config)
            for name, config in config.init_containers.items()
        ]

        workload.add_init_containers(init_containers)
        if config.image_pull_secrets:
            workload.root.spec.template.spec.imagePullSecrets = config.get(
                "image_pull_secrets"
            )
        workload.root.spec.template.spec.dnsPolicy = config.dns_policy
        workload.root.spec.template.spec.terminationGracePeriodSeconds = config.get(
            "grace_period", 30
        )

        if config.node_selector:
            workload.root.spec.template.spec.nodeSelector = config.node_selector

        if config.tolerations:
            workload.root.spec.template.spec.tolerations = config.tolerations

        affinity = workload.root.spec.template.spec.affinity
        if config.prefer_pods_in_node_with_expression and not config.node_selector:
            affinity.nodeAffinity.setdefault(
                "preferredDuringSchedulingIgnoredDuringExecutio", []
            )
            affinity.nodeAffinity.preferredDuringSchedulingIgnoredDuringExecution.append(
                {
                    "preference": {
                        "matchExpressions": [config.prefer_pods_in_node_with_expression]
                    },
                    "weight": 1,
                }
            )

        if config.prefer_pods_in_different_nodes:
            affinity.podAntiAffinity.setdefault(
                "preferredDuringSchedulingIgnoredDuringExecution", []
            )
            affinity.podAntiAffinity.preferredDuringSchedulingIgnoredDuringExecution.append(
                {
                    "podAffinityTerm": {
                        "labelSelector": {
                            "matchExpressions": [
                                {"key": "app", "operator": "In", "values": [name]}
                            ]
                        },
                        "topologyKey": "kubernetes.io/hostname",
                    },
                    "weight": 1,
                }
            )

        if config.prefer_pods_in_different_zones:
            affinity.podAntiAffinity.setdefault(
                "preferredDuringSchedulingIgnoredDuringExecution", []
            )
            affinity.podAntiAffinity.preferredDuringSchedulingIgnoredDuringExecution.append(
                {
                    "podAffinityTerm": {
                        "labelSelector": {
                            "matchExpressions": [
                                {"key": "app", "operator": "In", "values": [name]}
                            ]
                        },
                        "topologyKey": "failure-domain.beta.kubernetes.io/zone",
                    },
                    "weight": 1,
                }
            )

        return workload

    def set_replicas(self, replicas):
        self.root.spec.replicas = replicas

    def add_containers(self, containers):
        self.root.spec.template.spec.setdefault("containers", []).extend(
            [container.root for container in containers]
        )

    def add_init_containers(self, containers):
        self.root.spec.template.spec.setdefault("initContainers", []).extend(
            container.root for container in containers
        )

    def add_volumes(self, volumes):
        for key, value in volumes.items():
            kgenlib.merge({"name": key}, value)
            self.root.spec.template.spec.setdefault("volumes", []).append(value)

    def add_volume_claims(self, volume_claims):
        self.root.spec.setdefault("volumeClaimTemplates", [])
        for key, value in volume_claims.items():
            kgenlib.merge({"metadata": {"name": key, "labels": {"name": key}}}, value)
            self.root.spec.volumeClaimTemplates += [value]

    def add_volumes_for_object(self, object):
        object_name = object.object_name
        rendered_name = object.rendered_name

        if type(object) == ComponentConfig:
            key = "configMap"
            name_key = "name"
        else:
            key = "secret"
            name_key = "secretName"

        template = self.root.spec.template
        if isinstance(self, CronJob):
            template = self.root.spec.jobTemplate.spec.template

        template.spec.setdefault("volumes", []).append(
            {
                "name": object_name,
                key: {
                    "defaultMode": object.config.get("default_mode", 420),
                    name_key: rendered_name,
                    "items": [
                        {"key": value, "path": value}
                        for value in object.config.get("items", [])
                    ],
                },
            }
        )


class Deployment(Workload):
    kind = "Deployment"
    api_version = "apps/v1"

    def body(self):
        default_strategy = {
            "type": "RollingUpdate",
            "rollingUpdate": {"maxSurge": "25%", "maxUnavailable": "25%"},
        }
        super().body()
        config = self.config
        self.root.spec.template.metadata.setdefault("labels", {}).update(
            config.labels + self.root.metadata.labels
        )
        self.root.spec.selector.setdefault("matchLabels", {}).update(
            config.labels + self.root.metadata.labels
        )
        self.root.spec.template.spec.restartPolicy = config.get(
            "restart_policy", "Always"
        )
        if "host_network" in config:
            self.root.spec.template.spec.hostNetwork = config.host_network
        if "host_pid" in config:
            self.root.spec.template.spec.hostPID = config.host_pid
        self.root.spec.strategy = config.get("update_strategy", default_strategy)
        self.root.spec.revisionHistoryLimit = config.revision_history_limit
        self.root.spec.progressDeadlineSeconds = (
            config.deployment_progress_deadline_seconds
        )
        self.set_replicas(config.get("replicas", 1))


class StatefulSet(Workload):
    kind = "StatefulSet"
    api_version = "apps/v1"

    def body(self):
        default_strategy = {}
        update_strategy = {"rollingUpdate": {"partition": 0}, "type": "RollingUpdate"}

        super().body()
        name = self.name
        config = self.config
        self.root.spec.template.metadata.setdefault("labels", {}).update(
            config.labels + self.root.metadata.labels
        )
        self.root.spec.selector.setdefault("matchLabels", {}).update(
            config.labels + self.root.metadata.labels
        )
        self.root.spec.template.spec.restartPolicy = config.get(
            "restart_policy", "Always"
        )
        if "host_network" in config:
            self.root.spec.template.spec.hostNetwork = config.host_network
        if "host_pid" in config:
            self.root.spec.template.spec.hostPID = config.host_pid
        self.root.spec.revisionHistoryLimit = config.revision_history_limit
        self.root.spec.strategy = config.get("strategy", default_strategy)
        self.root.spec.updateStrategy = config.get("update_strategy", update_strategy)
        self.root.spec.serviceName = config.service.get("service_name", name)
        self.set_replicas(config.get("replicas", 1))


class DaemonSet(Workload):
    kind = "DaemonSet"
    api_version = "apps/v1"

    def body(self):
        super().body()
        config = self.config
        self.root.spec.template.metadata.setdefault("labels", {}).update(
            config.labels + self.root.metadata.labels
        )
        self.root.spec.selector.setdefault("matchLabels", {}).update(
            config.labels + self.root.metadata.labels
        )
        self.root.spec.template.spec.restartPolicy = config.get(
            "restart_policy", "Always"
        )
        if "host_network" in config:
            self.root.spec.template.spec.hostNetwork = config.host_network
        if "host_pid" in config:
            self.root.spec.template.spec.hostPID = config.host_pid
        self.root.spec.revisionHistoryLimit = config.revision_history_limit
        self.root.spec.progressDeadlineSeconds = (
            config.deployment_progress_deadline_seconds
        )


class Job(Workload):
    kind = "Job"
    api_version = "batch/v1"

    def body(self):
        super().body()
        config = self.config
        self.root.spec.template.metadata.setdefault("labels", {}).update(
            config.labels + self.root.metadata.labels
        )
        self.root.spec.template.spec.restartPolicy = config.get(
            "restart_policy", "Never"
        )
        if "host_network" in config:
            self.root.spec.template.spec.hostNetwork = config.host_network
        if "host_pid" in config:
            self.root.spec.template.spec.hostPID = config.host_pid
        self.root.spec.backoffLimit = config.get("backoff_limit", 1)
        self.root.spec.completions = config.get("completions", 1)
        self.root.spec.parallelism = config.get("parallelism", 1)


class CronJob(Workload):
    kind = "CronJob"
    api_version = "batch/v1"
    job: Job

    def body(self):
        super().body()
        config = self.config
        job = self.job
        self.root.metadata = job.root.metadata
        self.root.spec.jobTemplate.spec = job.root.spec
        self.root.spec.schedule = config.schedule


class Container(BaseModel):
    def new(self):
        name: str
        config: dict

    @staticmethod
    def find_key_in_config(key, configs):
        for name, config in configs.items():
            if key in config.data.keys():
                return name
        raise (
            BaseException(
                "Unable to find key {} in your configs definitions".format(key)
            )
        )

    def process_envs(self, config):
        name = self.name

        for env_name, value in sorted(config.env.items()):
            if isinstance(value, dict):
                if "fieldRef" in value:
                    self.root.setdefault("env", []).append(
                        {"name": env_name, "valueFrom": value}
                    )
                elif "secretKeyRef" in value:
                    if "name" not in value["secretKeyRef"]:
                        config_name = self.find_key_in_config(
                            value["secretKeyRef"]["key"], config.secrets
                        )
                        # TODO(ademaria) I keep repeating this logic. Refactor.
                        if len(config.secrets.keys()) == 1:
                            value["secretKeyRef"]["name"] = name
                        else:
                            value["secretKeyRef"]["name"] = "{}-{}".format(
                                name, config_name
                            )

                    self.root.setdefault("env", []).append(
                        {"name": env_name, "valueFrom": value}
                    )
                if "configMapKeyRef" in value:
                    if "name" not in value["configMapKeyRef"]:
                        config_name = self.find_key_in_config(
                            value["configMapKeyRef"]["key"], config.config_maps
                        )
                        # TODO(ademaria) I keep repeating this logic. Refactor.
                        if len(config.config_maps.keys()) == 1:
                            value["configMapKeyRef"]["name"] = name
                        else:
                            value["configMapKeyRef"]["name"] = "{}-{}".format(
                                name, config_name
                            )

                    self.root.setdefault("env", []).append(
                        {"name": env_name, "valueFrom": value}
                    )
            else:
                self.root.setdefault("env", []).append(
                    {"name": env_name, "value": str(value)}
                )

    def add_volume_mounts_from_configs(self):
        name = self.name
        config = self.config
        configs = config.config_maps.items()
        secrets = config.secrets.items()
        for object_name, spec in configs:
            if spec is None:
                raise CompileError(
                    f"error with '{object_name}' for component {name}: configuration cannot be empty!"
                )

            if "mount" in spec:
                self.root.setdefault("volumeMounts", [])
                self.root.volumeMounts += [
                    {
                        "mountPath": spec.mount,
                        "readOnly": spec.get("readOnly", None),
                        "name": object_name,
                        "subPath": spec.subPath,
                    }
                ]
        for object_name, spec in secrets:
            if spec is None:
                raise CompileError(
                    f"error with '{object_name}' for component {name}: configuration cannot be empty!"
                )

            if "mount" in spec:
                self.root.setdefault("volumeMounts", []).append(
                    {
                        "mountPath": spec.mount,
                        "readOnly": spec.get("readOnly", None),
                        "name": object_name,
                        "subPath": spec.subPath,
                    }
                )

    def add_volume_mounts(self, volume_mounts):
        for key, value in volume_mounts.items():
            kgenlib.merge({"name": key}, value)
            self.root.setdefault("volumeMounts", []).append(value)

    @staticmethod
    def create_probe(probe_definition):
        probe = BaseObj()
        if "type" in probe_definition:
            probe.root.initialDelaySeconds = probe_definition.get(
                "initial_delay_seconds", 0
            )
            probe.root.periodSeconds = probe_definition.get("period_seconds", 10)
            probe.root.timeoutSeconds = probe_definition.get("timeout_seconds", 5)
            probe.root.successThreshold = probe_definition.get("success_threshold", 1)
            probe.root.failureThreshold = probe_definition.get("failure_threshold", 3)

            if probe_definition.type == "http":
                probe.root.httpGet.scheme = probe_definition.get("scheme", "HTTP")
                probe.root.httpGet.port = probe_definition.get("port", 80)
                probe.root.httpGet.path = probe_definition.path
                probe.root.httpGet.httpHeaders = probe_definition.httpHeaders
            if probe_definition.type == "tcp":
                probe.root.tcpSocket.port = probe_definition.port
            if probe_definition.type == "command":
                probe.root.exec.command = probe_definition.command
        return probe.root

    def body(self):
        name = self.name
        config = self.config

        self.root.name = name
        self.root.image = config.image
        self.root.imagePullPolicy = config.get("pull_policy", "IfNotPresent")
        if config.lifecycle:
            self.root.lifecycle = config.lifecycle
        self.root.resources = config.resources
        self.root.args = config.args
        self.root.command = config.command
        # legacy container.security
        if config.security:
            self.root.securityContext.allowPrivilegeEscalation = (
                config.security.allow_privilege_escalation
            )
            self.root.securityContext.runAsUser = config.security.user_id
        else:
            self.root.securityContext = config.security_context
        self.add_volume_mounts_from_configs()
        self.add_volume_mounts(config.volume_mounts)

        for name, port in sorted(config.ports.items()):
            self.root.setdefault("ports", [])
            self.root.ports.append(
                {
                    "containerPort": port.get("container_port", port.service_port),
                    "name": name,
                    "protocol": port.get("protocol", "TCP"),
                }
            )

        self.root.startupProbe = self.create_probe(config.healthcheck.startup)
        self.root.livenessProbe = self.create_probe(config.healthcheck.liveness)
        self.root.readinessProbe = self.create_probe(config.healthcheck.readiness)
        self.process_envs(config)


class PodSecurityPolicy(KubernetesResource):
    kind = "PodSecurityPolicy"
    api_version = "policy/v1beta1"
    workload: Workload

    def new(self):
        super().new()

    def body(self):
        super().body()
        config = self.config
        self.root.spec = config.pod_security_policy.spec
        # Merge Dicts into PSP Annotations
        self.root.metadata.annotations = {
            **config.get("annotations", {}),
            **config.pod_security_policy.get("annotations", {}),
        }
        # Merge Dicts into PSP Labels
        self.root.metadata.labels = {
            **config.get("labels", {}),
            **config.pod_security_policy.get("labels", {}),
        }


@kgenlib.register_generator(
    path="components",
    apply_patches=[
        "generators.manifest.default_config",
        "applications.{application}.component_defaults",
    ],
)
class Components(kgenlib.BaseStore):
    def body(self):
        name = self.name
        config = self.config
        workload = Workload.create_workflow(name=name, config=config)

        logging.debug(f"Generating component {name} from {config}")
        if config.schedule:
            workload = CronJob(name=name, config=config, job=workload)

        workload.add_label("app.kapicorp.dev/component", name)

        configs = GenerateMultipleObjectsForClass(
            name=name,
            component_config=config,
            generating_class=ComponentConfig,
            config=config.config_maps,
            workload=workload,
        )

        map(lambda x: x.add_label("app.kapicorp.dev/component", name), configs)

        secrets = GenerateMultipleObjectsForClass(
            name=name,
            component_config=config,
            generating_class=ComponentSecret,
            config=config.secrets,
            workload=workload,
        )

        map(lambda x: x.add_label("app.kapicorp.dev/component", name), secrets)

        self.add(workload)
        self.add(configs)
        self.add(secrets)

        if config.pdb_min_available:
            pdb = PodDisruptionBudget(name=name, config=config, workload=workload)
            pdb.add_label("app.kapicorp.dev/component", name)
            self.add(pdb)

        if config.hpa:
            hpa = HorizontalPodAutoscaler(name=name, config=config, workload=workload)
            hpa.add_label("app.kapicorp.dev/component", name)
            self.add(hpa)

        if config.get("vpa", False):
            vpa = VerticalPodAutoscaler(name=name, config=config, workload=workload)
            vpa.add_label("app.kapicorp.dev/component", name)
            self.add(vpa)

        if config.keda_scaled_object:
            scaled_object = KedaScaledObject(
                name=name, config=config, workload=workload
            )
            scaled_object.add_label("app.kapicorp.dev/component", name)
            self.add(scaled_object)

        if config.type != "job":
            if config.pdb_min_available or config.auto_pdb:
                pdb = PodDisruptionBudget(name=name, config=config, workload=workload)
                pdb.add_label("app.kapicorp.dev/component", name)
                self.add(pdb)

        if config.istio_policy:
            istio_policy = IstioPolicy(name=name, config=config, workload=workload)
            istio_policy.add_label("app.kapicorp.dev/component", name)
            self.add(istio_policy)

        if config.pod_security_policy:
            psp = PodSecurityPolicy(name=name, config=config, workload=workload)
            psp.add_label("app.kapicorp.dev/component", name)
            self.add(psp)

        if config.service:
            service = Service(
                name=name,
                config=config,
                workload=workload,
                service_spec=config.service,
            )
            service.add_label("app.kapicorp.dev/component", name)

            self.add(service)

        if config.additional_services:
            for service_name, service_spec in config.additional_services.items():
                service = Service(
                    name=service_name,
                    config=config,
                    workload=workload,
                    service_spec=service_spec,
                )
                service.add_label("app.kapicorp.dev/component", name)
                self.add(service)

        if config.network_policies:
            policies = GenerateMultipleObjectsForClass(
                name=name,
                component_config=config,
                generating_class=NetworkPolicy,
                config=config.network_policies,
                workload=workload,
            )
            map(lambda x: x.add_label("app.kapicorp.dev/component", name), policies)
            self.add(policies)

        if config.webhooks:
            webhooks = MutatingWebhookConfiguration(name=name, config=config)
            webhooks.add_label("app.kapicorp.dev/component", name)
            self.add(webhooks)

        if config.service_monitors:
            service_monitor = ServiceMonitor(
                name=name, config=config, workload=workload
            )
            service_monitor.add_label("app.kapicorp.dev/component", name)
            self.add(service_monitor)

        if config.prometheus_rules:
            prometheus_rule = PrometheusRule(name=name, config=config)
            prometheus_rule.add_label("app.kapicorp.dev/component", name)
            self.add(prometheus_rule)

        if config.service_account.get("create", False):
            sa_name = config.service_account.get("name", name)
            sa = ServiceAccount(name=sa_name, config=config)
            sa.add_label("app.kapicorp.dev/component", name)
            self.add(sa)

        if config.role:
            role = Role(name=name, config=config)
            role.add_label("app.kapicorp.dev/component", name)
            self.add(role)
            role_binding = RoleBinding(name=name, config=config, sa=sa)
            role_binding.add_label("app.kapicorp.dev/component", name)
            self.add(role_binding)

        if config.cluster_role:
            cluster_role = ClusterRole(name=name, config=config)
            self.add(cluster_role)
            cluster_role.add_label("app.kapicorp.dev/component", name)
            cluster_role_binding = ClusterRoleBinding(name=name, config=config, sa=sa)
            cluster_role_binding.add_label("app.kapicorp.dev/component", name)
            self.add(cluster_role_binding)

        if config.backend_config:
            backend_config = BackendConfig(name=name, config=config)
            backend_config.add_label("app.kapicorp.dev/component", name)
            self.add(backend_config)
