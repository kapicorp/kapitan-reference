#!/bin/bash
DIR=$(dirname ${BASH_SOURCE[0]})
${DIR}/setup_context.sh >/dev/null
if [[ -p /dev/stdin ]]
then
    INPUT=$( cat )
fi
KUBECTL="kubectl --context prod-sockshop"
echo "${INPUT}" | ${KUBECTL} "$@"