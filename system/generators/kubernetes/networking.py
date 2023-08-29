import logging

logger = logging.getLogger(__name__)

from typing import Any

from .common import KubernetesResource, kgenlib


class Ingress(KubernetesResource):
    kind = "Ingress"
    api_version = "networking.k8s.io/v1"

    def new(self):
        super().new()

    def body(self):
        super().body()
        config = self.config

        self.add_annotations(config.get("annotations", {}))
        self.add_labels(config.get("labels", {}))
        if "default_backend" in config:
            self.root.spec.backend.service.name = config.default_backend.get("name")
            self.root.spec.backend.service.port = config.default_backend.get("port", 80)
        if "paths" in config:
            host = config.host
            paths = config.paths
            self.root.spec.setdefault("rules", []).extend(
                [{"host": host, "http": {"paths": paths}}]
            )
        if "rules" in config:
            self.root.spec.setdefault("rules", []).extend(config.rules)
        if config.tls:
            self.root.spec.tls = config.tls


class GoogleManagedCertificate(KubernetesResource):
    kind = "ManagedCertificate"
    api_version = "networking.gke.io/v1beta1"

    def body(self):
        super().body()
        config = self.config
        self.root.spec.domains = config.get("domains", [])


class NetworkPolicy(KubernetesResource):
    kind = "NetworkPolicy"
    api_version = "networking.k8s.io/v1"

    def body(self):
        super().body()
        policy = self.config
        workload = self.workload
        self.root.spec.podSelector.matchLabels = workload.root.metadata.labels
        self.root.spec.ingress = policy.ingress
        self.root.spec.egress = policy.egress
        if self.root.spec.ingress:
            self.root.spec.setdefault("policyTypes", []).append("Ingress")

        if self.root.spec.egress:
            self.root.spec.setdefault("policyTypes", []).append("Egress")


class HealthCheckPolicy(KubernetesResource):
    kind = "HealthCheckPolicy"
    api_version = "networking.gke.io/v1"

    def body(self):
        super().body()
        config = self.config

        self.root.spec.default.logConfig.enabled = config.healthcheck.get("log", False)

        config_spec = self.root.spec.default.config
        container_port = config.healthcheck.get("container_port", self.name)
        config_spec.type = config.healthcheck.get("type", "HTTP").upper()
        if config_spec.type == "HTTP":
            config_spec.httpHealthCheck.portSpecification = "USE_FIXED_PORT"
            config_spec.httpHealthCheck.port = container_port
            config_spec.httpHealthCheck.requestPath = config.healthcheck.get(
                "path", config.get("path", "/")
            )

        self.root.spec.targetRef = {
            "group": "",
            "kind": "Service",
            "name": config.get("service"),
        }


class Gateway(KubernetesResource):
    kind = "Gateway"
    api_version = "gateway.networking.k8s.io/v1beta1"

    def body(self):
        super().body()
        self.root.spec.gatewayClassName = self.config.type
        default_listener = {"name": "http", "protocol": "HTTP", "port": 80}

        certificate = self.config.get("certificate", None)
        if certificate:
            default_listener = {
                "name": "https",
                "protocol": "HTTPS",
                "port": 443,
                "tls": {
                    "mode": "Terminate",
                    "certificateRefs": [{"name": certificate}],
                },
            }

        self.root.spec.listeners = self.config.listeners or [default_listener]

        if self.config.get("named_address"):
            self.root.spec.setdefault("addresses", []).append(
                {"type": "NamedAddress", "value": self.config.get("named_address")}
            )


class GCPGatewayPolicy(KubernetesResource):
    kind = "GCPGatewayPolicy"
    api_version = "networking.gke.io/v1"
    gateway: Gateway = None

    def body(self):
        super().body()
        self.root.spec.default.allowGlobalAccess = self.config.get(
            "allow_global_access", False
        )
        self.root.spec.targetRef = {
            "group": "gateway.networking.k8s.io",
            "kind": "Gateway",
            "name": self.gateway.name,
        }


