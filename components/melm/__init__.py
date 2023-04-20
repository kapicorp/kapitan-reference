import os

from kapitan.inputs.kadet import BaseModel, load_from_search_paths

kgenlib = load_from_search_paths("generators")


def main(input_params):
    """Component main."""

    chart_dir = input_params["chart_dir"]
    helm_params = input_params.get("helm_params", {})
    helm_values = input_params.get("helm_values", {})

    mutations = input_params.get("mutations", {})

    output_file = helm_params.get("output_file", None)
    if output_file:
        output_file = os.path.splitext(os.path.basename(output_file))[0]

    store = kgenlib.BaseStore()
    helm_config = {
        "chart_dir": chart_dir,
        "helm_params": helm_params,
        "helm_values": helm_values,
    }
    store.import_from_helm_chart(**helm_config)
    store.process_mutations(mutations)

    return store.dump(output_filename=output_file)
