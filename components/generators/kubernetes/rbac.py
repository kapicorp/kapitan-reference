from kapitan.inputs.kadet import load_from_search_paths

from .common import KubernetesResource, ResourceTypes

kgenlib = load_from_search_paths("generators")


class Role(KubernetesResource):
    resource_type = ResourceTypes.ROLE.value

    def new(self):
        super().new()

    def body(self):
        super().body()
        config = self.config
        self.root.rules = config.role.rules


class RoleBinding(KubernetesResource):
    resource_type = ResourceTypes.ROLE_BINDING.value

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
    resource_type = ResourceTypes.CLUSTER_ROLE.value

    def new(self):
        super().new()

    def body(self):
        super().body()
        config = self.config
        self.root.rules = config.cluster_role.rules


class ClusterRoleBinding(KubernetesResource):
    resource_type = ResourceTypes.CLUSTER_ROLE_BINDING.value

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
