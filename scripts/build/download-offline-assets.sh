#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[build][assets] %s\n' "$*"
}

fail() {
  printf '[build][assets][error] %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "missing required command: $1"
}

get_app_ver() {
  local app="${1^^}"
  local wine_ver="$2"
  local url="https://raw.githubusercontent.com/wine-mirror/wine/wine-${wine_ver}/dlls/appwiz.cpl/addons.c"

  curl -fsSL "$url" | grep -E "^#define ${app}_VERSION\\s" | awk -F'"' '{print $2}'
}

download_file() {
  local url="$1"
  local output="$2"

  log "downloading $(basename "$output")"
  curl -fL "$url" -o "$output" || fail "download failed: $url"
  [[ -s "$output" ]] || fail "downloaded file is empty: $output"
}

require_cmd curl
require_cmd wine

MT5_INSTALLER_DIR="${MT5_INSTALLER_DIR:-/opt/installers}"
WINE_GECKO_DIR="${WINE_GECKO_DIR:-/opt/wine-offline/gecko}"
WINE_MONO_DIR="${WINE_MONO_DIR:-/opt/wine-offline/mono}"
MT5_SETUP_URL="${MT5_SETUP_URL:-https://download.terminal.free/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe}"
PYTHON_VERSION="${PYTHON_VERSION:-3.9.13}"
PYTHON_SETUP_URL="${PYTHON_SETUP_URL:-https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-amd64.exe}"
PYTHON_INSTALLER_NAME="$(basename "${PYTHON_SETUP_URL}")"

mkdir -p "$MT5_INSTALLER_DIR" "$WINE_GECKO_DIR" "$WINE_MONO_DIR"

WINE_VER="$(wine --version | awk '{print $1}' | sed -E 's/^wine-//')"
[[ -n "$WINE_VER" ]] || fail "failed to parse Wine version"
log "detected Wine version: $WINE_VER"

GECKO_VER="$(get_app_ver gecko "$WINE_VER")"
MONO_VER="$(get_app_ver mono "$WINE_VER")"
[[ -n "$GECKO_VER" ]] || fail "failed to parse Gecko version"
[[ -n "$MONO_VER" ]] || fail "failed to parse Mono version"
log "Gecko version: $GECKO_VER"
log "Mono version: $MONO_VER"

download_file "$MT5_SETUP_URL" "$MT5_INSTALLER_DIR/mt5setup.exe"
download_file "$PYTHON_SETUP_URL" "$MT5_INSTALLER_DIR/${PYTHON_INSTALLER_NAME}"
download_file "https://dl.winehq.org/wine/wine-gecko/${GECKO_VER}/wine-gecko-${GECKO_VER}-x86.msi" \
  "$WINE_GECKO_DIR/wine-gecko-${GECKO_VER}-x86.msi"
download_file "https://dl.winehq.org/wine/wine-gecko/${GECKO_VER}/wine-gecko-${GECKO_VER}-x86_64.msi" \
  "$WINE_GECKO_DIR/wine-gecko-${GECKO_VER}-x86_64.msi"
download_file "https://dl.winehq.org/wine/wine-mono/${MONO_VER}/wine-mono-${MONO_VER}-x86.msi" \
  "$WINE_MONO_DIR/wine-mono-${MONO_VER}-x86.msi"

log "offline assets ready"
