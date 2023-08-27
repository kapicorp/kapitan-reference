import logging

from kapitan.inputs.kadet import inventory

from .common import TerraformStore, kgenlib

kgenlib.load_generators(__name__, __file__)

logger = logging.getLogger(__name__)


def main(input_params):
    target_inventory = inventory()

    defaults_path = "parameters.generators.terraform.defaults"
    generator = kgenlib.BaseGenerator(
        inventory=target_inventory, store=TerraformStore, defaults_path=defaults_path
    )

    store = generator.generate()

    # mutations are currently not supported for terraform
    mutations = input_params.get("mutations", {})
    store.process_mutations(mutations)

    return store.dump()
