#!/usr/bin/env bash
# Shared utility functions sourced by build and runtime scripts.
# This file is not meant to be executed directly.

diag_timestamp() {
  date '+%Y-%m-%dT%H:%M:%S%z'
}

diag_compact_output() {
  local text="${1:-}"
  text="${text//$'\r'/ }"
  text="${text//$'\n'/ | }"
  text="${text//$'\t'/ }"
  if [[ ${#text} -gt 1200 ]]; then
    text="${text:0:1200}..."
  fi
  printf '%s' "${text}"
}

diag_log() {
  local component="$1"
  local stage="$2"
  shift 2

  local message="${*:-}"
  local display="${DISPLAY:-<unset>}"
  printf '[diag][%s] ts=%s pid=%s ppid=%s display=%s stage=%s %s\n' \
    "${component}" \
    "$(diag_timestamp)" \
    "$$" \
    "${PPID:-unknown}" \
    "${display}" \
    "${stage}" \
    "${message}"
}

diag_run_probe() {
  local component="$1"
  local stage="$2"
  local label="$3"
  shift 3

  local had_errexit=0
  local output
  local rc
  if [[ $- == *e* ]]; then
    had_errexit=1
    set +e
  fi
  output="$("$@" 2>&1)"
  rc=$?
  if [[ "${had_errexit}" -eq 1 ]]; then
    set -e
  fi

  diag_log "${component}" "${stage}" "probe=${label} rc=${rc} output=$(diag_compact_output "${output}")"
  return 0
}

diag_process_snapshot() {
  local component="$1"
  local stage="$2"
  local pattern="${3:-Xvnc|openbox|terminal64|wineserver|wine}"
  local had_errexit=0
  local output
  local rc

  if [[ $- == *e* ]]; then
    had_errexit=1
    set +e
  fi
  output="$(ps -eo pid=,ppid=,stat=,args= --sort=pid | awk -v pat="${pattern}" '$0 ~ pat {print}')"
  rc=$?
  if [[ "${had_errexit}" -eq 1 ]]; then
    set -e
  fi

  if [[ -z "${output}" ]]; then
    output="<no matching processes>"
  fi
  diag_log "${component}" "${stage}" "processes_rc=${rc} pattern=${pattern} snapshot=$(diag_compact_output "${output}")"
  return 0
}

diag_display_socket_path() {
  local display="${DISPLAY:-}"
  if [[ -z "${display}" || "${display}" != *:* ]]; then
    return 1
  fi

  local display_number="${display##*:}"
  display_number="${display_number%%.*}"
  if [[ -z "${display_number}" || ! "${display_number}" =~ ^[0-9]+$ ]]; then
    return 1
  fi

  printf '/tmp/.X11-unix/X%s' "${display_number}"
}

diag_display_probe() {
  local component="$1"
  local stage="$2"

  local socket_path="<unresolved>"
  local socket_state="display-unset-or-unparseable"
  if socket_path="$(diag_display_socket_path)"; then
    if [[ -S "${socket_path}" ]]; then
      socket_state="socket-present"
    elif [[ -e "${socket_path}" ]]; then
      socket_state="path-exists-not-socket"
    else
      socket_state="missing"
    fi
  fi
  diag_log "${component}" "${stage}" "x_socket=${socket_path} x_socket_state=${socket_state}"

  if command -v xdpyinfo >/dev/null 2>&1 && [[ -n "${DISPLAY:-}" ]]; then
    diag_run_probe "${component}" "${stage}" "xdpyinfo" xdpyinfo -display "${DISPLAY}"
  else
    diag_log "${component}" "${stage}" "probe=xdpyinfo skipped=1 reason=command-missing-or-display-unset"
  fi
}

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
