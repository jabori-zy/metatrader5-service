#!/usr/bin/env bash
# Shared utility functions sourced by build and runtime scripts.
# This file is not meant to be executed directly.

# Run a command with a virtual display if DISPLAY is not set.
run_gui() {
  if [[ -n "${DISPLAY:-}" ]]; then
    "$@"
    return
  fi

  if ! command -v xvfb-run >/dev/null 2>&1; then
    printf '[common][error] DISPLAY is not set and xvfb-run is not installed\n' >&2
    exit 1
  fi
  xvfb-run -a "$@"
}

# Wait for wineserver to finish; kill it forcefully on timeout.
wait_for_wineserver() {
  local timeout_secs="${WINE_WAIT_TIMEOUT:-60}"

  if timeout "${timeout_secs}" wineserver -w; then
    return
  fi

  printf '[common] wineserver wait timed out, killing remaining processes\n'
  wineserver -k >/dev/null 2>&1 || true
  sleep 2
}
