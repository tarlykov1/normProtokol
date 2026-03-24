#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

SERVER_IP="${SERVER_IP:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-15173}"
BACKEND_PORT="${BACKEND_PORT:-18000}"
VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://127.0.0.1:18000/api}"

FRONTEND_URL="http://${SERVER_IP}:${FRONTEND_PORT}"
BACKEND_URL="http://${SERVER_IP}:${BACKEND_PORT}"
EXPECTED_API_BASE_URL="${BACKEND_URL}/api"

echo "[status] Containers:"
docker compose ps

echo
echo "[status] URLs:"
echo "- Frontend: ${FRONTEND_URL}"
echo "- Backend docs: ${BACKEND_URL}/docs"
echo "- Health: ${BACKEND_URL}/health"
echo "- VITE_API_BASE_URL (.env): ${VITE_API_BASE_URL}"
echo "- Expected API URL: ${EXPECTED_API_BASE_URL}"

echo
echo "[status] Health checks:"
if curl -fsS --max-time 7 "${BACKEND_URL}/health" >/dev/null; then
  echo "- backend health: OK"
else
  echo "- backend health: FAIL"
fi

if curl -fsS --max-time 7 "${BACKEND_URL}/openapi.json" | grep -q "\"/api/protocols/upload\""; then
  echo "- upload api: OK"
else
  echo "- upload api: FAIL"
fi

if curl -fsS --max-time 7 "${FRONTEND_URL}" >/dev/null; then
  echo "- frontend: OK"
else
  echo "- frontend: FAIL"
fi

if [[ "${VITE_API_BASE_URL}" == "${EXPECTED_API_BASE_URL}" ]]; then
  echo "- api env consistency: OK"
else
  echo "- api env consistency: FAIL (ожидалось ${EXPECTED_API_BASE_URL})"
fi
