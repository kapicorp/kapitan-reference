#!/bin/bash -e
set -o nounset
set -o errexit
set -o pipefail

GITHUB_BOT=kapitanbot

if [[ -z "${GITHUB_ACCESS}" || -z "${TAG}" || -z "${REPO}" ]]; then
  echo 'One or more variables are undefined, skipping'
  exit 0
fi

set_tag() {
  curl  -u ${GITHUB_BOT}:"${GITHUB_ACCESS}" \
      --write-out "%{http_code}" --silent --output /dev/null \
      -X POST -H 'Content-Type: application/json' \
      "https://api.github.com/repos/${REPO}/git/refs" -d"{ \"ref\": \"refs/tags/${TAG}\", \"sha\": \"${COMMIT_SHA}\" }"
}

delete_tag() {
  curl -u ${GITHUB_BOT}:"${GITHUB_ACCESS}" \
      --write-out "%{http_code}" --silent --output /dev/null \
      -X DELETE "https://api.github.com/repos/${REPO}/git/refs/tags/${TAG}"
}

if [[ -n "${COMMIT_SHA}" ]]
then
  echo "Setting ${TAG} to ${COMMIT_SHA} on ${REPO}"
  error_code=$(set_tag)
  if [[ $error_code -eq 422 ]]
  then
    echo -n "Tag exists, deleting (204 is OK): "
    delete_tag
    echo ""
    error_code=$(set_tag)
    echo "Setting Tag (201 is OK): ${error_code}"
  else
    echo "Setting Tag (201 is OK): ${error_code}"
  fi
else
  echo "COMMIT_SHA is not set, skipping"
  exit 0
fi

if [[ $error_code -ne 201 ]]
then
  exit 1
fi
