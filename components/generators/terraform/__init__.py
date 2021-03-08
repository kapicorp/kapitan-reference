from kapitan.inputs.kadet import BaseObj, inventory

inv = inventory()


def main(input_params):
    obj = BaseObj()
    generator_root_paths = input_params.get("generator_root", "resources.tf").split(".")
    root = inv.parameters

    for path in generator_root_paths:
        root = root.get(path, {})

    for resource_name, content in root.items():
        obj.root["{}.tf".format(resource_name)][resource_name] = content
    return obj
