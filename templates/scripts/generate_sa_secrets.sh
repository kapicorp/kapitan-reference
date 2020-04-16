#!/bin/bash -e

{% set i = inventory.parameters %}
TARGET={{i.target_name}}


DIR=$(dirname ${BASH_SOURCE[0]})
ROOT=$(cd "${DIR}"; git rev-parse --show-toplevel)
KAPITAN_COMMAND=${ROOT}/kapitan

{% for sa_key in i.service_accounts %}
{% set sa = i.service_accounts[sa_key] %}
echo "Generating secret for {{sa.name}}"
gcloud --project {{i.google_project}} iam service-accounts keys \
create - \
--iam-account={{sa.name}} | ${KAPITAN_COMMAND} refs --write {{sa.ref}} --base64 -f - -t ${TARGET}

echo "Summary of available keys (please remove obsolete ones after deploying changes)"

gcloud --project {{i.google_project}} iam service-accounts keys \
list --iam-account={{sa.name}}

#####
{% endfor %}
