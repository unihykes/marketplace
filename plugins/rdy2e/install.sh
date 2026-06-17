#!/usr/bin/env bash
set -euo pipefail

if [[ $# -gt 1 ]]; then
  echo "[ERROR] Too many arguments." >&2
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

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${PROJECT_ROOT}/.cursor/plugins/local/r2e"
echo "Source: ${SOURCE_DIR} | Target: ${TARGET_DIR}"

if [[ -d "${TARGET_DIR}" ]]; then
  echo "Removing existing plugin: ${TARGET_DIR}"
  rm -rf "${TARGET_DIR}"
fi

mkdir -p "${TARGET_DIR}"

copy_dir() {
  local src="${SOURCE_DIR}/$1"
  if [[ ! -e "${src}" ]]; then
    return 0
  fi
  if [[ -n "${2:-}" ]]; then
    cp -a "${src}/." "${TARGET_DIR}/${2}/"
  else
    cp -a "${src}" "${TARGET_DIR}/"
  fi
}

copy_dir ".cursor-plugin"
copy_dir "rules"
copy_dir "skills"
copy_dir "agents"
copy_dir "commands"
copy_dir "hooks/linux" "hooks"

echo "Plugin installed successfully. Please restart Cursor"
exit 0
