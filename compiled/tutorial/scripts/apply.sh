#!/bin/bash
DIR=$(dirname ${BASH_SOURCE[0]})
ROOT=$(cd "${DIR}"; git rev-parse --show-toplevel)/
KAPITAN="${ROOT}/kapitan"

FILE=${1:-}

# Only GNU xargs supports --no-run-if-empty
XARGS="xargs --no-run-if-empty"
if ! echo | $XARGS 2>/dev/null; then
  # Looks like we have BSD xargs, use -x instead
  XARGS="xargs"
fi

## if tesoro is enabled, no need to reveal
apply () {
  FILEPATH=${1?}
  ${DIR}/kubectl.sh apply --recursive -f "${FILEPATH}"
}




if [[ ! -z $FILE ]]
then
  # Apply files passed at the command line
  for FILEPATH in "$@"
  do
    [[ -e ${FILEPATH} ]] || ( echo Invalid file ${FILEPATH} && exit 1 )
    echo "## run kubectl apply for ${FILEPATH}"
    apply "${FILEPATH}"
  done
else

  if [[ -f ${DIR}/../pre-deploy/01_namespace.yml ]]
  then
    apply "${DIR}/../pre-deploy/01_namespace.yml"
  fi

  # Apply files in specific order
  for SECTION in pre-deploy manifests
  do
    echo "## run kubectl apply for ${SECTION}"
    DEPLOY_PATH=${DIR}/../${SECTION}
    if [[ -d ${DEPLOY_PATH} ]]
    then
      apply "${DEPLOY_PATH}"
    fi
  done
fi
