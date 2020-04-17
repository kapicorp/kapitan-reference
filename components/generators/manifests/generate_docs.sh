#!/bin/bash
DIR=$(dirname ${BASH_SOURCE[0]})
pushd $DIR
jsonnet schema.libjsonnet > schema.json
bootprint json-schema schema.json target
popd
