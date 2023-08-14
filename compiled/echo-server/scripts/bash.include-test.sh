source $(dirname ${BASH_SOURCE[0]})/bash.include
set -o nounset +o pipefail +o noclobber +o errexit


testTargetName() {
  assertEquals ${TARGET_NAME} "echo-server"
}

testTargetPath() {
  assertEquals ${TARGET_PATH} "echo-server"
}

testKapitanFound() {
  assertTrue "kapitan found at ${KAPITAN_COMMAND}" "[ -r ${KAPITAN_COMMAND} ]"
}

testKapitanBaseDir() {
  assertTrue "[ -r ${KAPITAN_BASEDIR_RELATIVE_PATH_FROM_PWD} ]"
}

testTargetBaseDir() {
  assertTrue "[ -r ${KAPITAN_BASEDIR_RELATIVE_PATH_FROM_PWD}/compiled/${TARGET_PATH} ]"
}

# TODO(ademaria) understand why this doesn'
# testCreateRef() {
#   NAME=$(echo $RANDOM | md5sum | head -c 20)
#   EXPECTED_REF=${KAPITAN_BASEDIR_RELATIVE_PATH_FROM_PWD}/refs/targets/${TARGET_PATH}/${NAME}
#   echo "TEST" | set_reference_name ${NAME}
#   assertTrue "[ -r  ${EXPECTED_REF} ]"
# }


# Load shUnit2.
. ${KAPITAN_BASEDIR_RELATIVE_PATH_FROM_PWD}/system/scripts/shunit2