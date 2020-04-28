#!/bin/bash
set -o nounset -o pipefail -o noclobber -o errexit

{% set p = inventory.parameters %}

{% set cluster = p.cluster %}
{% if cluster.type == "gke" %}
GCLOUD="gcloud"
${GCLOUD} container clusters get-credentials {{cluster.name}} --zone {{cluster.zone}} --project {{cluster.google_project}}
{% elif cluster.type == "kind" %}
KIND="kind"
$KIND create cluster -q --name {{cluster.name}} || echo "Kind cluster {{cluster.name}} already exists!"
$KIND export kubeconfig
{% endif %}
