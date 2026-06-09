#!/usr/bin/env bash
set -euo pipefail

EVENT_NAME="${1:-}"

if ! command -v python3 >/dev/null 2>&1; then
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/r2e_hook_on_${EVENT_NAME}.py"
if ! python3 "${PY_SCRIPT}"; then
  exit 2
fi
