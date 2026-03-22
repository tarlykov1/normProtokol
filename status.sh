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

FRONTEND_URL="http://${SERVER_IP}:${FRONTEND_PORT}"
BACKEND_URL="http://${SERVER_IP}:${BACKEND_PORT}"

echo "[status] Containers:"
docker compose ps

echo
echo "[status] URLs:"
echo "- Frontend: ${FRONTEND_URL}"
echo "- Backend docs: ${BACKEND_URL}/docs"
echo "- Health: ${BACKEND_URL}/health"

echo
echo "[status] Health checks:"
if curl -fsS --max-time 7 "${BACKEND_URL}/health" >/dev/null; then
  echo "- backend health: OK"
else
  echo "- backend health: FAIL"
fi

if curl -fsS --max-time 7 "${FRONTEND_URL}" >/dev/null; then
  echo "- frontend: OK"
else
  echo "- frontend: FAIL"
fi
