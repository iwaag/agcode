#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE_NAME="${LOCAL_IMAGE_NAME_CODER_PRO:-agcode/coder-pro:dev}"
BUILD_ID="${WORKER_BUILD_ID:-$(date +%Y%m%d%H%M%S)}"
ENV_FILE="${ROOT_DIR}/.local/worker_local.env"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing required command: $1" >&2
    exit 1
  fi
}

require_cmd docker
require_cmd microk8s

microk8s status --wait-ready >/dev/null

echo "Building ${IMAGE_NAME}"
docker build \
  -f "${ROOT_DIR}/deploy/docker/worker-pro.Dockerfile" \
  -t "${IMAGE_NAME}" \
  "${ROOT_DIR}"

echo "Importing ${IMAGE_NAME} into microk8s"
docker save "${IMAGE_NAME}" | microk8s ctr image import -

mkdir -p "$(dirname "${ENV_FILE}")"
cat > "${ENV_FILE}" <<EOF
export SESSION_RUNTIME_MODE=local_microk8s
export LOCAL_IMAGE_NAME_CODER_PRO=${IMAGE_NAME}
export WORKER_BUILD_ID=${BUILD_ID}
export SESSION_REMOTE_CONFIG_PATH=${ROOT_DIR}/deploy/k8s/remote-config.yaml
EOF

echo "Wrote ${ENV_FILE}"
echo "Build ID: ${BUILD_ID}"
echo "Run: source ${ENV_FILE}"
