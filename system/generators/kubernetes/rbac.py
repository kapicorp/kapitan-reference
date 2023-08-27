import logging

logger = logging.getLogger(__name__)

from .common import KubernetesResource, kgenlib


class Role(KubernetesResource):
    kind = "Role"
    api_version = "rbac.authorization.k8s.io/v1"

    def body(self):
        super().body()
        config = self.config
        self.root.rules = config["role"]["rules"]


class RoleBinding(KubernetesResource):
    kind = "RoleBinding"
    api_version = "rbac.authorization.k8s.io/v1"

    def body(self):
        super().body()
        config = self.config
        sa = self.sa
        name = config.get("name", self.name)
        default_role_ref = {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "Role",
            "name": name,
        }
        default_subject = [
            {
                "kind": "ServiceAccount",
                "name": sa.name,
                "namespace": sa.namespace,
            }
        ]
        self.root.roleRef = config.get("roleRef", default_role_ref)
        self.root.subjects = config.get("subject", default_subject)


class ClusterRole(KubernetesResource):
    kind = "ClusterRole"
    api_version = "rbac.authorization.k8s.io/v1"

    def new(self):
        super().new()

    def body(self):
        super().body()
        config = self.config
        self.root.rules = config.cluster_role.rules


class ClusterRoleBinding(KubernetesResource):
    kind = "ClusterRoleBinding"
    api_version = "rbac.authorization.k8s.io/v1"

    def body(self):
        super().body()
        config = self.config
        sa = self.sa
        default_role_ref = {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": config.name,
        }
        default_subject = [
            {
                "kind": "ServiceAccount",
                "name": sa.name,
                "namespace": sa.namespace,
            }
        ]
        self.root.roleRef = config.get("roleRef", default_role_ref)
        self.root.subjects = config.get("subject", default_subject)


@kgenlib.register_generator(path="generators.kubernetes.service_accounts")
class ServiceAccountGenerator(kgenlib.BaseStore):
    def body(self):
        config = self.config
        name = config.get("name", self.name)
        namespace = config["namespace"]
        sa = ServiceAccount(name=name, config=config)
        sa.add_annotations(config.annotations)
        sa.add_labels(config.labels)

        roles = config.get("roles")
        objs = [sa]
        if roles is not None:
            role_cfg = {"role": {"rules": roles}}
            r = Role(name=f"{name}-role", namespace=namespace, config=role_cfg)
            rb_cfg = {"name": r.name}
            rb = RoleBinding(
                name=f"{name}-role-binding", namespace=namespace, config=rb_cfg, sa=sa
            )

            objs += [r, rb]

        self.add_list(objs)


class ServiceAccount(KubernetesResource):
    kind = "ServiceAccount"
    api_version = "v1"

    def new(self):
        super().new()

    def body(self):
        super().body()
        config = self.config
        self.add_annotations(config.service_account.annotations)
