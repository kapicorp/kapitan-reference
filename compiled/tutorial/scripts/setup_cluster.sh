#!/bin/bash
set -o nounset -o pipefail -o noclobber -o errexit


KIND="kind"
$KIND create cluster -q --name kind || echo "Kind cluster kind already exists!"
$KIND export kubeconfig
