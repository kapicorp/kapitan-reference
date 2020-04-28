#!/bin/bash
set -o nounset -o pipefail -o noclobber -o errexit
KUBECTL="kubectl"


${KUBECTL} config set-context tutorial --cluster kind-kind --user kind-kind --namespace tutorial
