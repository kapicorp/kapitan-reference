from kapitan.inputs.kadet import BaseModel, load_from_search_paths

kgenlib = load_from_search_paths("generators")


class ResourceType(BaseModel):
    kind: str
    id: str
    api_version: str


class KubernetesResource(kgenlib.BaseContent):
    resource_type: ResourceType
    name: str
    api_version: str = None
    kind: str = None
    rendered_name: str = None
    id: str = None

    @property
    def component_name(self):
        return self.root.metadata.labels.get("app.kapicorp.dev/component", self.name)

    def new(self):
        self.kind = self.resource_type.kind
        self.api_version = self.resource_type.api_version
        self.id = self.resource_type.id
        self.namespace = self.config.get("namespace", None)

    def body(self):
        self.root.apiVersion = self.api_version
        self.root.kind = self.kind
        self.name = self.name
        self.rendered_name = self.config.get("rendered_name", self.name)
        self.root.metadata.namespace = self.namespace
        self.root.metadata.name = self.rendered_name
        self.add_label("name", self.name)

    def add_label(self, key: str, value: str):
        self.root.metadata.labels[key] = value

    def add_labels(self, labels: dict):
        for key, value in labels.items():
            self.add_label(key, value)

    def add_annotation(self, key: str, value: str):
        self.root.metadata.annotations[key] = value

    def add_annotations(self, annotations: dict):
        for key, value in annotations.items():
            self.add_annotation(key, value)

    def add_namespace(self, namespace: str):
        self.root.metadata.namespace = namespace

    def set_labels(self, labels: dict):
        self.root.metadata.labels = labels

    def set_annotations(self, annotations: dict):
        self.root.metadata.annotations = annotations

    def setup_global_defaults(self, inventory):
        try:
            globals = (
                inventory.parameters.generators.manifest.default_config.globals.get(
                    self.id, {}
                )
            )
            self.add_annotations(globals.get("annotations", {}))
            self.add_labels(globals.get("labels", {}))
        except AttributeError:
            pass
