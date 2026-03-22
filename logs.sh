#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

SERVICE="${1:-}"
TAIL="${TAIL:-200}"

case "${SERVICE}" in
  backend|frontend)
    docker compose logs -f --tail="${TAIL}" "${SERVICE}"
    ;;
  "")
    docker compose logs -f --tail="${TAIL}" backend frontend
    ;;
  *)
    echo "Использование: bash logs.sh [backend|frontend]"
    exit 1
    ;;
esac
