#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") [PROJECT_ROOT_PATH]"
}

if [[ $# -gt 1 ]]; then
  echo "[ERROR] Too many arguments." >&2
  usage >&2
  exit 1
fi

if [[ $# -eq 0 ]]; then
  PROJECT_ROOT="${HOME}"
else
  PROJECT_ROOT="${1}"
  case "${PROJECT_ROOT}" in
    ~)
      PROJECT_ROOT="${HOME}"
      ;;
    ~/*)
      PROJECT_ROOT="${HOME}/${PROJECT_ROOT#~/}"
      ;;
  esac
fi

TARGET_DIR="${PROJECT_ROOT}/.cursor/plugins/local/r2e"

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "Target: ${TARGET_DIR}. Plugin not found, nothing to uninstall."
  exit 0
fi

rm -rf "${TARGET_DIR}"
echo "Target: ${TARGET_DIR}. Plugin uninstalled successfully. Please restart Cursor"
exit 0
