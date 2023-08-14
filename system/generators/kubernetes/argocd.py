import json
import logging

logger = logging.getLogger(__name__)

from .base import Namespace
from .common import KubernetesResource, kgenlib


class ArgoCDApplication(KubernetesResource):
    source: dict = None
    kind = "Application"
    api_version = "argoproj.io/v1alpha1"

    def body(self):
        super().body()
        project = self.config.get("project", "default")
        self.root.spec.project = project
        self.root.spec.destination = self.config.get("destination")
        self.root.spec.source = self.config.get("source")
        if self.config.get("sync_policy"):
            self.root.spec.syncPolicy = self.config.get("sync_policy")

        self.root.spec.ignoreDifferences = self.config.get("ignore_differences", None)
        namespace = self.config.get("namespace", None)

        if namespace is None:
            namespace = f"argocd-project-{project}"

        self.set_namespace(namespace)


@kgenlib.register_generator(
    path="generators.argocd.applications",
    global_generator=True,
    activation_path="argocd.app_of_apps",
    apply_patches=["generators.argocd.defaults.application"],
)
class GenArgoCDApplication(kgenlib.BaseStore):
    def body(self):
        config = self.config
        namespace = config.get("namespace", "argocd")
        name = config.get("name", self.name)

        argo_application = ArgoCDApplication(
            name=name, namespace=namespace, config=config
        )
        self.add(argo_application)


class ArgoCDProject(KubernetesResource):
    kind = "AppProject"
    api_version = "argoproj.io/v1alpha1"

    def body(self):
        super().body()
        self.root.spec.sourceRepos = self.config.get("source_repos")
        self.root.spec.destinations = self.config.get("destinations")
        if self.config.get("cluster_resource_whitelist"):
            self.root.spec.clusterResourceWhitelist = self.config.get(
                "cluster_resource_whitelist"
            )
        self.root.spec.sourceNamespaces = self.config.setdefault(
            "source_namespaces", [f"argocd-project-{self.name}"]
        )


@kgenlib.register_generator(
    path="generators.argocd.projects",
    apply_patches=["generators.argocd.defaults.project"],
)
class GenArgoCDProject(kgenlib.BaseStore):
    def body(self):
        config = self.config
        namespace = config.get("namespace", "argocd")
        name = config.get("name", self.name)

        self.add(ArgoCDProject(name=name, namespace=namespace, config=config))
        self.add(Namespace(name=f"argocd-project-{name}", config=config))


@kgenlib.register_generator(
    path="clusters", global_generator=True, activation_path="argocd.clusters"
)
class GenArgoCDCluster(kgenlib.BaseStore):
    def body(self):
        config = self.config
        target = self.target
        namespace = self.global_inventory[target]["parameters"]["namespace"]
        name = config.get("name")
        cluster = ArgoCDCluster(name=name, namespace=namespace, config=config)

        self.add(cluster)


class ArgoCDCluster(KubernetesResource):
    kind = "Secret"
    api_version = "v1"

    def body(self):
        super().body()
        self.add_label("argocd.argoproj.io/secret-type", "cluster")
        self.root.stringData.name = self.config.argocd.name
        self.root.stringData.server = self.config.endpoint_url
        self.root.stringData.config = json.dumps(self.config.argocd.config, indent=4)
