#!/usr/bin/env bash
set -euo pipefail

log() { echo "[bootstrap] $*"; }
warn() { echo "[bootstrap][warn] $*"; }
err() { echo "[bootstrap][error] $*" >&2; }

if [[ "${EUID}" -ne 0 ]]; then
  SUDO="sudo"
else
  SUDO=""
fi

if ! command -v apt-get >/dev/null 2>&1; then
  err "Этот скрипт поддерживает только Ubuntu/Debian (apt-get)."
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

log "Обновляю индекс пакетов..."
${SUDO} apt-get update -y

log "Устанавливаю базовые пакеты (curl, git, ca-certificates, gnupg, ufw)..."
${SUDO} apt-get install -y curl git ca-certificates gnupg lsb-release ufw

if ! command -v docker >/dev/null 2>&1; then
  log "Docker не найден. Устанавливаю docker.io и compose plugin из Ubuntu репозитория..."
  ${SUDO} apt-get install -y docker.io docker-compose-v2
else
  log "Docker уже установлен: $(docker --version)"
  if ! docker compose version >/dev/null 2>&1; then
    log "docker compose plugin отсутствует. Устанавливаю docker-compose-v2..."
    ${SUDO} apt-get install -y docker-compose-v2
  fi
fi

log "Проверяю, запущен ли сервис Docker..."
${SUDO} systemctl enable docker >/dev/null 2>&1 || true
${SUDO} systemctl restart docker

TARGET_USER="${SUDO_USER:-$USER}"
if id -nG "${TARGET_USER}" | tr ' ' '\n' | grep -qx docker; then
  log "Пользователь ${TARGET_USER} уже состоит в группе docker."
else
  log "Добавляю пользователя ${TARGET_USER} в группу docker..."
  ${SUDO} usermod -aG docker "${TARGET_USER}"
  warn "Для применения группы docker может потребоваться перелогиниться (или выполнить 'newgrp docker')."
fi

log "Настраиваю UFW (если активен/доступен) — открываю 22/tcp, 15173/tcp, 18000/tcp..."
${SUDO} ufw allow 22/tcp >/dev/null 2>&1 || true
${SUDO} ufw allow 15173/tcp >/dev/null 2>&1 || true
${SUDO} ufw allow 18000/tcp >/dev/null 2>&1 || true

if ${SUDO} ufw status | grep -qi inactive; then
  warn "UFW установлен, но не активирован. При необходимости включите вручную: sudo ufw enable"
else
  log "UFW активен, правила обновлены."
fi

log "Готово. Проверки:"
log "- docker: $(docker --version 2>/dev/null || echo 'не найден')"
log "- docker compose: $(docker compose version 2>/dev/null || echo 'не найден')"
