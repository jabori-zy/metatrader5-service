#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./http-env.sh
source "${SCRIPT_DIR}/http-env.sh"

ensure_http_dirs
require_http_runtime
ensure_mt5_running

if http_pid_is_running; then
  http_log "HTTP service is already running"
  exit 0
fi

"${SCRIPT_DIR}/http-sync-deps.sh"
resolve_service_paths

http_log "starting HTTP service"
(
  cd "${SERVICE_ROOT}"
  run_gui wine "${SERVICE_VENV_PYTHON_LINUX}" "${SERVICE_MAIN_WIN}" \
    --env "${HTTP_ENV}" \
    --port "${HTTP_PORT}" \
    --terminal-path "${MT5_TERMINAL_PATH}" \
    --login "${MT5_LOGIN}" \
    --password "${MT5_PASSWORD}" \
    --server "${MT5_SERVER}"
) >>"${HTTP_LOG_FILE}" 2>&1 &

HTTP_PID=$!
printf '%s\n' "${HTTP_PID}" >"${HTTP_PID_FILE}"

for _ in $(seq 1 "${HTTP_BOOT_TIMEOUT}"); do
  if kill -0 "${HTTP_PID}" 2>/dev/null; then
    http_log "HTTP service started with pid ${HTTP_PID}"
    exit 0
  fi
  sleep 1
done

rm -f "${HTTP_PID_FILE}"
http_fail "HTTP service failed to stay running; check ${HTTP_LOG_FILE}"
