#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

log() {
  printf '[runtime][launch] %s\n' "$*"
}

fail() {
  printf '[runtime][launch][error] %s\n' "$*" >&2
  exit 1
}

export WINEPREFIX="${WINEPREFIX:-/config/.wine}"
export WINEDEBUG="${WINEDEBUG:--all}"
export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-winemenubuilder.exe=d}"

MT5_LINUX_EXE="${MT5_TERMINAL_PATH:-${WINEPREFIX}/drive_c/Program Files/MetaTrader 5/terminal64.exe}"
MT5_PORTABLE="${MT5_PORTABLE:-true}"
MT5_LOG_DIR="/config/logs"
MT5_LOG_FILE="${MT5_LOG_DIR}/mt5.log"

mkdir -p "${MT5_LOG_DIR}" || fail "failed to create log directory: ${MT5_LOG_DIR}"

diag_log "launch" "entry" "mt5_linux_exe=${MT5_LINUX_EXE} portable=${MT5_PORTABLE} mt5_log_file=${MT5_LOG_FILE}"
diag_display_probe "launch" "entry"
diag_process_snapshot "launch" "entry"

if pgrep -fa terminal64.exe >/dev/null; then
  diag_run_probe "launch" "already-running" "pgrep-terminal64" pgrep -fa terminal64.exe
  log "MetaTrader 5 is already running"
  exit 0
fi

[[ -f "${MT5_LINUX_EXE}" ]] || fail "terminal64.exe not found: ${MT5_LINUX_EXE}"

log "launching MetaTrader 5"
if [[ "${MT5_PORTABLE}" == "true" ]]; then
  wine "${MT5_LINUX_EXE}" /portable >>"${MT5_LOG_FILE}" 2>&1 &
else
  wine "${MT5_LINUX_EXE}" >>"${MT5_LOG_FILE}" 2>&1 &
fi

MT5_LAUNCH_PID=$!
diag_log "launch" "spawned" "launcher_pid=${MT5_LAUNCH_PID}"

last_delay=0
for delay in 1 3 5; do
  sleep "$((delay - last_delay))"
  diag_run_probe "launch" "post-spawn-${delay}s" "pgrep-terminal64" pgrep -fa terminal64.exe
  diag_process_snapshot "launch" "post-spawn-${delay}s"
  last_delay="${delay}"
done
