import contextvars
import functools
import logging
from enum import Enum
from types import FunctionType
from typing import List

import yaml
from box.exceptions import BoxValueError
from kapitan.cached import args
from kapitan.inputs.helm import HelmChart
from kapitan.inputs.kadet import BaseModel, BaseObj, CompileError, Dict, current_target
from kapitan.utils import render_jinja2_file

logger = logging.getLogger(__name__)

search_paths = args.get("search_paths")
registered_generators = contextvars.ContextVar(
    "current registered_generators in thread"
)

target = current_target.get()
registered_generators.set({})


def register_function(func, params):
    logging.debug(
        f"Registering generator {func.__name__} with params {params} for target {target}"
    )
    my_dict = registered_generators.get()
    my_dict.setdefault(target, []).append((func, params))
    registered_generators.set(my_dict)


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


def findpath(obj, path, default={}):
    value = default
    if path:
        path_parts = path.split(".")
    else:
        return value

    try:
        value = getattr(obj, path_parts[0])
    except KeyError as e:
        if value is not None:
            return value
        logging.info(f"Key {e} not found in {obj}: ignoring")

    if len(path_parts) == 1:
        return value
    else:
        return findpath(value, ".".join(path_parts[1:]))


def register_generator(*args, **kwargs):
    def wrapper(func):
        register_function(func, kwargs)

        def wrapped_func():
            return func

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
        """Return a BaseContent initialised with dict_value."""

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

    def dump(self, output_filename=None, already_processed=False):
        """Return object dict/list."""
        logging.debug(f"Dumping {len(self.get_content_list())} items")
        if not already_processed:
            for content in self.get_content_list():
                if output_filename:
                    output_format = output_filename
                else:
                    output_format = getattr(content, "filename", "output")

                filename = output_format.format(content=content)
                self.root.setdefault(filename, []).append(content)

        return super().dump()


class BaseGenerator:
    def __init__(
        self, inventory: Dict, store: BaseStore = None, defaults_path: str = None
    ) -> None:
        self.inventory = inventory
        self.generator_defaults = findpath(self.inventory, defaults_path)
        logging.debug(f"Setting {self.generator_defaults} as generator defaults")

        if store == None:
            self.store = BaseStore()
        else:
            self.store = store()

    def expand_and_run(self, func, params):
        inventory = self.inventory
        path = params.get("path")
        patches = params.get("apply_patches", [])
        configs = findpath(inventory.parameters, path)
        if configs:
            logging.debug(
                f"Found {len(configs)} configs to generate at {path} for target {target}"
            )

        for name, config in configs.items():
            patched_config = Dict(config)
            patch_paths_to_apply = patches
            patches_applied = []
            for path in patch_paths_to_apply:
                try:
                    path = path.format(**config)
                except KeyError:
                    # Silently ignore missing keys
                    continue
                patch = findpath(inventory.parameters, path, {})
                patches_applied.append(patch)

                patched_config = merge(patch, patched_config)

            local_params = {
                "name": name,
                "config": patched_config,
                "patches_applied": patches_applied,
                "original_config": config,
                "defaults": self.generator_defaults,
            }
            logging.debug(
                f"Running class {func.__name__} with params {local_params.keys()} and name {name}"
            )
            self.store.add(func(**local_params))

    def generate(self):
        generators = registered_generators.get().get(target, [])
        logging.debug(
            f"{len(generators)} classes registered as generators for target {target}"
        )
        for func, params in generators:

            logging.debug(f"Expanding {func.__name__} with params {params}")
            self.expand_and_run(func=func, params=params)
        return self.store
