#!/bin/bash
set -o nounset -o pipefail -o noclobber -o errexit
KUBECTL="kubectl"


${KUBECTL} config set-context prod-sockshop --cluster gke_kapitan-demo_europe-west1-b_demo --user gke_kapitan-demo_europe-west1-b_demo --namespace prod-sockshop
