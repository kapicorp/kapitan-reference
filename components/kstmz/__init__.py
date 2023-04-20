import os

from kapitan.inputs.kadet import BaseModel, load_from_search_paths

kgenlib = load_from_search_paths("generators")


def main(input_params):
    """kstmz allows you to patch yaml files

    Args:
        input_params (dict): {input_file, output_file, mutations}

    Returns:
        BaseModel: the resulting files to render
    """

    store = kgenlib.BaseStore()

    input_files = input_params["files"]
    output_file = input_params.get("output_file")

    for file in input_files:
        store.add(kgenlib.BaseStore.from_yaml_file(file))

    mutations = input_params.get("mutations", {})
    store.process_mutations(mutations)
    return store.dump(output_filename=output_file)
