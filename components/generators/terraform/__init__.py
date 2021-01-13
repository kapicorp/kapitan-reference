from kapitan.inputs.kadet import BaseObj, inventory

inv = inventory()


def main(input_params):
    obj = BaseObj()
    for resource_name, content in inv.parameters.kapicorp.items():
        obj.root["{}.tf".format(resource_name)][resource_name] = content
    return obj
