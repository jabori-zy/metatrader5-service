#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

log() {
  printf '[runtime][bootstrap] %s\n' "$*"
}

fail() {
  printf '[runtime][bootstrap][error] %s\n' "$*" >&2
  exit 1
}

RUNTIME_WINEPREFIX="/config/.wine"

export WINEPREFIX="${RUNTIME_WINEPREFIX}"

mkdir -p /config || fail "failed to create /config"
mkdir -p "$(dirname "${RUNTIME_WINEPREFIX}")" || fail "failed to prepare Wine prefix parent directory"

if [[ -d "${RUNTIME_WINEPREFIX}" ]]; then
  log "runtime Wine prefix already exists"
else
  log "runtime Wine prefix will be initialized on first install"
fi
