#!/bin/bash
{% set p = inventory.parameters %}
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
{% if p.use_tesoro | default(false)%}
apply () {
  FILEPATH=${1?}
  ${DIR}/kubectl.sh apply --recursive -f "${FILEPATH}"
}
{% else %}
apply () {
  FILEPATH=${1?}
  ${KAPITAN} refs --reveal -f "${FILEPATH}" | ${DIR}/kubectl.sh apply -f -
}
{% endif %}




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

  if [[ -f ${DIR}/../manifests/{{p.namespace}}-namespace.yml ]]
  then
    apply "${DIR}/../manifests/{{p.namespace}}-namespace.yml"
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

