#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

export WINEPREFIX="${WINEPREFIX:-/config/.wine}"
export WINEDEBUG="${WINEDEBUG:--all}"
export WINEARCH="${WINEARCH:-win64}"
export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-winemenubuilder.exe=d}"

SERVICE_ROOT="${SERVICE_ROOT:-/workspace/metatrader5-service/service}"
SERVICE_MAIN_LINUX="${SERVICE_ROOT}/main.py"
SERVICE_LOCKFILE="${SERVICE_ROOT}/uv.lock"
SERVICE_VENV_PYTHON_LINUX="${SERVICE_ROOT}/.venv/Scripts/python.exe"
UV_LINUX_EXE="${UV_LINUX_EXE:-${WINEPREFIX}/drive_c/Program Files/uv/uv.exe}"

HTTP_ENV="${HTTP_ENV:-dev}"
HTTP_PORT="${HTTP_PORT:-8000}"
HTTP_LOG_DIR="${HTTP_LOG_DIR:-/config/logs}"
HTTP_LOG_FILE="${HTTP_LOG_FILE:-${HTTP_LOG_DIR}/http.log}"
HTTP_RUN_DIR="${HTTP_RUN_DIR:-/config/run}"
HTTP_PID_FILE="${HTTP_PID_FILE:-${HTTP_RUN_DIR}/http.pid}"
HTTP_DEPS_OK_FILE="${HTTP_DEPS_OK_FILE:-${HTTP_RUN_DIR}/http-deps.ok}"
HTTP_BOOT_TIMEOUT="${HTTP_BOOT_TIMEOUT:-15}"

MT5_TERMINAL_PATH="${MT5_TERMINAL_PATH:-C:/Program Files/MetaTrader 5/terminal64.exe}"

http_log() {
  mkdir -p "${HTTP_LOG_DIR}" "${HTTP_RUN_DIR}"
  printf '[runtime][http] %s\n' "$*" | tee -a "${HTTP_LOG_FILE}"
}

http_fail() {
  http_log "[error] $*"
  exit 1
}

ensure_http_dirs() {
  mkdir -p "${HTTP_LOG_DIR}" "${HTTP_RUN_DIR}" || http_fail "failed to prepare HTTP runtime directories"
  touch "${HTTP_LOG_FILE}" || http_fail "failed to create HTTP log file: ${HTTP_LOG_FILE}"
}

require_http_runtime() {
  [[ -d "${SERVICE_ROOT}" ]] || http_fail "service root not found: ${SERVICE_ROOT}"
  [[ -f "${SERVICE_MAIN_LINUX}" ]] || http_fail "service entrypoint not found: ${SERVICE_MAIN_LINUX}"
  [[ -f "${SERVICE_LOCKFILE}" ]] || http_fail "service lockfile not found: ${SERVICE_LOCKFILE}"
  [[ -n "${MT5_LOGIN:-}" ]] || http_fail "MT5_LOGIN is required"
  [[ -n "${MT5_PASSWORD:-}" ]] || http_fail "MT5_PASSWORD is required"
  [[ -n "${MT5_SERVER:-}" ]] || http_fail "MT5_SERVER is required"
}

ensure_mt5_running() {
  if ! pgrep -fa terminal64.exe >/dev/null; then
    http_fail "MetaTrader 5 is not running"
  fi
}

resolve_windows_uv() {
  [[ -f "${UV_LINUX_EXE}" ]] || http_fail "uv.exe not found in Wine prefix: ${UV_LINUX_EXE}"
  UV_WIN_EXE="$(winepath -w "${UV_LINUX_EXE}")"
}

resolve_service_paths() {
  SERVICE_MAIN_WIN="$(winepath -w "${SERVICE_MAIN_LINUX}")"
  SERVICE_VENV_PYTHON_WIN="$(winepath -w "${SERVICE_VENV_PYTHON_LINUX}")"
}

http_pid_is_running() {
  [[ -f "${HTTP_PID_FILE}" ]] || return 1

  local pid
  pid="$(tr -d '[:space:]' <"${HTTP_PID_FILE}")"
  [[ -n "${pid}" ]] || return 1
  kill -0 "${pid}" 2>/dev/null
}

collect_http_pids() {
  pgrep -f "python.*main.py" || true
}
