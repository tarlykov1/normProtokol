#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

echo "[clean] Останавливаю контейнеры проекта..."
docker compose down --remove-orphans

echo "[clean] Удаляю dangling образы и build cache..."
docker image prune -f
docker builder prune -f

echo "[clean] Удаляю неиспользуемые volumes (осторожно: глобальная операция)..."
docker volume prune -f

echo "[clean] Готово"
