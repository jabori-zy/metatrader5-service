#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

log() {
  printf '[build][uv] %s\n' "$*"
}

fail() {
  printf '[build][uv][error] %s\n' "$*" >&2
  exit 1
}

BUILD_WINEPREFIX="${BUILD_WINEPREFIX:-${WINEPREFIX:-/config/.wine}}"
MT5_INSTALLER_DIR="${MT5_INSTALLER_DIR:-/opt/installers}"
WINE_GECKO_DIR="${WINE_GECKO_DIR:-/opt/wine-offline/gecko}"
WINE_MONO_DIR="${WINE_MONO_DIR:-/opt/wine-offline/mono}"
UV_WINDOWS_ZIP_URL="${UV_WINDOWS_ZIP_URL:-https://github.com/astral-sh/uv/releases/download/0.10.11/uv-x86_64-pc-windows-msvc.zip}"
UV_ARCHIVE_NAME="$(basename "${UV_WINDOWS_ZIP_URL}")"
UV_ARCHIVE_PATH="${MT5_INSTALLER_DIR}/${UV_ARCHIVE_NAME}"
UV_EXTRACT_DIR="/tmp/uv-windows"
UV_INSTALL_DIR="${BUILD_WINEPREFIX}/drive_c/Program Files/uv"
UV_LINUX_EXE="${UV_INSTALL_DIR}/uv.exe"

export WINEPREFIX="${BUILD_WINEPREFIX}"
export WINEDEBUG="${WINEDEBUG:--all}"
export WINEARCH="${WINEARCH:-win64}"
export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-winemenubuilder.exe=d}"
export DISPLAY="${DISPLAY:-}"
export GST_PLUGIN_SYSTEM_PATH_1_0="${GST_PLUGIN_SYSTEM_PATH_1_0:-}"
export GST_PLUGIN_PATH_1_0="${GST_PLUGIN_PATH_1_0:-}"
export GST_REGISTRY="${GST_REGISTRY:-/tmp/gstreamer-registry.dat}"

command -v wine >/dev/null 2>&1 || fail "wine is not installed"
command -v winepath >/dev/null 2>&1 || fail "winepath is not installed"
command -v unzip >/dev/null 2>&1 || fail "unzip is not installed"
command -v timeout >/dev/null 2>&1 || fail "timeout is not installed"

mkdir -p "${WINEPREFIX}"
[[ -f "${UV_ARCHIVE_PATH}" ]] || fail "pre-downloaded uv archive not found: ${UV_ARCHIVE_PATH}"
[[ -d "${WINE_GECKO_DIR}" ]] || fail "Gecko offline directory not found: ${WINE_GECKO_DIR}"
[[ -d "${WINE_MONO_DIR}" ]] || fail "Mono offline directory not found: ${WINE_MONO_DIR}"

rm -rf "${UV_EXTRACT_DIR}"
mkdir -p "${UV_EXTRACT_DIR}" "${UV_INSTALL_DIR}"

log "extracting Windows uv archive"
unzip -oq "${UV_ARCHIVE_PATH}" -d "${UV_EXTRACT_DIR}" >/tmp/uv-unzip.log 2>&1 || {
  cat /tmp/uv-unzip.log >&2
  fail "failed to extract uv archive"
}

for exe in uv.exe uvx.exe uvw.exe; do
  UV_SOURCE="$(find "${UV_EXTRACT_DIR}" -type f -name "${exe}" | head -n 1 || true)"
  [[ -n "${UV_SOURCE}" ]] || fail "missing ${exe} in ${UV_ARCHIVE_PATH}"
  cp "${UV_SOURCE}" "${UV_INSTALL_DIR}/${exe}"
  chmod 755 "${UV_INSTALL_DIR}/${exe}"
done

[[ -f "${UV_LINUX_EXE}" ]] || fail "uv.exe not installed: ${UV_LINUX_EXE}"

log "verifying Windows uv version"
run_gui wine "${UV_LINUX_EXE}" --version >/tmp/uv-version.log 2>&1 || {
  cat /tmp/uv-version.log >&2
  fail "uv version check failed"
}
cat /tmp/uv-version.log
