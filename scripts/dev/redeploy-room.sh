#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <room_id>" >&2
  exit 1
fi

ROOM_ID="$1"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
AUTH_TOKEN="${AUTH_TOKEN:-}"

if [[ -z "${AUTH_TOKEN}" ]]; then
  echo "AUTH_TOKEN is required" >&2
  exit 1
fi

curl --fail --silent --show-error \
  -X POST \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  "${API_BASE_URL}/room/open?room_id=${ROOM_ID}"

echo
echo "Redeploy request sent for room_id=${ROOM_ID}"
