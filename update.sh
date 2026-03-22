#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

echo "[update] git pull --rebase"
git pull --rebase

echo "[update] redeploy"
bash deploy.sh
