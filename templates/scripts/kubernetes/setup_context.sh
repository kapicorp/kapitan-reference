#!/bin/bash
set -o nounset -o pipefail -o noclobber -o errexit
KUBECTL="kubectl"

{% set p = inventory.parameters %}

{% set cluster = p.cluster %}
${KUBECTL} config set-context {{cluster.name}} --cluster {{cluster.id}} --user {{cluster.user}} --namespace {{p.namespace}}
