import logging

logger = logging.getLogger(__name__)

import base64
import hashlib
import logging
import os

from kapitan.inputs.kadet import Dict

from .common import KubernetesResource, kgenlib


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

    def setup_metadata(self):
        namespace = None
        if self.component:
            namespace = self.component.get("namespace", namespace)

        namespace = self.config.get("namespace", namespace)

        if namespace:
            self.set_namespace(namespace)

        self.add_annotations(self.config.get("annotations", {}).copy())
        self.add_labels(self.config.get("labels", {}).copy())

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
    kind = "ConfigMap"
    api_version = "v1"


class Secret(SharedConfig):
    kind = "Secret"
    api_version = "v1"


class ComponentConfig(ConfigMap):
    config: Dict

    def body(self):
        super().body()
        self.setup_metadata()
        self.versioning_enabled = self.config.get("versioned", False)
        if getattr(self, "workload", None) and self.workload.root.metadata.name:
            self.add_label("name", self.workload.root.metadata.name)
        self.add_data(self.config.data)
        self.add_directory(self.config.directory, encode=False)
        if getattr(self, "workload", None):
            self.workload.add_volumes_for_object(self)


class ComponentSecret(Secret):
    config: Dict

    def new(self):
        super().new()

    def body(self):
        super().body()
        self.root.type = self.config.get("type", "Opaque")
        self.versioning_enabled = self.config.get("versioned", False)
        if getattr(self, "workload", None) and self.workload.root.metadata.name:
            self.add_label("name", self.workload.root.metadata.name)
        self.setup_metadata()
        if self.config.data:
            self.add_data(self.config.data)
        if self.config.string_data:
            self.add_string_data(self.config.string_data)
        self.add_directory(self.config.directory, encode=True)
        if getattr(self, "workload", None):
            self.workload.add_volumes_for_object(self)


@kgenlib.register_generator(
    path="generators.kubernetes.secrets",
    apply_patches=["generators.manifest.default_resource"],
)
class SecretGenerator(kgenlib.BaseStore):
    def body(self):
        self.add(ComponentSecret(name=self.name, config=self.config))


@kgenlib.register_generator(
    path="generators.kubernetes.config_maps",
    apply_patches=["generators.manifest.default_resource"],
)
class ConfigGenerator(kgenlib.BaseStore):
    def body(self):
        self.add(ComponentConfig(name=self.name, config=self.config))