class HTTPRoute(KubernetesResource):
    kind = "HTTPRoute"
    api_version = "gateway.networking.k8s.io/v1beta1"
    gateway: Gateway = None

    def body(self):
        super().body()
        self.root.spec.setdefault("parentRefs", []).append(
            {
                "kind": "Gateway",
                "name": self.gateway.name,
            }
        )

        self.root.spec.hostnames = self.config.get("hostnames", [])

        for service_name, service_config in self.config.get("services", {}).items():
            match = {"path": {"value": service_config.get("path", "/")}}
            rule = {
                "backendRefs": [
                    {
                        "name": service_config.get("service", service_name),
                        "port": service_config.get("port", 80),
                    }
                ],
                "matches": [match],
            }
            self.root.spec.setdefault("rules", []).append(rule)


@kgenlib.register_generator(
    path="generators.kubernetes.gateway",
)
class GatewayGenerator(kgenlib.BaseStore):
    def body(self):
        gateway = Gateway(name=self.name, config=self.config)
        self.add(gateway)

        policy = GCPGatewayPolicy(name=self.name, config=self.config, gateway=gateway)
        self.add(policy)

        for route_id, route_config in self.config.get("routes", {}).items():
            route_name = f"{self.name}-{route_id}"
            route = HTTPRoute(name=route_name, config=route_config, gateway=gateway)
            self.add(route)

            for service_id, service_config in route_config.get("services", {}).items():
                healthcheck = HealthCheckPolicy(
                    name=f"{route_name}-{service_id}",
                    config=service_config,
                    gateway=gateway,
                )
                self.add(healthcheck)


class Service(KubernetesResource):
    kind = "Service"
    api_version = "v1"

    service_spec: dict

    def new(self):
        super().new()

    def body(self):
        config = self.config
        workload = self.workload.root
        service_spec = self.service_spec

        self.name = service_spec.get("service_name", self.name)
        super().body()

        self.add_labels(config.get("labels", {}))
        self.add_annotations(service_spec.annotations)
        self.root.spec.setdefault("selector", {}).update(
            workload.spec.template.metadata.labels
        )
        self.root.spec.setdefault("selector", {}).update(service_spec.selectors)
        self.root.spec.type = service_spec.type
        if service_spec.get("publish_not_ready_address", False):
            self.root.spec.publishNotReadyAddresses = True
        if service_spec.get("headless", False):
            self.root.spec.clusterIP = "None"
        self.root.spec.clusterIP
        self.root.spec.sessionAffinity = service_spec.get("session_affinity", "None")
        all_ports = [config.ports] + [
            container.ports
            for container in config.additional_containers.values()
            if "ports" in container
        ]

        self.exposed_ports = {}

        for port in all_ports:
            for port_name in port.keys():
                if (
                    not service_spec.expose_ports
                    or port_name in service_spec.expose_ports
                ):
                    self.exposed_ports.update(port)

        for port_name in sorted(self.exposed_ports):
            self.root.spec.setdefault("ports", [])
            port_spec = self.exposed_ports[port_name]
            port_spec["name"] = port_name
            service_port = port_spec.get("service_port", None)
            if service_port:
                self.root.spec.setdefault("ports", []).append(
                    {
                        "name": port_name,
                        "port": service_port,
                        "targetPort": port_name,
                        "protocol": port_spec.get("protocol", "TCP"),
                    }
                )


@kgenlib.register_generator(path="ingresses")
class IngressComponent(kgenlib.BaseStore):
    name: str
    config: Any

    def body(self):
        name = self.name
        config = self.config
        ingress = Ingress(name=name, config=config)
        self.add(ingress)

        if "managed_certificate" in config:
            certificate_name = config.managed_certificate
            additional_domains = config.get("additional_domains", [])
            domains = [certificate_name] + additional_domains
            ingress.add_annotations(
                {"networking.gke.io/managed-certificates": certificate_name}
            )
            self.add(
                GoogleManagedCertificate(
                    name=certificate_name, config={"domains": domains}
                )
            )
