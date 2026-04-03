#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./http-env.sh
source "${SCRIPT_DIR}/http-env.sh"

ensure_http_dirs
require_http_runtime
resolve_windows_uv
resolve_uv_runtime_paths
warn_legacy_project_venv

unset VIRTUAL_ENV

http_log "syncing service dependencies with uv"
(
  cd "${SERVICE_ROOT}"
  export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT_WIN}"
  export UV_CACHE_DIR="${UV_CACHE_DIR_WIN}"
  run_gui wine "${UV_LINUX_EXE}" sync \
    --frozen \
    --no-install-project \
    --no-python-downloads \
    --python "${SYSTEM_PYTHON_WIN_EXE}"
) > >(tee -a "${HTTP_LOG_FILE}") 2>&1 || http_fail "uv sync failed"

[[ -f "${SERVICE_VENV_PYTHON_LINUX}" ]] || http_fail "service venv Python not found after sync: ${SERVICE_VENV_PYTHON_LINUX}"
touch "${HTTP_DEPS_OK_FILE}" || http_fail "failed to update dependency sync marker"
http_log "service dependencies are synchronized"
