import base64
import hashlib
import os

from kapitan.cached import args
from kapitan.inputs.kadet import BaseObj, inventory
from kapitan.utils import render_jinja2_file

search_paths = args.get('search_paths')

from . import k8s


def j2(filename, ctx):
    return render_jinja2_file(filename, ctx, search_paths=search_paths)

inv = inventory()

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

class ArgoCDAppProject(k8s.Base):
    def new(self):
        self.need('name')
        self.kwargs.apiVersion = 'argoproj.io/v1alpha1'
        self.kwargs.kind = 'AppProject'

        # Add a this finalizer ONLY if you want these to cascade delete
        self.kwargs.finalizers = list('resources-finalizer.argocd.argoproj.io')
        super().new()

    def body(self):
        super().body()

        # You'll usually want to add your resources to the argocd namespace.
        self.add_namespace(inv.parameters.argocd_namespace)

        argocd_project = self.kwargs.argocd_project

        self.add_annotations(argocd_project.get('annotations', {}))
        self.add_labels(argocd_project.get('labels', {}))

        # Allow manifests to deploy from any Git repos
        if argocd_project.source_repos:
            self.root.spec.sourceRepos = argocd_project.source_repos

        # Only permit applications to deploy to the namespace in the same cluster
        if argocd_project.destinations:
            self.root.spec.destinations = argocd_project.destinations

        # Deny all cluster-scoped resources from being created, except for Namespace
        if argocd_project.cluster_resource_whitelist:
            self.root.spec.clusterResourceWhitelist = argocd_project.cluster_resource_whitelist

        # Allow all namespaced-scoped resources to be created, except for ResourceQuota, LimitRange, NetworkPolicy
        if argocd_project.namespace_resource_blacklist:
            self.root.spec.namespaceResourceBlacklist = argocd_project.namespace_resource_blacklist

        # Deny all namespaced-scoped resources from being created, except for Deployment and StatefulSet
        if argocd_project.namespace_resource_whitelist:
            self.root.spec.namespaceResourceWhitelist = argocd_project.namespace_resource_whitelist

        # Enables namespace orphaned resource monitoring.
        if argocd_project.orphaned_resources:
            self.root.spec.orphanedResources = argocd_project.orphaned_resources

        # Roles
        if argocd_project.roles:
            self.root.spec.roles = argocd_project.roles


class ArgoCDApplication(k8s.Base):
    def new(self):
        self.need('name')
        self.kwargs.apiVersion = 'argoproj.io/v1alpha1'
        self.kwargs.kind = 'Application'
        
       # Add a this finalizer ONLY if you want these to cascade delete
        
       # self.kwargs.finalizers = list('resources-finalizer.argocd.argoproj.io')
        super().new()

    def body(self):
        super().body()

       # You'll usually want to add your resources to the argocd namespace.
        self.add_namespace(inv.parameters.argocd_namespace)

        argocd_application = self.kwargs.argocd_application

        self.add_annotations(argocd_application.get('annotations', {}))
        self.add_labels(argocd_application.get('labels', {}))

       # The project the argocd_application belongs to.
        self.root.spec.project = argocd_application.project
        
       # The destination in which Namespace the application should be deployed
        self.root.spec.destination = argocd_application.destination
        
       # Source of the application manifests
        if argocd_application.source:
            self.root.spec.source = argocd_application.source

       # Sync policy
        if argocd_application.sync_policy:
            self.root.spec.syncPolicy = argocd_application.sync_policy

       # Ignore differences at the specified json pointers
        if argocd_application.ignore_differences:
            self.root.spec.ignoreDifferences = argocd_application.ignore_differences

# The following classes are required to generate Secrets + ConfigMaps
# TODO: Imported from k8s-generator
class SharedConfig():
    """Shared class to use for both Secrets and ConfigMaps classes.

    contain anything needed by both classes, so that their behavious is basically the same.
    Each subclass will then implement its own way of adding the data depending on their implementation.
    """
    @staticmethod
    def encode_string(unencoded_string):
        return base64.b64encode(unencoded_string.encode('ascii')).decode('ascii')

    def setup_metadata(self):
        self.add_namespace(inv.parameters.argocd_namespace)
        self.add_annotations(self.config.annotations)
        self.add_labels(self.config.labels)

        self.items = self.config['items']
        try:
            if isinstance(self, ConfigMap):
                globals = inv.parameters.generators.manifest.default_config.globals.config_maps
            else:
                globals = inv.parameters.generators.manifest.default_config.globals.secrets
            self.add_annotations(globals.get('annotations', {}))
            self.add_labels(globals.get('labels', {}))
        except AttributeError:
            pass

        self.versioning(self.config.get('versioned', False))

    def add_directory(self, directory, encode=False):
        stringdata = inv.parameters.get('use_tesoro', False)
        if directory and os.path.isdir(directory):
            for filename in os.listdir(directory):
                with open(f'{directory}/{filename}', 'r') as f:
                    file_content = f.read()
                    self.add_item(filename, file_content, request_encode=encode,
                                  stringdata=stringdata)

    def add_data(self, data):
        stringdata = inv.parameters.get('use_tesoro', False)

        for key, spec in data.items():
            encode = spec.get('b64_encode', False)

            if 'value' in spec:
                value = spec.get('value')
            if 'template' in spec:
                value = j2(
                    spec.template, spec.get('values', {}))
            if 'file' in spec:
                with open(spec.file, 'r') as f:
                    value = f.read()

            self.add_item(key, value, request_encode=encode,
                          stringdata=stringdata)

    def add_string_data(self, string_data, encode=False):
        stringdata = True

        for key, spec in string_data.items():

            if 'value' in spec:
                value = spec.get('value')
            if 'template' in spec:
                value = j2(
                    spec.template, spec.get('values', {}))
            if 'file' in spec:
                with open(spec.file, 'r') as f:
                    value = f.read()

            self.add_item(key, value, request_encode=encode,
                          stringdata=stringdata)

    def versioning(self, enabled=False):
        if enabled:
            self.hash = hashlib.sha256(
                str(self.root.to_dict()).encode()).hexdigest()[:8]
            self.root.metadata.name += f'-{self.hash}'

