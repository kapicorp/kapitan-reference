#!/bin/bash -e

TARGET=gke-pvm-killer


DIR=$(dirname ${BASH_SOURCE[0]})
ROOT=$(cd "${DIR}"; git rev-parse --show-toplevel)
KAPITAN_COMMAND=${ROOT}/kapitan

echo "Generating secret for gke-pvm-killer@example-gce-project.iam.gserviceaccount.com"
gcloud --project example-gce-project iam service-accounts keys \
create - \
--iam-account=gke-pvm-killer@example-gce-project.iam.gserviceaccount.com | ${KAPITAN_COMMAND} refs --write plain:targets/gke-pvm-killer/gke-pvm-killer-service-account --base64 -f - -t ${TARGET}

echo "Summary of available keys (please remove obsolete ones after deploying changes)"

gcloud --project example-gce-project iam service-accounts keys \
list --iam-account=gke-pvm-killer@example-gce-project.iam.gserviceaccount.com

#####
