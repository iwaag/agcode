#!/bin/sh
set -eu

SESSION_ROOT="${NOOB_SESSION_ROOT:-/mnt/session}"
WORKSPACE_ROOT="${SESSION_ROOT}/workspace"
STATE_DIR="${SESSION_ROOT}/state"
CONTEXT_DIR="${SESSION_ROOT}/context"
READY_PATH="${STATE_DIR}/context-ready.json"
ERROR_PATH="${STATE_DIR}/context-error.json"

mkdir -p "${WORKSPACE_ROOT}" "${STATE_DIR}" "${CONTEXT_DIR}"
rm -f "${READY_PATH}" "${ERROR_PATH}"

export SESSION_ROOT WORKSPACE_ROOT STATE_DIR CONTEXT_DIR READY_PATH ERROR_PATH

write_error_marker() {
  ERROR_MESSAGE="$1" python3 - <<'PY'
import json
import os
from datetime import datetime, timezone
from pathlib import Path

payload = {
    "status": "failed",
    "error": os.environ.get("ERROR_MESSAGE", "workspace prep failed"),
    "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
}
Path(os.environ["ERROR_PATH"]).write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
PY
}

if ! python3 - <<'PY'
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


session_root = Path(os.environ["SESSION_ROOT"])
workspace_root = Path(os.environ["WORKSPACE_ROOT"])
ready_path = Path(os.environ["READY_PATH"])
error_path = Path(os.environ["ERROR_PATH"])
repo_url = os.environ.get("PREP_REPO_URL", "").strip()
ref = os.environ.get("PREP_REF", "").strip()
depth = os.environ.get("PREP_DEPTH", "").strip()
sub_path = os.environ.get("PREP_SUB_PATH", "").strip()
mode = os.environ.get("PREP_MODE", "clone").strip() or "clone"

if not repo_url:
    raise SystemExit("PREP_REPO_URL is required")
if mode != "clone":
    raise SystemExit(f"unsupported PREP_MODE: {mode}")

target_dir = workspace_root / sub_path if sub_path else workspace_root
target_dir.parent.mkdir(parents=True, exist_ok=True)
if target_dir.exists():
    shutil.rmtree(target_dir)
target_dir.mkdir(parents=True, exist_ok=True)

clone_cmd = ["git", "clone"]
if depth:
    clone_cmd.extend(["--depth", depth])
clone_cmd.extend([repo_url, str(target_dir)])
subprocess.run(clone_cmd, check=True)

if ref:
    fetch_cmd = ["git", "-C", str(target_dir), "fetch", "origin"]
    if depth:
        fetch_cmd.extend(["--depth", depth])
    fetch_cmd.append(ref)
    subprocess.run(fetch_cmd, check=True)
    subprocess.run(["git", "-C", str(target_dir), "checkout", "FETCH_HEAD"], check=True)

ready_payload = {
    "status": "ready",
    "repo_url": repo_url,
    "ref": ref or None,
    "workspace_path": str(target_dir),
    "updated_at": now_iso(),
}
ready_path.write_text(json.dumps(ready_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
PY
then
  write_error_marker "workspace prep failed"
  exit 1
fi
