import contextvars
import functools
import logging
from enum import Enum
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
    current_target,
    inventory_global,
)
from kapitan.utils import render_jinja2_file

logger = logging.getLogger(__name__)

search_paths = args.get("search_paths")
registered_generators = contextvars.ContextVar(
    "current registered_generators in thread", default={}
)

target = current_target.get()


@functools.lru_cache
def load_generators(name, path):
    from importlib import import_module
    from inspect import isclass
    from pathlib import Path
    from pkgutil import iter_modules

    # iterate through the modules in the current package
    package_dir = Path(path).resolve().parent
    for _, module_name, _ in iter_modules([package_dir]):
        # import the module and iterate through its attributes
        module = import_module(f"{name}.{module_name}")
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)

            if isclass(attribute):
                # Add the class to this package's variables
                globals()[attribute_name] = attribute


class DeleteContent(Exception):
    # Raised when a content should be deleted
    pass


def patch_config(config: Dict, inventory: Dict, inventory_path: str) -> None:
    """Apply patch to config"""
    patch = findpath(inventory, inventory_path, {})
    logger.debug(f"Applying patch {inventory_path} : {patch}")
    merge(patch, config)


def register_function(func, params):
    target = current_target.get()
    logger.debug(
        f"Registering generator {func.__name__} with params {params} for target {target}"
    )

    my_dict = registered_generators.get()
    generator_list = my_dict.get(target, [])
    generator_list.append((func, params))

    logger.debug(
        f"Currently registered {len(generator_list)} generators for target {target}"
    )

    my_dict[target] = generator_list

    registered_generators.set(my_dict)


def merge(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.get(key, None)
            if node is None:
                destination[key] = value
            elif len(node) == 0:
                # node is set to an empty dict on purpose as a way to override the value
                pass
            else:
                merge(value, node)
        else:
            destination[key] = destination.setdefault(key, value)

    return destination


def render_jinja(filename, ctx):
    return render_jinja2_file(filename, ctx, search_paths=search_paths)


def findpaths_by_property(obj: dict, property: str) -> dict:
    """
    Traverses the whole dictionary looking of objects containing a given property.

    Args:
        obj: the dictionary to scan for a given property
        property: the key to look for in a dictionary

    Returns:
        A dictionary with found objects. Keys in the dictionary are the "name" properties of these objects.
    """
    res = {}
    for k, v in obj.items():
        if k == property:
            res[obj["name"]] = obj
        if isinstance(v, dict):
            sub_results = findpaths_by_property(v, property)
            res = {**res, **sub_results}
    return res


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
    except AttributeError as e:
        if value is not None:
            return value
        logging.info(f"Attribute {e} not found in {obj}: ignoring")

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
    filename: str = None

    def body(self):
        pass

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
                        raise DeleteContent(f"Deleting {self} because of {condition}")
            if action == "bundle":
                for condition in conditions:
                    if self.match(condition["conditions"]):
                        if self.filename is None:
                            try:
                                self.filename = condition["filename"].format(
                                    content=self
                                )
                            except (AttributeError, KeyError):
                                pass
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
        self.root.merge_update(Dict(patch), box_merge_lists="extend")


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
        logger.debug(f"Adding {type(object)} to store")
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
            except DeleteContent as e:
                logger.debug(e)
                self.content_list.remove(content)
            except:
                raise CompileError(f"Error when processing mutations on {content}")

    def get_content_list(self):
        return getattr(self, "content_list", [])

    def dump(self, output_filename=None, already_processed=False):
        """Return object dict/list."""
        logger.debug(f"Dumping {len(self.get_content_list())} items")
        if not already_processed:
            for content in self.get_content_list():
                if output_filename:
                    output_format = output_filename
                else:
                    output_format = getattr(content, "filename", "output")
                    if output_format is None:
                        output_format = "output"

                filename = output_format.format(content=content)
                file_content_list = self.root.get(filename, [])
                if content in file_content_list:
                    logger.debug(
                        f"Skipping duplicated content content for reason 'Duplicate name {content.name} for {filename}'"
                    )
                    continue

                self.root.setdefault(filename, []).append(content)

        return super().dump()


class BaseGenerator:
    def __init__(
        self,
        inventory: Dict,
        store: BaseStore = None,
        defaults_path: str = None,
    ) -> None:
        self.inventory = inventory
        self.global_inventory = inventory_global()
        self.generator_defaults = findpath(self.inventory, defaults_path)
        logger.debug(f"Setting {self.generator_defaults} as generator defaults")

        if store == None:
            self.store = BaseStore()
        else:
            self.store = store()

    def expand_and_run(self, func, params, inventory=None):
        if inventory == None:
            inventory = self.inventory

        path = params.get("path")
        activation_property = params.get("activation_property")
        patches = params.get("apply_patches", [])
        if path is not None:
            configs = findpath(inventory.parameters, path)
        elif activation_property is not None:
            configs = findpaths_by_property(inventory.parameters, activation_property)
        else:
            raise CompileError(
                f"generator need to provide either 'path' or 'activation_property'"
            )

        if configs:
            logger.debug(
                f"Found {len(configs)} configs to generate at {path} for target {target}"
            )
        for config_id, config in configs.items():
            patched_config = Dict(config)
            patch_paths_to_apply = patches
            patches_applied = []
            for path in patch_paths_to_apply:
                try:
                    path = path.format(**patched_config)
                except KeyError:
                    # Silently ignore missing keys
                    continue
                patch = findpath(inventory.parameters, path, {})
                patches_applied.append(patch)

                patched_config = merge(patch, patched_config)

            local_params = {
                "id": config_id,
                "name": patched_config.get("name", config_id),
                "config": patched_config,
                "patches_applied": patches_applied,
                "original_config": config,
                "defaults": self.generator_defaults,
                "inventory": inventory,
                "global_inventory": self.global_inventory,
                "target": current_target.get(),
            }
            logger.debug(
                f"Running class {func.__name__} for {config_id} with params {local_params.keys()}"
            )
            self.store.add(func(**local_params))

    def generate(self):
        generators = registered_generators.get().get(target, [])
        logger.debug(
            f"{len(generators)} classes registered as generators for target {target}"
        )
        for func, params in generators:
            activation_path = params.get("activation_path", False)
            global_generator = params.get("global_generator", False)
            if activation_path and global_generator:
                logger.debug(
                    f"Running global generator {func.__name__} with activation path {activation_path}"
                )
                if not findpath(self.inventory.parameters, activation_path):
                    logger.debug(
                        f"Skipping global generator {func.__name__} with params {params}"
                    )
                    continue
                else:
                    logger.debug(
                        f"Running global generator {func.__name__} with params {params}"
                    )

                    for _, inventory in self.global_inventory.items():
                        self.expand_and_run(
                            func=func, params=params, inventory=inventory
                        )
            elif not global_generator:
                logger.debug(f"Expanding {func.__name__} with params {params}")
                self.expand_and_run(func=func, params=params)
            else:
                logger.debug(
                    f"Skipping generator {func.__name__} with params {params} because not global and no activation path"
                )
        return self.store
