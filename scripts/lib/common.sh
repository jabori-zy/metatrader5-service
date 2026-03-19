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

python_version_tag() {
  local version="${PYTHON_VERSION:-3.9.13}"
  local major_minor
  major_minor="$(printf '%s' "${version}" | awk -F. '{print $1 $2}')"
  printf '%s\n' "${major_minor}"
}

# Locate the Windows Python executable inside the Wine prefix.
# Requires WINEPREFIX to be exported by the calling script.
find_windows_python() {
  local version_tag
  local preferred
  local preferred_32

  version_tag="$(python_version_tag)"
  preferred="${WINEPREFIX}/drive_c/Program Files/Python${version_tag}/python.exe"
  preferred_32="${WINEPREFIX}/drive_c/Program Files (x86)/Python${version_tag}-32/python.exe"

  if [[ -f "${preferred_32}" ]]; then
    printf '%s\n' "${preferred_32}"
    return
  fi

  if [[ -f "${preferred}" ]]; then
    printf '%s\n' "${preferred}"
    return
  fi

  find "${WINEPREFIX}/drive_c" -type f \
    \( -path "*/Program Files*/Python${version_tag}*/python.exe" \
    -o -path '*/Program Files*/Python*/python.exe' \) \
    ! -path '*/Lib/venv/*' \
    | sort | head -n 1
}
