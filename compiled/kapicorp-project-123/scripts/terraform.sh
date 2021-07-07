#!/bin/bash

set -e           # If a command fails, the whole script exit
set -u           # Treat unset variables as an error, and immediately exit.
set -o pipefail  # this will make your script exit if any command in a pipeline errors


DIR=$(realpath $(dirname ${BASH_SOURCE[0]}))
ROOT=$(cd "${DIR}"; git rev-parse --show-toplevel)
TARGET_NAME=kapicorp-project-123
GCP_PROJECT=kapicorp-project-123

########################################################################################
# Check required binaries are installed

error(){
  echo "${@}"
}

check_installed() {
  CMD=$1
  if ! $(which ${CMD} > /dev/null); then
      error "${CMD} not installed. Exiting..."
  fi
}

check_installed terraform

########################################################################################
# Variables
export DIR=$(realpath $(dirname ${BASH_SOURCE[0]}))                      # Folder where this script is
export TF_DIR=$(realpath ${DIR}/../terraform)                            # Folder where TF files are
export TF_DATA_DIR=$(realpath -m ${DIR}/../../../.TF_DATA_DIR/${GCP_PROJECT}) # Folder for TF initialization (preferable outside of compiled)
export OUTPUT_DIR=$(realpath -m ${DIR}/../../../output/${GCP_PROJECT}) # Folder for storing output files (preferable outside of compiled)
export TERRAFORM="terraform"
DEBUG=${DEBUG:-0}

########################################################################################
# MAIN

if [ $DEBUG -ne 0 ]; then
    debug
fi

pushd $TF_DIR &> /dev/null

terraform "$@"

if [[ -f $ROOT/compiled/${TARGET_NAME}/terraform/.terraform.lock.hcl ]]
then
  mkdir -p $ROOT/resources/state/${TARGET_NAME}/
  cp $ROOT/compiled/${TARGET_NAME}/terraform/.terraform.lock.hcl \
    $ROOT/resources/state/${TARGET_NAME}/.terraform.lock.hcl
fi