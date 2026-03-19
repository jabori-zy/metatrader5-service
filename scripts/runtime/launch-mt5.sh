#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[runtime][launch] %s\n' "$*"
}

fail() {
  printf '[runtime][launch][error] %s\n' "$*" >&2
  exit 1
}

export WINEPREFIX="${WINEPREFIX:-/config/.wine}"
export WINEDEBUG="${WINEDEBUG:--all}"
export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-winemenubuilder.exe=d}"

MT5_LINUX_EXE="${WINEPREFIX}/drive_c/Program Files/MetaTrader 5/terminal64.exe"
MT5_LOG_DIR="/config/logs"
MT5_LOG_FILE="${MT5_LOG_DIR}/mt5.log"

mkdir -p "${MT5_LOG_DIR}" || fail "failed to create log directory: ${MT5_LOG_DIR}"

if pgrep -fa terminal64.exe >/dev/null; then
  log "MetaTrader 5 is already running"
  exit 0
fi

[[ -f "${MT5_LINUX_EXE}" ]] || fail "terminal64.exe not found: ${MT5_LINUX_EXE}"

log "launching MetaTrader 5"
# shellcheck disable=SC2086
wine "${MT5_LINUX_EXE}" /portable ${MT5_CMD_OPTIONS:-} >>"${MT5_LOG_FILE}" 2>&1 &

