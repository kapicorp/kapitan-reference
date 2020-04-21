#!/bin/bash
DIR=$(dirname ${BASH_SOURCE[0]})
pushd $DIR
jsonnet schemas.libsonnet -m .
bootprint json-schema service_component target
popd
