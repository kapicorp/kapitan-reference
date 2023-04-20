import functools
import logging
from enum import Enum
from types import FunctionType
from typing import List

import yaml
from box.exceptions import BoxValueError
from kapitan.cached import args
from kapitan.inputs.helm import HelmChart
from kapitan.inputs.kadet import (
    BaseModel,
    BaseObj,
    CompileError,
    Dict,
    inventory,
    inventory_global,
)
from kapitan.utils import render_jinja2_file

logger = logging.getLogger(__name__)
inventory = inventory(lazy=True)
inventory_global = inventory_global(lazy=True)

search_paths = args.get("search_paths")


class BaseGenerator:
    inventory: Dict
    functions: List[FunctionType] = []

    @classmethod
    def run(cls, output):
        store = BaseStore()
        if isinstance(output, BaseStore):
            store.add(output)
        elif isinstance(output, BaseContent):
            store.add(output)

        else:
            raise CompileError(f"Unknown output type {output.__class__.__name__}")
        return store

    @classmethod
    def generate(cls):
        store = BaseStore()
        logging.debug(f"{len(cls.functions)} functions registered as generators")
        for func in cls.functions:
            store.add(cls.run(func()))
        return store

    @classmethod
    def register_function(cls, func):
        cls.functions.append(func)


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


def render_jinja(filename, ctx):
    return render_jinja2_file(filename, ctx, search_paths=search_paths)


def findpath(obj, path, default=None):
    path_parts = path.split(".")
    try:
        value = getattr(obj, path_parts[0])
    except KeyError as e:
        if default is not None:
            return default
        raise CompileError(f"Key {e} not found in {obj}")

    if len(path_parts) == 1:
        return value
    else:
        return findpath(value, ".".join(path_parts[1:]))


def register_generator(*args, **kwargs):
    def wrapper(func):
        @functools.wraps(func)
        def wrapped_func():
            path = kwargs.get("path")
            configs = findpath(inventory.parameters, path)

            store = BaseStore()
            for name, config in configs.items():
                patched_config = Dict(config)
                apply_patches_paths = kwargs.get("apply_patches", [])
                patches_applied = []
                for path in apply_patches_paths:
                    try:
                        path = path.format(**config)
                    except KeyError:
                        # Silently ignore missing keys
                        continue
                    patch = findpath(inventory.parameters, path, {})
                    patches_applied.append(patch)

                    patched_config = merge(patch, patched_config)

                store.add(
                    BaseGenerator.run(
                        func(
                            name=name,
                            config=patched_config,
                            patches_applied=patches_applied,
                            original_config=config,
                        )
                    )
                )
            return store

        BaseGenerator.register_function(wrapped_func)
        return wrapped_func

    return wrapper


class ContentType(Enum):
    YAML = 1
    KUBERNETES_RESOURCE = 2
    TERRAFORM_BLOCK = 3


class BaseContent(BaseModel):
    content_type: ContentType = ContentType.YAML
    filename: str = "output"

    @classmethod
    def from_baseobj(cls, baseobj: BaseObj):
        """Return a BaseContent initialised with baseobj."""
        return cls.from_dict(baseobj.root)

    @classmethod
    def from_yaml(cls, file_path) -> List:
        """Returns a list of BaseContent initialised with the content of file_path data."""

        content_list = list()
        with open(file_path) as fp:
            yaml_objs = yaml.safe_load_all(fp)
            for yaml_obj in yaml_objs:
                if yaml_obj:
                    content_list.append(BaseContent.from_dict(yaml_obj))

        return content_list

    @classmethod
    def from_dict(cls, dict_value):
        """Return a KubernetesResource initialise with dict_value."""

        if dict_value:
            try:
                obj = cls()
                obj.parse(Dict(dict_value))
                return obj
            except BoxValueError as e:
                raise CompileError(
                    f"error when importing item '{dict_value}' of type {type(dict_value)}: {e}"
                )

    def parse(self, content: Dict):
        self.root = content

    @staticmethod
    def findpath(obj, path):
        path_parts = path.split(".")
        value = getattr(obj, path_parts[0])
        if len(path_parts) == 1:
            return value
        else:
            return BaseContent.findpath(value, ".".join(path_parts[1:]))

    def mutate(self, mutations: List):
        for action, conditions in mutations.items():
            if action == "patch":
                for condition in conditions:
                    if self.match(condition["conditions"]):
                        self.patch(condition["patch"])
            if action == "delete":
                for condition in conditions:
                    if self.match(condition["conditions"]):
                        self = None
            if action == "bundle":
                for condition in conditions:
                    if self.match(condition["conditions"]):
                        self.filename = condition["filename"].format(content=self)
                        if condition.get("break", True):
                            break

    def match(self, match_conditions):
        for key, values in match_conditions.items():
            if "*" in values:
                return True
            value = self.findpath(self.root, key)
            if value in values:
                continue
            else:
                return False
        return True

    def patch(self, patch):
        self.root.merge_update(Dict(patch))


class BaseStore(BaseModel):
    content_list: List[BaseContent] = []

    @classmethod
    def from_yaml_file(cls, file_path):
        store = cls()
        with open(file_path) as fp:
            yaml_objs = yaml.safe_load_all(fp)
            for yaml_obj in yaml_objs:
                if yaml_obj:
                    store.add(BaseContent.from_dict(yaml_obj))
        return store

    def add(self, object):
        logging.debug(f"Adding {type(object)} to store")
        if isinstance(object, BaseContent):
            self.content_list.append(object)
        elif isinstance(object, BaseStore):
            self.content_list.extend(object.content_list)

        elif isinstance(object, list):
            for item in object:
                if isinstance(item, BaseObj):
                    self.add(BaseContent.from_baseobj(item))
                else:
                    self.add_list(item)

        elif isinstance(object, BaseObj):
            self.add(BaseContent.from_baseobj(object))

        else:
            self.content_list.append(object)

    def add_list(self, contents: List[BaseContent]):
        for content in contents:
            self.add(content)

    def import_from_helm_chart(self, **kwargs):
        self.add_list(
            [
                BaseContent.from_baseobj(resource)
                for resource in HelmChart(**kwargs).root.values()
            ]
        )

    def apply_patch(self, patch: Dict):
        for content in self.get_content_list():
            content.patch(patch)

    def process_mutations(self, mutations: Dict):
        for content in self.get_content_list():
            try:
                content.mutate(mutations)
            except:
                raise CompileError(f"Error when processing mutations on {content}")

    def get_content_list(self):
        return self.content_list

    def dump(self, output_filename=None):
        """Return object dict/list."""
        logging.debug(f"Dumping {len(self.get_content_list())} items")
        for content in self.get_content_list():
            if output_filename:
                output_format = output_filename
            else:
                output_format = getattr(content, "filename", "output")

            filename = output_format.format(content=content)
            self.root.setdefault(filename, []).append(content)

        return super().dump()


class KubernetesGenerator(BaseStore):
    name: str
    config: Dict
