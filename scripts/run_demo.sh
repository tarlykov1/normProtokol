#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "[demo] Starting stack (detached)..."
docker compose -f "$ROOT_DIR/docker-compose.yml" up -d --build

echo "[demo] Waiting backend on http://localhost:8000/health ..."
for i in {1..30}; do
  if curl -fsS http://localhost:8000/health >/dev/null; then
    break
  fi
  sleep 1
done

echo "[demo] Bootstrapping demo protocol..."
RESP="$(curl -fsS -X POST http://localhost:8000/api/demo/bootstrap)"
PROTOCOL_ID="$(python - <<'PY'
import json,sys
print(json.loads(sys.stdin.read())["id"])
PY
<<< "$RESP")"

echo "[demo] Ready!"
echo "- Frontend: http://localhost:5173/upload"
echo "- Open directly: http://localhost:5173/normalize?protocolId=${PROTOCOL_ID}"
echo "- Confirm page:  http://localhost:5173/confirm?protocolId=${PROTOCOL_ID}"
