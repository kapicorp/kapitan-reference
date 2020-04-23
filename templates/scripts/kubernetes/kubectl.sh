#!/bin/bash
DIR=$(dirname ${BASH_SOURCE[0]})
${DIR}/setup_context.sh >/dev/null
if [[ -p /dev/stdin ]]
then
    INPUT=$( cat )
fi
{% set i = inventory.parameters %}
KUBECTL="kubectl --context {{i.target_name}}"
echo "${INPUT}" | ${KUBECTL} "$@"
