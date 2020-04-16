#!/bin/bash -e

TARGET=postgres-proxy


DIR=$(dirname ${BASH_SOURCE[0]})
ROOT=$(cd "${DIR}"; git rev-parse --show-toplevel)
KAPITAN_COMMAND=${ROOT}/kapitan

echo "Generating secret for postgres-proxy@example-project.iam.gserviceaccount.com"
gcloud --project example-project iam service-accounts keys \
create - \
--iam-account=postgres-proxy@example-project.iam.gserviceaccount.com | ${KAPITAN_COMMAND} refs --write plain:targets/postgres-proxy/postgres-proxy-service-account --base64 -f - -t ${TARGET}

echo "Summary of available keys (please remove obsolete ones after deploying changes)"

gcloud --project example-project iam service-accounts keys \
list --iam-account=postgres-proxy@example-project.iam.gserviceaccount.com

#####
