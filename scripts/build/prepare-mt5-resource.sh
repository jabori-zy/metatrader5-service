#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[build][mt5-resource] %s\n' "$*"
}

fail() {
  printf '[build][mt5-resource][error] %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "missing required command: $1"
}

MT5_SOURCE_DIR="${MT5_SOURCE_DIR:-/resource/MetaTrader 5}"
MT5_BUNDLED_DIR="${MT5_BUNDLED_DIR:-/opt/MetaTrader 5}"
TERMINAL_ZIP="${MT5_SOURCE_DIR}/terminal64.zip"
METAEDITOR_ZIP="${MT5_SOURCE_DIR}/MetaEditor64.zip"

require_cmd unzip

[[ -d "${MT5_SOURCE_DIR}" ]] || fail "MetaTrader 5 resource directory not found: ${MT5_SOURCE_DIR}"
[[ -f "${TERMINAL_ZIP}" ]] || fail "terminal64.zip not found: ${TERMINAL_ZIP}"
[[ -f "${METAEDITOR_ZIP}" ]] || fail "MetaEditor64.zip not found: ${METAEDITOR_ZIP}"

log "preparing bundled MetaTrader 5 directory"
rm -rf "${MT5_BUNDLED_DIR}"
mkdir -p "$(dirname "${MT5_BUNDLED_DIR}")"
cp -a "${MT5_SOURCE_DIR}" "${MT5_BUNDLED_DIR}"

log "extracting terminal64.zip"
unzip -oq "${MT5_BUNDLED_DIR}/terminal64.zip" -d "${MT5_BUNDLED_DIR}" >/tmp/mt5-terminal-unzip.log 2>&1 || {
  cat /tmp/mt5-terminal-unzip.log >&2
  fail "failed to extract terminal64.zip"
}

log "extracting MetaEditor64.zip"
unzip -oq "${MT5_BUNDLED_DIR}/MetaEditor64.zip" -d "${MT5_BUNDLED_DIR}" >/tmp/mt5-metaeditor-unzip.log 2>&1 || {
  cat /tmp/mt5-metaeditor-unzip.log >&2
  fail "failed to extract MetaEditor64.zip"
}

rm -f "${MT5_BUNDLED_DIR}/terminal64.zip" "${MT5_BUNDLED_DIR}/MetaEditor64.zip"

[[ -f "${MT5_BUNDLED_DIR}/terminal64.exe" ]] || fail "terminal64.exe not found after extraction"
[[ -f "${MT5_BUNDLED_DIR}/MetaEditor64.exe" ]] || fail "MetaEditor64.exe not found after extraction"

log "bundled MetaTrader 5 directory is ready: ${MT5_BUNDLED_DIR}"
