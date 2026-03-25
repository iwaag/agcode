#!/bin/sh
set -eu

ROOM_ROOT="${NOOB_ROOM_ROOT:-/mnt/room}"

mkdir -p \
  "${ROOM_ROOT}/control" \
  "${ROOM_ROOT}/events" \
  "${ROOM_ROOT}/state" \
  "${ROOM_ROOT}/artifacts"

exec node /app/noob_runner.mjs
