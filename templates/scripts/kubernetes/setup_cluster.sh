#!/bin/bash
set -o nounset -o pipefail -o noclobber -o errexit
GCLOUD="gcloud"

{% set p = inventory.parameters %}

{% set cluster = p.cluster %}
{% if cluster.type == "gke" %}
${GCLOUD} container clusters get-credentials {{cluster.name}} --zone {{cluster.zone}} --project {{cluster.google_project}}
{% endif %}
