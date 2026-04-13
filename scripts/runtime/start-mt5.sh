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

run_and_measure() {
  local component="$1"
  local stage="$2"
  shift 2

  local start_time=$SECONDS
  diag_log "${component}" "${stage}" "action=start"
  if "$@"; then
    local rc=0
    local duration=$((SECONDS - start_time))
    diag_log "${component}" "${stage}" "action=finish rc=${rc} duration=${duration}s"
    return 0
  fi

  local rc=$?
  local duration=$((SECONDS - start_time))
  diag_log "${component}" "${stage}" "action=finish rc=${rc} duration=${duration}s"
  return "${rc}"
}

mkdir -p "${MT5_LOG_DIR}" || fail "failed to create log directory: ${MT5_LOG_DIR}"
touch "${MT5_LOG_FILE}" || fail "failed to create log file: ${MT5_LOG_FILE}"
exec > >(tee -a "${MT5_LOG_FILE}") 2>&1

diag_log "start" "entry" "pwd=$(pwd) xauthority=${XAUTHORITY:-<unset>} wineprefix=${WINEPREFIX} mt5_log_file=${MT5_LOG_FILE}"
diag_run_probe "start" "entry" "ls-x11-unix" ls -ld /tmp/.X11-unix
diag_display_probe "start" "entry"
diag_process_snapshot "start" "entry"

touch "${STARTUP_MARKER}" || fail "failed to create startup marker: ${STARTUP_MARKER}"
trap cleanup_startup_marker EXIT

TOTAL_START_TIME=$SECONDS

run_and_measure "start" "bootstrap-prefix" "${SCRIPT_DIR}/bootstrap-prefix.sh"
diag_process_snapshot "start" "post-bootstrap"

log "running MT5 installation"
MT5_INSTALL_START=$SECONDS
run_and_measure "start" "install-mt5" /scripts/build/install-mt5.sh || fail "MT5 first-time installation failed, check ${MT5_LOG_FILE}"
MT5_INSTALL_DURATION=$((SECONDS - MT5_INSTALL_START))
log "MT5 installation completed in ${MT5_INSTALL_DURATION}s"

log "running Windows uv installation"
UV_INSTALL_START=$SECONDS
run_and_measure "start" "install-uv" /scripts/build/install-uv.sh || fail "Windows uv first-time installation failed, check ${MT5_LOG_FILE}"
UV_INSTALL_DURATION=$((SECONDS - UV_INSTALL_START))
log "Windows uv installation completed in ${UV_INSTALL_DURATION}s"

log "running Windows Python installation"
PYTHON_INSTALL_START=$SECONDS
run_and_measure "start" "install-python" /scripts/build/install-python.sh || fail "Windows Python first-time installation failed, check ${MT5_LOG_FILE}"
PYTHON_INSTALL_DURATION=$((SECONDS - PYTHON_INSTALL_START))
log "Windows Python installation completed in ${PYTHON_INSTALL_DURATION}s"

[[ -f "${MT5_LINUX_EXE}" ]] || fail "terminal64.exe not found: ${MT5_LINUX_EXE}"

log "terminal64.exe is ready at ${MT5_LINUX_EXE}"
log "starting MetaTrader 5"
MT5_START_TIME=$SECONDS
diag_process_snapshot "start" "pre-launch"
run_and_measure "start" "launch-mt5" /scripts/runtime/launch-mt5.sh || fail "MetaTrader 5 startup failed, check ${MT5_LOG_FILE}"
for _ in $(seq 1 60); do
  if pgrep -fa terminal64.exe >/dev/null; then
    break
  fi
  sleep 1
done
pgrep -fa terminal64.exe >/dev/null || fail "MetaTrader 5 did not start within 60s, check ${MT5_LOG_FILE}"
MT5_START_DURATION=$((SECONDS - MT5_START_TIME))
diag_run_probe "start" "mt5-started" "pgrep-terminal64" pgrep -fa terminal64.exe
diag_process_snapshot "start" "mt5-started"
log "MetaTrader 5 started in ${MT5_START_DURATION}s"

log "starting HTTP service"
HTTP_START_TIME=$SECONDS
run_and_measure "start" "launch-http" /scripts/runtime/http-start.sh || fail "HTTP startup failed, check /config/logs/http.log"
HTTP_START_DURATION=$((SECONDS - HTTP_START_TIME))
TOTAL_DURATION=$((SECONDS - TOTAL_START_TIME))
diag_process_snapshot "start" "http-started"
log "HTTP service started in ${HTTP_START_DURATION}s"
log "startup summary: mt5_install=${MT5_INSTALL_DURATION}s, uv_install=${UV_INSTALL_DURATION}s, python_install=${PYTHON_INSTALL_DURATION}s, mt5_start=${MT5_START_DURATION}s, http_start=${HTTP_START_DURATION}s, total=${TOTAL_DURATION}s"
cleanup_startup_marker

HTTP_PID_FILE="/config/run/http.pid"
if [[ ! -f "${HTTP_PID_FILE}" ]]; then
  fail "HTTP pid file not found after startup: ${HTTP_PID_FILE}"
fi

HTTP_PID="$(tr -d '[:space:]' <"${HTTP_PID_FILE}")"
[[ -n "${HTTP_PID}" ]] || fail "HTTP pid file is empty: ${HTTP_PID_FILE}"

MT5_PID="$(pgrep -o -f terminal64.exe || true)"
[[ -n "${MT5_PID}" ]] || fail "MetaTrader 5 pid not found after startup"

log "monitoring MetaTrader 5 pid ${MT5_PID} and HTTP service pid ${HTTP_PID}"
while kill -0 "${MT5_PID}" 2>/dev/null && kill -0 "${HTTP_PID}" 2>/dev/null; do
  sleep 5
done

if ! kill -0 "${MT5_PID}" 2>/dev/null; then
  diag_log "start" "monitor-exit" "reason=mt5-exited mt5_pid=${MT5_PID} http_pid=${HTTP_PID}"
  diag_process_snapshot "start" "monitor-exit-mt5"
  fail "MetaTrader 5 exited unexpectedly, check ${MT5_LOG_FILE}"
fi

diag_log "start" "monitor-exit" "reason=http-exited mt5_pid=${MT5_PID} http_pid=${HTTP_PID}"
diag_process_snapshot "start" "monitor-exit-http"
fail "HTTP service exited unexpectedly, check /config/logs/http.log"
