#!/bin/bash
set -e

SCRIPT_TMP_DIR="$(mktemp -d /tmp/kapitan.XXXXXXXXXX)"
trap "rm -fr '${SCRIPT_TMP_DIR}'" INT TERM EXIT

NAMESPACE=tesoro
TARGET_NAME=tesoro

# Generates new certificates
CACERT_KEY=rootCA.key
CACERT_PEM=rootCA.crt
CERT_KEY=priv.key
CERT_PEM=cert.pem
CN=tesoro.${NAMESPACE}.svc

pushd ${SCRIPT_TMP_DIR}
openssl genrsa -out ${CACERT_KEY} 4096 > /dev/null
openssl req -x509 -new -nodes -key ${CACERT_KEY} -subj "/CN=CA-${CN}" -sha256 -days 1024 -out ${CACERT_PEM} > /dev/null


openssl genrsa -out ${CERT_KEY} 2048 > /dev/null
openssl req -new -sha256 -key ${CERT_KEY} -subj "/CN=${CN}" -out csr.csr >/dev/null
openssl x509 -req -in csr.csr -CA ${CACERT_PEM} -extfile <(printf "subjectAltName=DNS:${CN}")  -CAkey ${CACERT_KEY} -CAcreateserial -out ${CERT_PEM} -days 500 -sha256 > /dev/null
openssl x509 -in ${CERT_PEM} -noout
popd
kapitan refs -t tesoro --write plain:targets/tesoro/kapicorp-tesoro-cert-pem --base64 -f ${SCRIPT_TMP_DIR}/${CERT_PEM}
kapitan refs -t tesoro --write plain:targets/tesoro/kapicorp-tesoro-cert-key --base64 -f ${SCRIPT_TMP_DIR}/${CERT_KEY}
kapitan refs -t tesoro --write plain:targets/tesoro/kapicorp-tesoro-cacert-pem --base64 -f ${SCRIPT_TMP_DIR}/${CACERT_PEM}