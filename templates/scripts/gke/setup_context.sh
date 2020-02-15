#!/bin/bash
set -o nounset -o pipefail -o noclobber -o errexit
KUBECTL="kubectl"

{% set p = inventory.parameters %}

{% set cluster = p.cluster %}
{% if cluster.type == "gke" %}
${KUBECTL} config set-context {{p.target_name}}-{{cluster.name}} --cluster {{cluster.id}} --user {{cluster.user}} --namespace {{p.namespace}}
{% endif %}
