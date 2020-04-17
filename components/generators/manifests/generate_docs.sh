#!/bin/bash
DIR=$(dirname ${BASH_SOURCE[0]})
pushd $DIR
jsonnet schema.libjsonnet > schema.json
generate-schema-doc schema.json
popd
