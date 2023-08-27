import logging

logger = logging.getLogger(__name__)

from kapitan.inputs.kadet import inventory

from .common import kgenlib

# Loads generators dynamically
kgenlib.load_generators(__name__, __file__)


def main(input_params):
    target_inventory = inventory(lazy=True)
    generator = kgenlib.BaseGenerator(inventory=target_inventory)
    store = generator.generate()
    store.process_mutations(input_params.get("mutations", {}))

    return store.dump()
