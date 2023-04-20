from kapitan.inputs.kadet import load_from_search_paths

from .common import KubernetesResource, ResourceType

kgenlib = load_from_search_paths("generators")


class Role(KubernetesResource):
    resource_type = ResourceType(
        kind="Role", api_version="rbac.authorization.k8s.io/v1", id="role"
    )

    def new(self):
        super().new()

    def body(self):
        super().body()
        config = self.config
        self.root.rules = config.role.rules


class RoleBinding(KubernetesResource):
    resource_type = ResourceType(
        kind="RoleBinding",
        api_version="rbac.authorization.k8s.io/v1",
        id="role_binding",
    )

    def new(self):
        super().new()

    def body(self):
        super().body()
        config = self.config
        sa = self.sa
        default_role_ref = {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "Role",
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


class ClusterRole(KubernetesResource):
    resource_type = ResourceType(
        kind="ClusterRole",
        api_version="rbac.authorization.k8s.io/v1",
        id="cluster_role",
    )

    def new(self):
        super().new()

    def body(self):
        super().body()
        config = self.config
        self.root.rules = config.cluster_role.rules


class ClusterRoleBinding(KubernetesResource):
    resource_type = ResourceType(
        kind="ClusterRoleBinding",
        api_version="rbac.authorization.k8s.io/v1",
        id="cluster_role_binding",
    )

    def new(self):
        super().new()

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
