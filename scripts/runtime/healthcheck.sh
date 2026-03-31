#!/usr/bin/env bash
set -euo pipefail

WINEPREFIX="/config/.wine"
MT5_LINUX_EXE="${WINEPREFIX}/drive_c/Program Files/MetaTrader 5/terminal64.exe"
STARTUP_MARKER="/config/.mt5-startup-in-progress"
HTTP_PORT="${HTTP_PORT:-8000}"

if [[ -f "${STARTUP_MARKER}" ]]; then
  printf '[healthcheck] first-time startup initialization in progress, skipping health check\n'
  exit 0
fi

if [[ ! -d "${WINEPREFIX}" ]]; then
  printf '[healthcheck] preinstalled WINEPREFIX does not exist: %s\n' "${WINEPREFIX}" >&2
  exit 1
fi

if [[ ! -f "${MT5_LINUX_EXE}" ]]; then
  printf '[healthcheck] terminal64.exe not found: %s\n' "${MT5_LINUX_EXE}" >&2
  exit 1
fi

if ! pgrep -fa terminal64.exe >/dev/null; then
  printf '[healthcheck] MetaTrader 5 is not running\n' >&2
  exit 1
fi

if ! curl -fsS --max-time 2 "http://127.0.0.1:${HTTP_PORT}/" >/dev/null 2>&1; then
  printf '[healthcheck] HTTP service is not ready on port %s\n' "${HTTP_PORT}" >&2
  exit 1
fi

exit 0
