from kapitan.inputs.kadet import BaseObj, inventory

from .k8s import j2, merge, NetworkPolicy, ServiceAccount, ConfigMap, Secret, Service, Deployment, StatefulSet, \
    Container, PrometheusRule, ServiceMonitor, MutatingWebhookConfiguration, ClusterRole, ClusterRoleBinding

inv = inventory()


class Workload(BaseObj):
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
        else:
            raise ()

        workload.add_namespace(inv.parameters.namespace)
        workload.set_replicas(component.get('replicas', 1))
        workload.add_annotations(component.get('annotations', {}))
        workload.add_labels(component.get('labels', {}))
        workload.add_volumes(component.volumes)
        workload.add_volume_claims(component.volume_claims)
        workload.root.spec.template.spec.securityContext = component.workload_security_context
        workload.root.spec.minReadySeconds = component.min_ready_seconds
        workload.root.spec.progressDeadlineSeconds = component.deployment_progress_deadline_seconds
        if component.service_account.enabled:
            workload.root.spec.template.spec.serviceAccountName = component.service_account.get("name", name)

        container = Container(name=name, container=component)
        additional_containers = [Container(name=name, container=component) for name, component in
                                 component.additional_containers.items()]
        workload.add_containers([container])
        workload.add_containers(additional_containers)
        workload.add_volumes_from_config()

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


class GeneratePolicies(BaseObj):
    def new(self):
        self.need("name")
        self.need("component")

    def body(self):
        component = self.kwargs.component
        name = self.kwargs.name

        if len(component.network_policies.items()) == 1:
            self.root = [NetworkPolicy(name=name, policy=policy) for policy_name, policy in
                         component.network_policies.items()]
        else:
            self.root = [NetworkPolicy(name=policy_name, policy=policy) for policy_name, policy in
                         component.network_policies.items()]


class GenerateConfigMaps(BaseObj):
    def new(self):
        self.need("name")
        self.need("component")

    def body(self):
        component = self.kwargs.component
        name = self.kwargs.name

        if len(component.config_maps.items()) == 1:
            self.root = [ConfigMap(name=name, config=config, component=component) for config_name, config in
                         component.config_maps.items()]
        else:
            self.root = [ConfigMap(name="{}-{}".format(name, config_name), config=config, component=component) for
                         config_name, config in
                         component.config_maps.items()]


class GenerateSecrets(BaseObj):
    def new(self):
        self.need("name")
        self.need("component")

    def body(self):
        component = self.kwargs.component
        name = self.kwargs.name

        if len(component.secrets.items()) == 1:
            self.root = [Secret(name=name, config=config, component=component) for secret_name, config in
                         component.secrets.items()]
        else:
            self.root = [Secret(name="{}-{}".format(name, secret_name), config=config, component=component) for
                         secret_name, config in
                         component.secrets.items()]


def get_components():
    if 'components' in inv.parameters:
        generator_defaults = inv.parameters.generators.manifest.default_config

        for name, component in inv.parameters.components.items():
            if "application" in component:
                application_defaults = inv.parameters.applications.get(
                    component.application, {}).get(
                    'component_defaults', {})
                merge(generator_defaults, application_defaults)
                merge(application_defaults, component)

            merge(generator_defaults, component)
            component.name = name
            yield name, component


def generate_docs():
    obj = BaseObj()
    for name, component in get_components():
        obj.root["{}-readme.md".format(name)] = j2('templates/docs/service_component.md.j2',
                                                   {"service_component": component.to_dict(), "inventory": inv.parameters.to_dict()})
    return obj


def generate_manifests():
    obj = BaseObj()
    for name, component in get_components():

        config_maps = GenerateConfigMaps(name=name, component=component).root
        secrets = GenerateSecrets(name=name, component=component).root
        obj.root["{}-config".format(name)] = config_maps
        obj.root["{}-secret".format(name)] = secrets

        bundle = []
        workload = Workload(name=name, component=component).root

        bundle += [workload]
        if component.service:
            service = Service(name=name, component=component, workload=workload).root
            bundle += [service]

        if component.network_policies:
            policies = GeneratePolicies(name=name, component=component).root
            bundle += policies

        if component.webhooks:
            webhooks = MutatingWebhookConfiguration(name=name, component=component).root
            bundle += [webhooks]

        if component.service_monitors:
            service_monitor = ServiceMonitor(name=name, component=component).root
            bundle += [service_monitor]

        if component.prometheus_rules:
            prometheus_rule = PrometheusRule(name=name, component=component).root
            bundle += [prometheus_rule]

        if component.cluster_role:
            cluster_role = ClusterRole(name=name, component=component).root
            bundle += [cluster_role]
            cluster_role_binding = ClusterRoleBinding(name=name, component=component).root
            bundle += [cluster_role_binding]

        obj.root["{}-bundle".format(name)] = bundle

        if component.service_account.get('enabled', False):
            sa = ServiceAccount(name=name).root
            obj.root["{}-sa".format(name)] = sa
    return obj


def main(input_params):
    whitelisted_functions = ["generate_manifests", "generate_docs"]
    function = input_params.get("function", "generate_manifests")
    if function in whitelisted_functions:
        return globals()[function]()
