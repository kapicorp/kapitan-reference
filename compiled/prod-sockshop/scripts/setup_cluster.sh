#!/bin/bash
set -o nounset -o pipefail -o noclobber -o errexit


GCLOUD="gcloud"
${GCLOUD} container clusters get-credentials demo --zone europe-west1-b --project kapitan-demo
