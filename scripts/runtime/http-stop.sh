#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./http-env.sh
source "${SCRIPT_DIR}/http-env.sh"

ensure_http_dirs

stopped=0

if [[ -f "${HTTP_PID_FILE}" ]]; then
  HTTP_PID="$(tr -d '[:space:]' <"${HTTP_PID_FILE}")"
  if [[ -n "${HTTP_PID}" ]] && kill -0 "${HTTP_PID}" 2>/dev/null; then
    http_log "stopping HTTP service pid ${HTTP_PID}"
    kill "${HTTP_PID}" >/dev/null 2>&1 || true
    for _ in $(seq 1 10); do
      if ! kill -0 "${HTTP_PID}" 2>/dev/null; then
        stopped=1
        break
      fi
      sleep 1
    done
    if kill -0 "${HTTP_PID}" 2>/dev/null; then
      kill -9 "${HTTP_PID}" >/dev/null 2>&1 || true
      stopped=1
    fi
  fi
  rm -f "${HTTP_PID_FILE}"
fi

for pid in $(collect_http_pids); do
  if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
    http_log "stopping fallback HTTP pid ${pid}"
    kill "${pid}" >/dev/null 2>&1 || true
    sleep 1
    if kill -0 "${pid}" 2>/dev/null; then
      kill -9 "${pid}" >/dev/null 2>&1 || true
    fi
    stopped=1
  fi
done

rm -f "${HTTP_PID_FILE}"

if [[ "${stopped}" -eq 1 ]]; then
  http_log "HTTP service stopped"
else
  http_log "HTTP service is not running"
fi
