#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

log() {
  printf '[build][mt5] %s\n' "$*"
}

fail() {
  printf '[build][mt5][error] %s\n' "$*" >&2
  exit 1
}

BUILD_WINEPREFIX="${BUILD_WINEPREFIX:-${WINEPREFIX:-/config/.wine}}"
MT5_INSTALLER_DIR="${MT5_INSTALLER_DIR:-/opt/installers}"
WINE_GECKO_DIR="${WINE_GECKO_DIR:-/opt/wine-offline/gecko}"
WINE_MONO_DIR="${WINE_MONO_DIR:-/opt/wine-offline/mono}"
MT5_INSTALL_TIMEOUT="${MT5_INSTALL_TIMEOUT:-600}"
MT5_LINUX_EXE="${BUILD_WINEPREFIX}/drive_c/Program Files/MetaTrader 5/terminal64.exe"
MT5_TARGET_DIR="${BUILD_WINEPREFIX}/drive_c/Program Files/MetaTrader 5"
MT5_INSTALLER="${MT5_INSTALLER_DIR}/mt5setup.exe"
MT5_BUNDLED_DIR="${MT5_BUNDLED_DIR:-/opt/MetaTrader 5}"
MONO_MARKER_DIR="${BUILD_WINEPREFIX}/drive_c/windows/mono"
MONO_INSTALLER="$(find "${WINE_MONO_DIR}" -maxdepth 1 -type f -name 'wine-mono-*.msi' | sort | head -n 1 || true)"

export WINEPREFIX="${BUILD_WINEPREFIX}"
export WINEDEBUG="${WINEDEBUG:--all}"
export WINEARCH="${WINEARCH:-win64}"
export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-winemenubuilder.exe=d}"
export DISPLAY="${DISPLAY:-}"
export GST_PLUGIN_SYSTEM_PATH_1_0="${GST_PLUGIN_SYSTEM_PATH_1_0:-}"
export GST_PLUGIN_PATH_1_0="${GST_PLUGIN_PATH_1_0:-}"
export GST_REGISTRY="${GST_REGISTRY:-/tmp/gstreamer-registry.dat}"

command -v wine >/dev/null 2>&1 || fail "wine is not installed"
command -v timeout >/dev/null 2>&1 || fail "timeout is not installed"

mkdir -p "$(dirname "${WINEPREFIX}")"
[[ -f "${MT5_INSTALLER}" ]] || fail "pre-downloaded MT5 installer not found: ${MT5_INSTALLER}"
[[ -d "${WINE_GECKO_DIR}" ]] || fail "Gecko offline directory not found: ${WINE_GECKO_DIR}"
[[ -d "${WINE_MONO_DIR}" ]] || fail "Mono offline directory not found: ${WINE_MONO_DIR}"
[[ -n "${MONO_INSTALLER}" ]] || fail "Mono installer not found in: ${WINE_MONO_DIR}"
[[ -d "${MT5_BUNDLED_DIR}" ]] || fail "bundled MetaTrader 5 directory not found: ${MT5_BUNDLED_DIR}"
[[ -f "${MT5_BUNDLED_DIR}/terminal64.exe" ]] || fail "bundled terminal64.exe not found: ${MT5_BUNDLED_DIR}/terminal64.exe"

if [[ ! -f "${WINEPREFIX}/system.reg" ]]; then
  log "initializing Wine prefix ${WINEPREFIX}"
  rm -rf "${WINEPREFIX}"
  run_gui winecfg -v=win10 >/tmp/mt5-winecfg-init.log 2>&1 || {
    cat /tmp/mt5-winecfg-init.log >&2
    fail "winecfg initialization failed"
  }
  wait_for_wineserver
else
  log "setting Wine to Windows 10 mode"
  run_gui winecfg -v=win10 >/tmp/mt5-winver.log 2>&1 || {
    cat /tmp/mt5-winver.log >&2
    fail "failed to set Wine Windows version"
  }
  wait_for_wineserver
fi

if [[ ! -d "${MONO_MARKER_DIR}" ]]; then
  log "installing Wine Mono"
  run_gui wine msiexec /i "${MONO_INSTALLER}" /qn >/tmp/mt5-mono.log 2>&1 || {
    cat /tmp/mt5-mono.log >&2
    fail "Wine Mono installation failed"
  }
  wait_for_wineserver
else
  log "Wine Mono already installed, skipping"
fi

#
# The unattended installer path is intentionally kept here for fallback.
# Temporarily disabled while the image ships a bundled MetaTrader 5 directory.
#
# log "running MT5 unattended installation"
# log "note: mt5setup.exe is a bootstrap installer and may still download MT5 components from the network"
# rm -f /tmp/mt5-install.log
# run_gui bash -lc "wine \"${MT5_INSTALLER}\" /auto" >/tmp/mt5-install.log 2>&1 &
# INSTALLER_PID=$!
# START_TIME=$SECONDS
# INSTALLER_EXIT_REPORTED=0
#
# while (( SECONDS - START_TIME < MT5_INSTALL_TIMEOUT )); do
#   if [[ -f "${MT5_LINUX_EXE}" ]]; then
#     break
#   fi
#
#   if [[ "${INSTALLER_EXIT_REPORTED}" -eq 0 ]] && ! kill -0 "${INSTALLER_PID}" 2>/dev/null; then
#     set +e
#     wait "${INSTALLER_PID}"
#     INSTALLER_STATUS=$?
#     set -e
#     log "MT5 installer process exited with code ${INSTALLER_STATUS}, waiting for installation to complete"
#     INSTALLER_EXIT_REPORTED=1
#   fi
#
#   ELAPSED=$((SECONDS - START_TIME))
#   log "MT5 installation still in progress (${ELAPSED}s elapsed, waiting for ${MT5_LINUX_EXE})"
#   sleep 2
# done
#
# if [[ ! -f "${MT5_LINUX_EXE}" ]]; then
#   {
#     echo
#     echo "[build][mt5][error] MT5 installation timed out (${MT5_INSTALL_TIMEOUT}s)"
#     ps -ef | grep -Ei 'mt5setup|terminal64|wine|winedevice|wineserver' | grep -v grep || true
#   } >>/tmp/mt5-install.log
#   wineserver -k >/dev/null 2>&1 || true
#   cat /tmp/mt5-install.log >&2
#   fail "MT5 unattended installation failed"
# fi

log "copying bundled MetaTrader 5 directory from ${MT5_BUNDLED_DIR} into Wine prefix"
mkdir -p "$(dirname "${MT5_TARGET_DIR}")"
rm -rf "${MT5_TARGET_DIR}"
cp -a "${MT5_BUNDLED_DIR}" "${MT5_TARGET_DIR}"

wait_for_wineserver

[[ -f "${MT5_LINUX_EXE}" ]] || fail "terminal64.exe not found: ${MT5_LINUX_EXE}"
log "MetaTrader 5 files are ready: ${MT5_LINUX_EXE}"