# TODO: Imported from k8s-generator
class ConfigMap(k8s.Base, SharedConfig):
    def new(self):
        self.kwargs.apiVersion = 'v1'
        self.kwargs.kind = 'ConfigMap'
        super().new()

    def body(self):
        super().body()

    def add_item(self, key, value, request_encode=False, stringdata=False):
        encode = request_encode

        self.root['data'][key] = self.encode_string(
            value) if encode else value

# TODO: Imported from k8s-generator
class ComponentConfig(ConfigMap, SharedConfig):
    def new(self):
        super().new()
        self.need('config')

    def body(self):
        super().body()
        self.config = self.kwargs.config

        self.setup_metadata()
        self.add_data(self.config.data)
        self.add_directory(self.config.directory, encode=False)

class Secret(k8s.Base):
    def new(self):
        self.kwargs.apiVersion = 'v1'
        self.kwargs.kind = 'Secret'
        super().new()

    def body(self):
        super().body()

    def add_item(self, key, value, request_encode=False, stringdata=False):
        encode = not stringdata and request_encode
        field = 'stringData' if stringdata else 'data'
        self.root[field][key] = self.encode_string(
            value) if encode else value

class ComponentSecret(Secret, SharedConfig):
    def new(self):
        super().new()
        self.need('config')

    def body(self):
        super().body()
        self.config = self.kwargs.config
        self.root.type = self.config.get('type', 'Opaque')

        self.setup_metadata()
        if self.config.data:
            self.add_data(self.config.data)
        if self.config.string_data:
            self.add_string_data(self.config.string_data)
        self.add_directory(self.config.directory, encode=True)

# This function renderes an ArgoCD-AppProject
def generate_argocd_appproject(input_params):
    obj = BaseObj()
    bundle = list()
    argocd_projects = inv.parameters.argocd_projects
    for name in argocd_projects.keys():
        argocd_project = ArgoCDAppProject(
            name=name, argocd_project=argocd_projects[name])

        obj.root['{}-argo-appproject'.format(name)] = argocd_project

    return obj

# This function renderes an ArgoCD-Application
def generate_argocd_application(input_params):
    obj = BaseObj()
    bundle = list()
    argocd_applications = inv.parameters.argocd_applications
    for name in argocd_applications.keys():
        argocd_application = ArgoCDApplication(
            name=name, argocd_application=argocd_applications[name])

        obj.root['{}-argo-application'.format(name)] = argocd_application

    return obj

# This function renderes an Shared-ConfigMaps + Secrets
def generate_resource_manifests(input_params):
    obj = BaseObj()

    for secret_name, secret_spec in inv.parameters.generators.argocd.secrets.items():
        name = secret_spec.get('name', secret_name)
        secret = ComponentSecret(name=name, config=secret_spec)
        obj.root[f'{name}'] = secret

    for config_name, config_spec in inv.parameters.generators.argocd.configs.items():
        name = config_spec.get('name', config_name)
        config = ComponentConfig(name=name, config=config_spec)
        obj.root[f'{name}'] = config

    return obj

# This function renderes all previous defined functions and returns
def generate_manifests(input_params):
    all_manifests = BaseObj()

    argocd_project_manifests = generate_argocd_appproject(input_params)
    argocd_application_manifests = generate_argocd_application(input_params)
    resource_manifests = generate_resource_manifests(input_params)

    all_manifests.root.update(argocd_project_manifests.root)
    all_manifests.root.update(argocd_application_manifests.root)
    all_manifests.root.update(resource_manifests.root)

    return all_manifests

def main(input_params):
    whitelisted_functions = ['generate_manifests']
    function = input_params.get('function', 'generate_manifests')
    if function in whitelisted_functions:
        return globals()[function](input_params)
