import logging

from kapitan.inputs.kadet import load_from_search_paths

kgenlib = load_from_search_paths("kgenlib")
logger = logging.getLogger(__name__)


class TerraformStore(kgenlib.BaseStore):
    def dump(self, output_filename=None):
        """Return object dict/list."""
        for content in self.get_content_list():
            if output_filename:
                output_format = output_filename
            else:
                output_format = getattr(content, "filename", "output")

            filename = output_format.format(content=content)
            logging.debug(f"Adding {content.root} to {filename}")
            kgenlib.merge(content.root, self.root.setdefault(filename, {}))

        return super().dump(already_processed=True)


class TerraformBlock(kgenlib.BaseContent):
    block_type: str
    type: str = None
    id: str
    defaults: dict = {}
    config: dict = {}

    def new(self):
        if self.type:
            self.filename = f"{self.type}.tf"
            self.provider = self.type.split("_")[0]
            self.patch_config(f"provider.{self.provider}.{self.block_type}")
        else:
            self.filename = f"{self.block_type}.tf"

        self.patch_config(f"{self.type}")

    def patch_config(self, inventory_path: str) -> None:
        """Apply patch to config"""
        patch = kgenlib.findpath(self.defaults, inventory_path, {})
        logging.debug(f"Applying patch {inventory_path} for {self.id}: {patch}")
        kgenlib.merge(patch, self.config)

    @property
    def resource(self):
        if self.type:
            return self.root[self.block_type][self.type].setdefault(self.id, {})
        else:
            return self.root[self.block_type].setdefault(self.id, {})

    @resource.setter
    def resource(self, value):
        self.add(value)

    def set(self, config=None):
        if config is None:
            config = self.config
        self.root[self.block_type][self.type].setdefault(self.id, config).update(config)

    def add(self, name, value):
        self.root[self.block_type][self.type].setdefault(self.id, {})[name] = value

    def get_reference(
        self, attr: str = None, wrap: bool = True, prefix: str = ""
    ) -> str:
        """Get reference or attribute reference for terraform resource

        Args:
            attr (str, optional): The attribute to get. Defaults to None.
            wrap (bool, optional): Whether to wrap the result. Defaults to True.
            prefix (str, optional): Whether to prefix the result. Defaults to "".

        Raises:
            TypeError: Unknown block_type

        Returns:
            str: a reference or attribute reference for terraform, e.g. "${var.foo}"
        """

        if self.block_type in ("data", "resource"):
            reference = f"{prefix}{self.type}.{self.id}"
        elif self.block_type in ("local", "output", "variable"):
            reference = f"{prefix}{self.id}"
        else:
            raise TypeError(
                f"Cannot produced wrapped reference for block_type={self.block_type}"
            )

        if attr:
            reference = f"{reference}.{attr}"

        if wrap:
            return f"${{{reference}}}"
        else:
            return reference


class TerraformResource(TerraformBlock):
    block_type = "resource"


class TerraformLocal(TerraformBlock):
    block_type = "locals"

    def set_local(self, name, value):
        self.root.locals.setdefault(name, value)

    def body(self):
        if self.config:
            config = self.config
            name = config.get("name", self.id)
            value = config.get("value", None)
            if value:
                self.set_local(name, value)


class TerraformData(TerraformBlock):
    block_type = "data"

    def body(self):
        config = self.config
        name = config.get("name", self.id)
        value = config.get("value")
        self.root.data.setdefault(name, value)


class TerraformProvider(TerraformBlock):
    block_type = "provider"

    def add(self, name, value):
        self.root.setdefault(self.block_type, {}).setdefault(name, value)[name] = value

    def set(self, config=None):
        if config is None:
            config = self.config
        self.root.setdefault(self.block_type, {}).setdefault(self.id, config).update(
            config
        )
