import base64
import hashlib
import os

from kapitan.cached import args
from kapitan.inputs.kadet import BaseObj, inventory
from kapitan.utils import render_jinja2_file

search_paths = args.get("search_paths")

from . import k8s


def j2(filename, ctx):
    return render_jinja2_file(filename, ctx, search_paths=search_paths)


inv = inventory(lazy=True)


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


class RabbitmqCluster(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "rabbitmq.com/v1beta1"
        self.kwargs.kind = "RabbitmqCluster"

        self.kwargs.finalizers = list(
            "deletion.finalizers.rabbitmqclusters.rabbitmq.com"
        )
        super().new()
        self.need("name")

    def body(self):
        super().body()

        self.add_namespace(inv.parameters.rabbitmq_namespace)

        rabbitmqcluster = self.kwargs.rabbitmqcluster
        self.add_annotations(rabbitmqcluster.get("annotations", {}))
        self.add_labels(rabbitmqcluster.get("labels", {}))

        if rabbitmqcluster.replicas:
            self.root.spec.replicas = rabbitmqcluster.replicas

        if rabbitmqcluster.image:
            self.root.spec.image = rabbitmqcluster.image

        if rabbitmqcluster.imagePullSecrets:
            self.root.spec.imagePullSecrets = rabbitmqcluster.imagePullSecrets

        if rabbitmqcluster.service:
            self.root.spec.service = rabbitmqcluster.service

        if rabbitmqcluster.persistence:
            self.root.spec.persistence = rabbitmqcluster.persistence

        if rabbitmqcluster.resources:
            self.root.spec.resources = rabbitmqcluster.resources

        if rabbitmqcluster.affinity:
            self.root.spec.resources = rabbitmqcluster.affinity

        if rabbitmqcluster.tolerations:
            self.root.spec.tolerations = rabbitmqcluster.tolerations

        if rabbitmqcluster.rabbitmq:
            self.root.spec.rabbitmq = rabbitmqcluster.rabbitmq

        if rabbitmqcluster.tls:
            self.root.spec.tls = rabbitmqcluster.tls

        if rabbitmqcluster.skipPostDeploySteps:
            self.root.spec.skipPostDeploySteps = rabbitmqcluster.skipPostDeploySteps

        if rabbitmqcluster.terminationGracePeriodSeconds:
            self.root.spec.terminationGracePeriodSeconds = (
                rabbitmqcluster.terminationGracePeriodSeconds
            )

        if rabbitmqcluster.secretBackend:
            self.root.spec.secretBackend = rabbitmqcluster.secretBackend

        if rabbitmqcluster.override:
            self.root.spec.override = rabbitmqcluster.override


class RabbitmqQueue(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "rabbitmq.com/v1beta1"
        self.kwargs.kind = "Queue"

        self.kwargs.finalizers = list(
            "deletion.finalizers.rabbitmqclusters.rabbitmq.com"
        )
        super().new()
        self.need("name")

    def body(self):
        super().body()

        self.add_namespace(inv.parameters.rabbitmq_namespace)

        rabbitmq_queue = self.kwargs.rabbitmq_queue
        self.add_annotations(rabbitmq_queue.get("annotations", {}))
        self.add_labels(rabbitmq_queue.get("labels", {}))

        if rabbitmq_queue.name:
            self.root.spec.name = rabbitmq_queue.name

        if type(rabbitmq_queue.autoDelete) is bool:
            self.root.spec.autoDelete = rabbitmq_queue.autoDelete

        if type(rabbitmq_queue.durable) is bool:
            self.root.spec.durable = rabbitmq_queue.durable

        if rabbitmq_queue.rabbitmqClusterReference:
            self.root.spec.rabbitmqClusterReference = (
                rabbitmq_queue.rabbitmqClusterReference
            )

        if rabbitmq_queue.arguments:
            self.root.spec.arguments = rabbitmq_queue.arguments


class RabbitmqPolicy(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "rabbitmq.com/v1beta1"
        self.kwargs.kind = "Policy"

        self.kwargs.finalizers = list(
            "deletion.finalizers.rabbitmqclusters.rabbitmq.com"
        )
        super().new()
        self.need("name")

    def body(self):
        super().body()

        self.add_namespace(inv.parameters.rabbitmq_namespace)

        rabbitmq_policy = self.kwargs.rabbitmq_policy
        self.add_annotations(rabbitmq_policy.get("annotations", {}))
        self.add_labels(rabbitmq_policy.get("labels", {}))

        if rabbitmq_policy.name:
            self.root.spec.name = rabbitmq_policy.name

        if rabbitmq_policy.pattern:
            self.root.spec.pattern = rabbitmq_policy.pattern

        if rabbitmq_policy.applyTo:
            self.root.spec.applyTo = rabbitmq_policy.applyTo

        if rabbitmq_policy.definition:
            self.root.spec.definition = rabbitmq_policy.definition

        if rabbitmq_policy.rabbitmqClusterReference:
            self.root.spec.rabbitmqClusterReference = (
                rabbitmq_policy.rabbitmqClusterReference
            )

        if rabbitmq_policy.priority:
            self.root.spec.priority = rabbitmq_policy.priority

        if rabbitmq_policy.vhost:
            self.root.spec.vhost = rabbitmq_policy.vhost


class RabbitmqExchange(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "rabbitmq.com/v1beta1"
        self.kwargs.kind = "Exchange"

        self.kwargs.finalizers = list(
            "deletion.finalizers.rabbitmqclusters.rabbitmq.com"
        )
        super().new()
        self.need("name")

    def body(self):
        super().body()

        self.add_namespace(inv.parameters.rabbitmq_namespace)

        rabbitmq_exchange = self.kwargs.rabbitmq_exchange
        self.add_annotations(rabbitmq_exchange.get("annotations", {}))
        self.add_labels(rabbitmq_exchange.get("labels", {}))

        if rabbitmq_exchange.name:
            self.root.spec.name = rabbitmq_exchange.name

        if rabbitmq_exchange.type:
            self.root.spec.type = rabbitmq_exchange.type

        if type(rabbitmq_exchange.autoDelete) is bool:
            self.root.spec.autoDelete = rabbitmq_exchange.autoDelete

        if type(rabbitmq_exchange.durable) is bool:
            self.root.spec.durable = rabbitmq_exchange.durable

        if rabbitmq_exchange.rabbitmqClusterReference:
            self.root.spec.rabbitmqClusterReference = (
                rabbitmq_exchange.rabbitmqClusterReference
            )

        if rabbitmq_exchange.arguments:
            self.root.spec.arguments = rabbitmq_exchange.arguments

        if rabbitmq_exchange.vhost:
            self.root.spec.vhost = rabbitmq_exchange.vhost


class RabbitmqBinding(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "rabbitmq.com/v1beta1"
        self.kwargs.kind = "Binding"

        self.kwargs.finalizers = list(
            "deletion.finalizers.rabbitmqclusters.rabbitmq.com"
        )
        super().new()
        self.need("name")

    def body(self):
        super().body()

        self.add_namespace(inv.parameters.rabbitmq_namespace)

        rabbitmq_binding = self.kwargs.rabbitmq_binding
        self.add_annotations(rabbitmq_binding.get("annotations", {}))
        self.add_labels(rabbitmq_binding.get("labels", {}))

        if rabbitmq_binding.source:
            self.root.spec.source = rabbitmq_binding.source

        if rabbitmq_binding.destination:
            self.root.spec.destination = rabbitmq_binding.destination

        if rabbitmq_binding.destinationType:
            self.root.spec.destinationType = rabbitmq_binding.destinationType

        if rabbitmq_binding.rabbitmqClusterReference:
            self.root.spec.rabbitmqClusterReference = (
                rabbitmq_binding.rabbitmqClusterReference
            )

        if rabbitmq_binding.routingKey:
            self.root.spec.routingKey = rabbitmq_binding.routingKey

        if rabbitmq_binding.arguments:
            self.root.spec.arguments = rabbitmq_binding.arguments

        if rabbitmq_binding.vhost:
            self.root.spec.vhost = rabbitmq_binding.vhost


class RabbitmqUser(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "rabbitmq.com/v1beta1"
        self.kwargs.kind = "User"

        self.kwargs.finalizers = list(
            "deletion.finalizers.rabbitmqclusters.rabbitmq.com"
        )
        super().new()
        self.need("name")

    def body(self):
        super().body()

        self.add_namespace(inv.parameters.rabbitmq_namespace)

        rabbitmq_user = self.kwargs.rabbitmq_user
        self.add_annotations(rabbitmq_user.get("annotations", {}))
        self.add_labels(rabbitmq_user.get("labels", {}))

        if rabbitmq_user.tags:
            self.root.spec.tags = rabbitmq_user.tags

        if rabbitmq_user.rabbitmqClusterReference:
            self.root.spec.rabbitmqClusterReference = (
                rabbitmq_user.rabbitmqClusterReference
            )

        if rabbitmq_user.importCredentialsSecret:
            self.root.spec.importCredentialsSecret = (
                rabbitmq_user.importCredentialsSecret
            )


class RabbitmqPermission(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "rabbitmq.com/v1beta1"
        self.kwargs.kind = "Permission"

        self.kwargs.finalizers = list(
            "deletion.finalizers.rabbitmqclusters.rabbitmq.com"
        )
        super().new()
        self.need("name")

    def body(self):
        super().body()

        self.add_namespace(inv.parameters.rabbitmq_namespace)

        rabbitmq_permission = self.kwargs.rabbitmq_permission
        self.add_annotations(rabbitmq_permission.get("annotations", {}))
        self.add_labels(rabbitmq_permission.get("labels", {}))

        if rabbitmq_permission.vhost:
            self.root.spec.vhost = rabbitmq_permission.vhost

        if rabbitmq_permission.user:
            self.root.spec.user = rabbitmq_permission.user

        if rabbitmq_permission.permissions:
            self.root.spec.permissions = rabbitmq_permission.permissions

        if rabbitmq_permission.rabbitmqClusterReference:
            self.root.spec.rabbitmqClusterReference = (
                rabbitmq_permission.rabbitmqClusterReference
            )

        if rabbitmq_permission.userReference:
            self.root.spec.userReference = rabbitmq_permission.userReference


class RabbitmqVhost(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "rabbitmq.com/v1beta1"
        self.kwargs.kind = "Vhost"

        self.kwargs.finalizers = list(
            "deletion.finalizers.rabbitmqclusters.rabbitmq.com"
        )
        super().new()
        self.need("name")

    def body(self):
        super().body()

        self.add_namespace(inv.parameters.rabbitmq_namespace)

        rabbitmq_vhost = self.kwargs.rabbitmq_vhost
        self.add_annotations(rabbitmq_vhost.get("annotations", {}))
        self.add_labels(rabbitmq_vhost.get("labels", {}))

        if rabbitmq_vhost.name:
            self.root.spec.name = rabbitmq_vhost.name

        if rabbitmq_vhost.rabbitmqClusterReference:
            self.root.spec.rabbitmqClusterReference = (
                rabbitmq_vhost.rabbitmqClusterReference
            )

        if rabbitmq_vhost.tags:
            self.root.spec.tags = rabbitmq_vhost.tags

        if rabbitmq_vhost.tracing:
            self.root.spec.tracing = rabbitmq_vhost.tracing


class RabbitmqFederation(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "rabbitmq.com/v1beta1"
        self.kwargs.kind = "Federation"

        self.kwargs.finalizers = list(
            "deletion.finalizers.rabbitmqclusters.rabbitmq.com"
        )
        super().new()
        self.need("name")

    def body(self):
        super().body()

        self.add_namespace(inv.parameters.rabbitmq_namespace)

        rabbitmq_federation = self.kwargs.rabbitmq_federation
        self.add_annotations(rabbitmq_federation.get("annotations", {}))
        self.add_labels(rabbitmq_federation.get("labels", {}))

        if rabbitmq_federation.name:
            self.root.spec.name = rabbitmq_federation.name

        if rabbitmq_federation.uriSecret:
            self.root.spec.uriSecret = rabbitmq_federation.uriSecret

        if rabbitmq_federation.ackMode:
            self.root.spec.ackMode = rabbitmq_federation.ackMode

        if rabbitmq_federation.rabbitmqClusterReference:
            self.root.spec.rabbitmqClusterReference = (
                rabbitmq_federation.rabbitmqClusterReference
            )

        if rabbitmq_federation.exchange:
            self.root.sec.exchange = rabbitmq_federation.exchange

        if rabbitmq_federation.expires:
            self.root.spec.expires = rabbitmq_federation.expires

        if rabbitmq_federation.maxHops:
            self.root.spec.maxHops = rabbitmq_federation.maxHops

        if rabbitmq_federation.messageTTL:
            self.root.spec.messageTTL = rabbitmq_federation.messageTTL

        if rabbitmq_federation.prefetch_count:
            self.root.spec.prefetch_count = rabbitmq_federation.prefetch_count

        if rabbitmq_federation.queue:
            self.root.spec.queue = rabbitmq_federation.queue

        if rabbitmq_federation.reconnectDelay:
            self.root.spec.reconnectDelay = rabbitmq_federation.reconnectDelay

        if rabbitmq_federation.trustUserId:
            self.root.spec.trustUserId = rabbitmq_federation.trustUserId

        if rabbitmq_federation.vhost:
            self.root.spec.vhost = rabbitmq_federation.vhost


class RabbitmqShovel(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "rabbitmq.com/v1beta1"
        self.kwargs.kind = "Shovel"

        self.kwargs.finalizers = list(
            "deletion.finalizers.rabbitmqclusters.rabbitmq.com"
        )
        super().new()
        self.need("name")

    def body(self):
        super().body()

        self.add_namespace(inv.parameters.rabbitmq_namespace)

        rabbitmq_shovel = self.kwargs.rabbitmq_shovel
        self.add_annotations(rabbitmq_shovel.get("annotations", {}))
        self.add_labels(rabbitmq_shovel.get("labels", {}))

        if rabbitmq_shovel.name:
            self.root.spec.name = rabbitmq_shovel.name

        if rabbitmq_shovel.uriSecret:
            self.root.spec.uriSecret = rabbitmq_shovel.uriSecret

        if rabbitmq_shovel.srcQueue:
            self.root.spec.srcQueue = rabbitmq_shovel.srcQueue

        if rabbitmq_shovel.destQueue:
            self.root.spec.destQueue = rabbitmq_shovel.destQueue

        if rabbitmq_shovel.rabbitmqClusterReference:
            self.root.spec.rabbitmqClusterReference = (
                rabbitmq_shovel.rabbitmqClusterReference
            )

        if rabbitmq_shovel.ackMode:
            self.root.spec.ackMode = rabbitmq_shovel.ackMode

        if rabbitmq_shovel.addForwardHeaders:
            self.root.spec.addForwardHeaders = rabbitmq_shovel.addForwardHeaders

        if rabbitmq_shovel.deleteAfter:
            self.root.spec.deleteAfter = rabbitmq_shovel.deleteAfter

        if rabbitmq_shovel.destAddForwardHeaders:
            self.root.spec.destAddForwardHeaders = rabbitmq_shovel.destAddForwardHeaders

        if rabbitmq_shovel.destAddTimestampHeader:
            self.root.spec.destAddTimestampHeader = (
                rabbitmq_shovel.destAddTimestampHeader
            )

        if rabbitmq_shovel.destAddress:
            self.root.spec.destAddress = rabbitmq_shovel.destAddress

        if rabbitmq_shovel.destApplicationProperties:
            self.root.spec.destApplicationProperties = (
                rabbitmq_shovel.destApplicationProperties
            )

        if rabbitmq_shovel.destExchange:
            self.root.spec.destExchange = rabbitmq_shovel.destExchange

        if rabbitmq_shovel.destExchangeKey:
            self.root.spec.destExchangeKey = rabbitmq_shovel.destExchangeKey

        if rabbitmq_shovel.destProperties:
            self.root.spec.destProperties = rabbitmq_shovel.destProperties

        if rabbitmq_shovel.destProtocol:
            self.root.spec.destProtocol = rabbitmq_shovel.destProtocol

        if rabbitmq_shovel.destPublishProperties:
            self.root.spec.destPublishProperties = rabbitmq_shovel.destPublishProperties

        if rabbitmq_shovel.prefetchCount:
            self.root.spec.prefetchCount = rabbitmq_shovel.prefetchCount

        if rabbitmq_shovel.reconnectDelay:
            self.root.spec.reconnectDelay = rabbitmq_shovel.reconnectDelay

        if rabbitmq_shovel.srcAddress:
            self.root.spec.srcAddress = rabbitmq_shovel.srcAddress

        if rabbitmq_shovel.srcDeleteAfter:
            self.root.spec.srcDeleteAfter = rabbitmq_shovel.srcDeleteAfter

        if rabbitmq_shovel.srcExchange:
            self.root.spec.srcExchange = rabbitmq_shovel.srcExchange

        if rabbitmq_shovel.srcExchangeKey:
            self.root.spec.srcExchangeKey = rabbitmq_shovel.srcExchangeKey

        if rabbitmq_shovel.srcPrefetchCount:
            self.root.spec.srcPrefetchCount = rabbitmq_shovel.srcPrefetchCount

        if rabbitmq_shovel.srcProtocol:
            self.root.spec.srcProtocol = rabbitmq_shovel.srcProtocol

        if rabbitmq_shovel.vhost:
            self.root.spec.vhost = rabbitmq_shovel.vhost


# The following classes are required to generate Secrets + ConfigMaps
class SharedConfig:
    """Shared class to use for both Secrets and ConfigMaps classes.

    containt anything needed by both classes, so that their behavious is basically the same.
    Each subclass will then implement its own way of adding the data depending on their implementation.
    """

    @staticmethod
    def encode_string(unencoded_string):
        return base64.b64encode(unencoded_string.encode("ascii")).decode("ascii")

    def setup_metadata(self):
        self.add_namespace(inv.parameters.rabbitmq_namespace)
        self.add_annotations(self.config.annotations)
        self.add_labels(self.config.labels)

        self.items = self.config["items"]
        try:
            if isinstance(self, ConfigMap):
                globals = (
                    inv.parameters.generators.manifest.default_config.globals.config_maps
                )
            else:
                globals = (
                    inv.parameters.generators.manifest.default_config.globals.secrets
                )
            self.add_annotations(globals.get("annotations", {}))
            self.add_labels(globals.get("labels", {}))
        except AttributeError:
            pass

        self.versioning(self.config.get("versioned", False))

    def add_directory(self, directory, encode=False):
        stringdata = inv.parameters.get("use_tesoro", False)
        if directory and os.path.isdir(directory):
            for filename in os.listdir(directory):
                with open(f"{directory}/{filename}", "r") as f:
                    file_content = f.read()
                    self.add_item(
                        filename,
                        file_content,
                        request_encode=encode,
                        stringdata=stringdata,
                    )

    def add_data(self, data):
        stringdata = inv.parameters.get("use_tesoro", False)

        for key, spec in data.items():
            encode = spec.get("b64_encode", False)

            if "value" in spec:
                value = spec.get("value")
            if "template" in spec:
                value = j2(spec.template, spec.get("values", {}))
            if "file" in spec:
                with open(spec.file, "r") as f:
                    value = f.read()

            self.add_item(key, value, request_encode=encode, stringdata=stringdata)

    def add_string_data(self, string_data, encode=False):
        stringdata = True

        for key, spec in string_data.items():

            if "value" in spec:
                value = spec.get("value")
            if "template" in spec:
                value = j2(spec.template, spec.get("values", {}))
            if "file" in spec:
                with open(spec.file, "r") as f:
                    value = f.read()

            self.add_item(key, value, request_encode=encode, stringdata=stringdata)

    def versioning(self, enabled=False):
        if enabled:
            self.hash = hashlib.sha256(str(self.root.to_dict()).encode()).hexdigest()[
                :8
            ]
            self.root.metadata.name += f"-{self.hash}"


class ConfigMap(k8s.Base, SharedConfig):
    def new(self):
        self.kwargs.apiVersion = "v1"
        self.kwargs.kind = "ConfigMap"
        super().new()

    def body(self):
        super().body()

    def add_item(self, key, value, request_encode=False, stringdata=False):
        encode = request_encode

        self.root["data"][key] = self.encode_string(value) if encode else value


class ComponentConfig(ConfigMap, SharedConfig):
    def new(self):
        super().new()
        self.need("config")

    def body(self):
        super().body()
        self.config = self.kwargs.config

        self.setup_metadata()
        self.add_data(self.config.data)
        self.add_directory(self.config.directory, encode=False)


class Secret(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = "v1"
        self.kwargs.kind = "Secret"
        super().new()

    def body(self):
        super().body()

    def add_item(self, key, value, request_encode=False, stringdata=False):
        encode = not stringdata and request_encode
        field = "stringData" if stringdata else "data"
        self.root[field][key] = self.encode_string(value) if encode else value


class ComponentSecret(Secret, SharedConfig):
    def new(self):
        super().new()
        self.need("config")

    def body(self):
        super().body()
        self.config = self.kwargs.config
        self.root.type = self.config.get("type", "Opaque")

        self.setup_metadata()
        if self.config.data:
            self.add_data(self.config.data)
        if self.config.string_data:
            self.add_string_data(self.config.string_data)
        self.add_directory(self.config.directory, encode=True)


def generate_rabbitmqcluster(input_params):
    obj = BaseObj()
    rabbitmqcluster_list = inv.parameters.rabbitmqcluster
    for name in rabbitmqcluster_list.keys():
        rabbitmqcluster = RabbitmqCluster(
            name=name, rabbitmqcluster=rabbitmqcluster_list[name]
        )

        obj.root["{}-rabbitmq".format(name)] = rabbitmqcluster

    return obj


def generate_rabbitmq_queue(input_params):
    obj = BaseObj()
    rabbitmq_queue_list = inv.parameters.rabbitmq_queue
    for name in rabbitmq_queue_list.keys():
        rabbitmq_queue = RabbitmqQueue(
            name=name, rabbitmq_queue=rabbitmq_queue_list[name]
        )

        obj.root["{}-rabbitmq".format(name)] = rabbitmq_queue
    return obj


def generate_rabbitmq_policy(input_params):
    obj = BaseObj()
    rabbitmq_policy_list = inv.parameters.rabbitmq_policy
    for name in rabbitmq_policy_list.keys():
        rabbitmq_policy = RabbitmqPolicy(
            name=name, rabbitmq_policy=rabbitmq_policy_list[name]
        )

        obj.root["{}-rabbitmq".format(name)] = rabbitmq_policy
    return obj


def generate_rabbitmq_exchange(input_params):
    obj = BaseObj()
    rabbitmq_exchange_list = inv.parameters.rabbitmq_exchange
    for name in rabbitmq_exchange_list.keys():
        rabbitmq_exchange = RabbitmqExchange(
            name=name, rabbitmq_exchange=rabbitmq_exchange_list[name]
        )

        obj.root["{}-rabbitmq".format(name)] = rabbitmq_exchange
    return obj


def generate_rabbitmq_binding(input_params):
    obj = BaseObj()
    rabbitmq_binding_list = inv.parameters.rabbitmq_binding
    for name in rabbitmq_binding_list.keys():
        rabbitmq_binding = RabbitmqBinding(
            name=name, rabbitmq_binding=rabbitmq_binding_list[name]
        )

        obj.root["{}-rabbitmq".format(name)] = rabbitmq_binding
    return obj


def generate_rabbitmq_user(input_params):
    obj = BaseObj()
    rabbitmq_user_list = inv.parameters.rabbitmq_user
    for name in rabbitmq_user_list.keys():
        rabbitmq_user = RabbitmqUser(name=name, rabbitmq_user=rabbitmq_user_list[name])

        obj.root["{}-rabbitmq".format(name)] = rabbitmq_user
    return obj


def generate_rabbitmq_permission(input_params):
    obj = BaseObj()
    rabbitmq_permission_list = inv.parameters.rabbitmq_permission
    for name in rabbitmq_permission_list.keys():
        rabbitmq_permission = RabbitmqPermission(
            name=name, rabbitmq_permission=rabbitmq_permission_list[name]
        )

        obj.root["{}-rabbitmq".format(name)] = rabbitmq_permission
    return obj


def generate_rabbitmq_vhost(input_params):
    obj = BaseObj()
    rabbitmq_vhost_list = inv.parameters.rabbitmq_vhost
    for name in rabbitmq_vhost_list.keys():
        rabbitmq_vhost = RabbitmqVhost(
            name=name, rabbitmq_vhost=rabbitmq_vhost_list[name]
        )

        obj.root["{}-rabbitmq".format(name)] = rabbitmq_vhost
    return obj


def generate_rabbitmq_federation(input_params):
    obj = BaseObj()
    rabbitmq_federation_list = inv.parameters.rabbitmq_federation
    for name in rabbitmq_federation_list.keys():
        rabbitmq_federation = RabbitmqFederation(
            name=name, rabbitmq_federation=rabbitmq_federation_list[name]
        )

        obj.root["{}-rabbitmq".format(name)] = rabbitmq_federation
    return obj


def generate_rabbitmq_shovel(input_params):
    obj = BaseObj()
    rabbitmq_shovel_list = inv.parameters.rabbitmq_shovel
    for name in rabbitmq_shovel_list.keys():
        rabbitmq_shovel = RabbitmqShovel(
            name=name, rabbitmq_shovel=rabbitmq_shovel_list[name]
        )

        obj.root["{}-rabbitmq".format(name)] = rabbitmq_shovel
    return obj


# This function renderes an Shared-ConfigMaps + Secrets
def generate_resource_manifests(input_params):
    obj = BaseObj()

    for secret_name, secret_spec in inv.parameters.generators.rabbitmq.secrets.items():
        name = secret_spec.get("name", secret_name)
        secret = ComponentSecret(name=name, config=secret_spec)
        obj.root[f"{name}"] = secret

    for config_name, config_spec in inv.parameters.generators.rabbitmq.configs.items():
        name = config_spec.get("name", config_name)
        config = ComponentConfig(name=name, config=config_spec)
        obj.root[f"{name}"] = config
    return obj


# This function renderes all previous defined functions and returns


def generate_manifests(input_params):
    all_manifests = BaseObj()

    rabbitmq_manifests = generate_rabbitmqcluster(input_params)
    rabbitmq_queue_manifests = generate_rabbitmq_queue(input_params)
    rabbitmq_policy_manifests = generate_rabbitmq_policy(input_params)
    rabbitmq_exchange_manifests = generate_rabbitmq_exchange(input_params)
    rabbitmq_binding_manifests = generate_rabbitmq_binding(input_params)
    rabbitmq_user_manifests = generate_rabbitmq_user(input_params)
    rabbitmq_permission_manifests = generate_rabbitmq_permission(input_params)
    rabbitmq_vhost_manifests = generate_rabbitmq_vhost(input_params)
    rabbitmq_federation_manifests = generate_rabbitmq_federation(input_params)
    rabbitmq_shovel_manifests = generate_rabbitmq_shovel(input_params)

    resource_manifests = generate_resource_manifests(input_params)

    all_manifests.root.update(rabbitmq_manifests.root)
    all_manifests.root.update(rabbitmq_queue_manifests.root)
    all_manifests.root.update(rabbitmq_policy_manifests.root)
    all_manifests.root.update(rabbitmq_exchange_manifests.root)
    all_manifests.root.update(rabbitmq_binding_manifests.root)
    all_manifests.root.update(rabbitmq_user_manifests.root)
    all_manifests.root.update(rabbitmq_permission_manifests.root)
    all_manifests.root.update(rabbitmq_vhost_manifests.root)
    all_manifests.root.update(rabbitmq_federation_manifests.root)
    all_manifests.root.update(rabbitmq_shovel_manifests.root)

    all_manifests.root.update(resource_manifests.root)

    return all_manifests


def main(input_params):
    whitelisted_functions = ["generate_manifests"]
    function = input_params.get("function", "generate_manifests")
    if function in whitelisted_functions:
        return globals()[function](input_params)
