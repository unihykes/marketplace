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
R2U_DIR="$(cd "${SOURCE_DIR}/../r2u" 2>/dev/null && pwd || true)"
TARGET_DIR="${PROJECT_ROOT}/.cursor/plugins/local/r2e"
echo "Source: ${SOURCE_DIR} | Target: ${TARGET_DIR}"

if [[ -d "${TARGET_DIR}" ]]; then
  echo "Removing existing plugin: ${TARGET_DIR}"
  rm -rf "${TARGET_DIR}"
fi

mkdir -p "${TARGET_DIR}"

copy_dir_optional() {
  local src="$1"
  local target_name="${2:-$1}"
  if [[ ! -d "${src}" ]]; then
    src="${SOURCE_DIR}/$1"
  fi
  if [[ ! -d "${src}" ]]; then
    return 0
  fi
  mkdir -p "${TARGET_DIR}/${target_name}"
  cp -a "${src}/." "${TARGET_DIR}/${target_name}/"
}

copy_dir_optional ".cursor-plugin"
copy_dir_optional "rules"
copy_dir_optional "skills"
copy_dir_optional "${R2U_DIR}/skills" "skills"
copy_dir_optional "agents"
copy_dir_optional "commands"
copy_dir_optional "hooks/linux" "hooks"

echo "Plugin installed successfully. Please restart Cursor"
exit 0
