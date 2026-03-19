#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[runtime][start] %s\n' "$*"
}

fail() {
  printf '[runtime][start][error] %s\n' "$*" >&2
  exit 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

export WINEPREFIX="/config/.wine"
export WINEDEBUG="${WINEDEBUG:--all}"
export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-winemenubuilder.exe=d}"
export WINE_GECKO_DIR="${WINE_GECKO_DIR:-/opt/wine-offline/gecko}"
export WINE_MONO_DIR="${WINE_MONO_DIR:-/opt/wine-offline/mono}"
export MT5_INSTALLER_DIR="${MT5_INSTALLER_DIR:-/opt/installers}"

MT5_LINUX_EXE="${WINEPREFIX}/drive_c/Program Files/MetaTrader 5/terminal64.exe"
MT5_LOG_DIR="/config/logs"
MT5_LOG_FILE="${MT5_LOG_DIR}/mt5.log"
STARTUP_MARKER="/config/.mt5-startup-in-progress"

cleanup_startup_marker() {
  rm -f "${STARTUP_MARKER}"
}

mkdir -p "${MT5_LOG_DIR}" || fail "failed to create log directory: ${MT5_LOG_DIR}"
touch "${MT5_LOG_FILE}" || fail "failed to create log file: ${MT5_LOG_FILE}"
exec > >(tee -a "${MT5_LOG_FILE}") 2>&1

touch "${STARTUP_MARKER}" || fail "failed to create startup marker: ${STARTUP_MARKER}"
trap cleanup_startup_marker EXIT

TOTAL_START_TIME=$SECONDS

"${SCRIPT_DIR}/bootstrap-prefix.sh"

log "running MT5 installation"
MT5_INSTALL_START=$SECONDS
/scripts/build/install-mt5.sh || fail "MT5 first-time installation failed, check ${MT5_LOG_FILE}"
MT5_INSTALL_DURATION=$((SECONDS - MT5_INSTALL_START))
log "MT5 installation completed in ${MT5_INSTALL_DURATION}s"

log "running Windows uv installation"
UV_INSTALL_START=$SECONDS
/scripts/build/install-uv.sh || fail "Windows uv first-time installation failed, check ${MT5_LOG_FILE}"
UV_INSTALL_DURATION=$((SECONDS - UV_INSTALL_START))
log "Windows uv installation completed in ${UV_INSTALL_DURATION}s"

[[ -f "${MT5_LINUX_EXE}" ]] || fail "terminal64.exe not found: ${MT5_LINUX_EXE}"

log "starting MetaTrader 5"
# shellcheck disable=SC2086
wine "${MT5_LINUX_EXE}" /portable ${MT5_CMD_OPTIONS:-} >>"${MT5_LOG_FILE}" 2>&1 &
MT5_PID=$!

for _ in $(seq 1 30); do
  if pgrep -fa terminal64.exe >/dev/null; then
    TOTAL_DURATION=$((SECONDS - TOTAL_START_TIME))
    log "MetaTrader 5 started"
    # HTTP startup is intentionally disabled for now.
    # Re-enable /scripts/runtime/http-start.sh after validating Wine uv startup.
    log "HTTP startup is disabled in this phase"
    log "startup summary: mt5_install=${MT5_INSTALL_DURATION}s, uv_install=${UV_INSTALL_DURATION}s, total=${TOTAL_DURATION}s"
    cleanup_startup_marker
    wait "${MT5_PID}"
    exit $?
  fi
  sleep 2
done

fail "MetaTrader 5 process failed to start, check ${MT5_LOG_FILE}"
