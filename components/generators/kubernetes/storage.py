import base64
import hashlib
import logging
import os

from kapitan.inputs.kadet import BaseModel, Dict, load_from_search_paths

from .common import KubernetesResource, ResourceTypes, ResourceType

logger = logging.getLogger(__name__)
kgenlib = load_from_search_paths("generators")


class SharedConfig(KubernetesResource):
    """Shared class to use for both Secrets and ConfigMaps classes.

    containt anything needed by both classes, so that their behavious is basically the same.
    Each subclass will then implement its own way of adding the data depending on their implementation.
    """

    component: Dict = None
    versioning_enabled: bool = False

    @staticmethod
    def encode_string(unencoded_string):
        return base64.b64encode(unencoded_string.encode("ascii")).decode("ascii")

    def setup_metadata(self, inventory):
        namespace = inventory.parameters.get("namespace", None)

        if self.component:
            namespace = self.component.get("namespace", namespace)

        namespace = self.config.get("namespace", namespace)

        if namespace:
            self.add_namespace(namespace)

        self.add_annotations(self.config.get("annotations", {}).copy())
        self.add_labels(self.config.get("labels", {}).copy())
        self.setup_global_defaults(inventory=inventory)

        self.items = self.config["items"]

    def add_directory(self, directory, encode=False, stringdata=False):
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
        self.versioning(enabled=self.versioning_enabled)

    def add_data(self, data, stringdata=False):
        for key, spec in data.items():
            encode = spec.get("b64_encode", False)

            if "value" in spec:
                value = spec.get("value")
            if "template" in spec:
                value = kgenlib.render_jinja(spec.template, spec.get("values", {}))
            if "file" in spec:
                with open(spec.file, "r") as f:
                    value = f.read()

            self.add_item(key, value, request_encode=encode, stringdata=stringdata)
        self.versioning(enabled=self.versioning_enabled)

    def add_item(self, key, value, request_encode=False, stringdata=False):
        encode = not stringdata and request_encode
        field = "stringData" if stringdata else "data"
        
        self.root[field][key] = self.encode_string(value) if encode else value
    
    def add_string_data(self, string_data, encode=False, stringdata=True):

        for key, spec in string_data.items():

            if "value" in spec:
                value = spec.get("value")
            if "template" in spec:
                value = kgenlib.render_jinja(spec.template, spec.get("values", {}))
            if "file" in spec:
                with open(spec.file, "r") as f:
                    value = f.read()

            self.add_item(key, value, request_encode=encode, stringdata=stringdata)
        
        self.versioning(enabled=self.versioning_enabled)

    def versioning(self, enabled=False):
        if enabled:
            keys_of_interest = ["data", "binaryData", "stringData"]
            subset = {
                key: value
                for key, value in self.root.to_dict().items()
                if key in keys_of_interest
            }
            self.hash = hashlib.sha256(str(subset).encode()).hexdigest()[:8]
            self.rendered_name = f"{self.name}-{self.hash}"
            self.root.metadata.name = self.rendered_name


class ConfigMap(SharedConfig):
    resource_type = ResourceType(kind="ConfigMap", api_version="v1", id="config_map")

class Secret(SharedConfig):
    resource_type = ResourceType(kind="Secret", api_version="v1", id="secret")