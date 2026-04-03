#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./http-env.sh
source "${SCRIPT_DIR}/http-env.sh"

ensure_http_dirs
require_http_runtime
# HTTP service starts without MT5 credentials.
# Terminal initialization and account login are now driven by HTTP APIs.

if http_pid_is_running; then
  http_log "HTTP service is already running"
  exit 0
fi

rm -f "${HTTP_PID_FILE}"

bash "${SCRIPT_DIR}/http-sync-deps.sh"
resolve_service_paths

http_log "starting HTTP service"
(
  trap '' HUP
  cd "${SERVICE_ROOT}"
  exec </dev/null > >(http_copy_to_container_logs) 2>&1
  run_gui wine "${SERVICE_VENV_PYTHON_LINUX}" "${SERVICE_MAIN_WIN}" \
    --env "${HTTP_ENV}" \
    --port "${HTTP_PORT}"
) &

HTTP_PID=$!
printf '%s\n' "${HTTP_PID}" >"${HTTP_PID_FILE}"

for _ in $(seq 1 "${HTTP_BOOT_TIMEOUT}"); do
  if ! kill -0 "${HTTP_PID}" 2>/dev/null; then
    rm -f "${HTTP_PID_FILE}"
    http_fail "HTTP service exited before becoming ready; check ${HTTP_LOG_FILE}"
  fi

  if curl -fsS --max-time 2 "http://127.0.0.1:${HTTP_PORT}/" >/dev/null 2>&1; then
    http_log "HTTP service started with pid ${HTTP_PID}"
    exit 0
  fi
  sleep 1
done

if kill -0 "${HTTP_PID}" 2>/dev/null; then
  kill "${HTTP_PID}" >/dev/null 2>&1 || true
fi
rm -f "${HTTP_PID_FILE}"
http_fail "HTTP service did not become ready on port ${HTTP_PORT}; check ${HTTP_LOG_FILE}"
