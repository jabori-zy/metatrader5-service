#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

log() {
  printf '[build][python] %s\n' "$*"
}

fail() {
  printf '[build][python][error] %s\n' "$*" >&2
  exit 1
}

BUILD_WINEPREFIX="${BUILD_WINEPREFIX:-${WINEPREFIX:-/config/.wine}}"
MT5_INSTALLER_DIR="${MT5_INSTALLER_DIR:-/opt/installers}"
WINE_GECKO_DIR="${WINE_GECKO_DIR:-/opt/wine-offline/gecko}"
WINE_MONO_DIR="${WINE_MONO_DIR:-/opt/wine-offline/mono}"
PYTHON_VERSION="${PYTHON_VERSION:-3.9.13}"
PYTHON_SETUP_URL="${PYTHON_SETUP_URL:-https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-amd64.exe}"
PYTHON_INSTALLER="${MT5_INSTALLER_DIR}/$(basename "${PYTHON_SETUP_URL}")"
PYTHON_WIN_DIR='C:\Program Files\Python39'
PYTHON_INSTALL_DIR="${BUILD_WINEPREFIX}/drive_c/Program Files/Python39"
PYTHON_LINUX_EXE="${PYTHON_INSTALL_DIR}/python.exe"
PYTHON_WIN_EXE="${PYTHON_WIN_DIR}\\python.exe"

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

mkdir -p "${WINEPREFIX}"
[[ -f "${PYTHON_INSTALLER}" ]] || fail "pre-downloaded Python installer not found: ${PYTHON_INSTALLER}"
[[ -d "${WINE_GECKO_DIR}" ]] || fail "Gecko offline directory not found: ${WINE_GECKO_DIR}"
[[ -d "${WINE_MONO_DIR}" ]] || fail "Mono offline directory not found: ${WINE_MONO_DIR}"

if [[ -f "${PYTHON_LINUX_EXE}" ]]; then
  log "Windows Python already installed, verifying version"
else
  log "running Python silent installation"
  run_gui wine "${PYTHON_INSTALLER}" /quiet InstallAllUsers=1 PrependPath=0 Include_test=0 TargetDir="${PYTHON_WIN_DIR}" >/tmp/python-install.log 2>&1 || {
    cat /tmp/python-install.log >&2
    fail "Python silent installation failed"
  }
  wait_for_wineserver
fi

[[ -f "${PYTHON_LINUX_EXE}" ]] || fail "installed python.exe not found: ${PYTHON_LINUX_EXE}"
log "detected Windows Python: ${PYTHON_LINUX_EXE}"

log "verifying Windows Python version"
run_gui wine "${PYTHON_WIN_EXE}" --version >/tmp/python-version.log 2>&1 || {
  cat /tmp/python-version.log >&2
  fail "Python version check failed"
}
cat /tmp/python-version.log
