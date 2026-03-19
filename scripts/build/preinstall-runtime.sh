#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
log() {
  printf '[build][preinstall] %s\n' "$*"
}

fail() {
  printf '[build][preinstall][error] %s\n' "$*" >&2
  exit 1
}

log "downloading offline assets"
"${SCRIPT_DIR}/download-offline-assets.sh"

log "preinstalled runtime is ready"
