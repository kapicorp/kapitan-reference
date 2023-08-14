import logging

logger = logging.getLogger(__name__)

from kapitan.inputs.kadet import inventory

from .argocd import *
from .base import *
from .certmanager import *
from .common import kgenlib
from .gke import *
from .helm import *
from .istio import *
from .networking import *
from .prometheus import *
from .rbac import *
from .storage import *
from .workloads import *

inv = inventory(lazy=True)


def main(input_params):
    generator = kgenlib.BaseGenerator(inventory=inv)
    store = generator.generate()
    store.process_mutations(input_params.get("mutations", {}))

    return store.dump()
