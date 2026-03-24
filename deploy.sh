#!/usr/bin/env bash
set -euo pipefail

log() { echo "[deploy] $*"; }
warn() { echo "[deploy][warn] $*"; }
err() { echo "[deploy][error] $*" >&2; }

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

if [[ -f deploy.env ]]; then
  log "Загружаю настройки из deploy.env"
  set -a
  # shellcheck disable=SC1091
  source deploy.env
  set +a
else
  log "deploy.env не найден, использую defaults (см. deploy.env.example)"
fi

FRONTEND_PORT="${FRONTEND_PORT:-15173}"
BACKEND_PORT="${BACKEND_PORT:-18000}"
APP_ENV="${APP_ENV:-production}"
BITRIX_MODE="${BITRIX_MODE:-mock}"
SERVER_IP="${SERVER_IP:-auto}"
VITE_USE_MOCK_API="${VITE_USE_MOCK_API:-false}"
DEBUG="${DEBUG:-false}"
DISK_WARN_MB="${DISK_WARN_MB:-4096}"
DISK_MIN_MB="${DISK_MIN_MB:-2048}"
RAM_WARN_MB="${RAM_WARN_MB:-2048}"
AUTO_SWITCH_PORTS="${AUTO_SWITCH_PORTS:-false}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    err "Не найдена команда '$1'. Запустите сначала: bash bootstrap.sh"
    exit 1
  fi
}

require_cmd docker
require_cmd curl
if ! docker compose version >/dev/null 2>&1; then
  err "docker compose plugin не найден. Запустите: bash bootstrap.sh"
  exit 1
fi

if [[ ! -f backend/.env.template ]]; then
  err "Не найден backend/.env.template"
  exit 1
fi

if ! [[ "${FRONTEND_PORT}" =~ ^[0-9]+$ && "${BACKEND_PORT}" =~ ^[0-9]+$ ]]; then
  err "FRONTEND_PORT и BACKEND_PORT должны быть числами"
  exit 1
fi

if docker compose ps -q | grep -q .; then
  log "Останавливаю текущие контейнеры перед проверкой портов, чтобы избежать ложной смены портов..."
  docker compose down --remove-orphans
fi

check_port_free() {
  local port="$1"
  if ss -ltn "( sport = :${port} )" | tail -n +2 | grep -q .; then
    return 1
  fi
  return 0
}

find_free_port() {
  local start="$1"
  local port
  for ((port=start; port<start+200; port++)); do
    if check_port_free "${port}"; then
      echo "${port}"
      return 0
    fi
  done
  return 1
}

handle_busy_port() {
  local var_name="$1"
  local value="$2"
  if [[ "${AUTO_SWITCH_PORTS}" == "true" ]]; then
    warn "Порт ${var_name}=${value} занят. Ищу свободный, так как AUTO_SWITCH_PORTS=true..."
    find_free_port "$((value + 1))"
    return 0
  fi
  err "Порт ${var_name}=${value} занят. Автопереключение отключено (AUTO_SWITCH_PORTS=false)."
  err "Освободите порт или задайте другой в deploy.env, затем перезапустите deploy.sh."
  err "Если нужно старое поведение, запустите с AUTO_SWITCH_PORTS=true."
  exit 1
}

if ! check_port_free "${FRONTEND_PORT}"; then
  FRONTEND_PORT="$(handle_busy_port "FRONTEND_PORT" "${FRONTEND_PORT}")"
  warn "Выбран новый FRONTEND_PORT=${FRONTEND_PORT}"
fi

if ! check_port_free "${BACKEND_PORT}"; then
  BACKEND_PORT="$(handle_busy_port "BACKEND_PORT" "${BACKEND_PORT}")"
  warn "Выбран новый BACKEND_PORT=${BACKEND_PORT}"
fi

AVAILABLE_DISK_MB="$(df -Pm . | awk 'NR==2 {print $4}')"
if (( AVAILABLE_DISK_MB < DISK_MIN_MB )); then
  err "Недостаточно места на диске: ${AVAILABLE_DISK_MB}MB (минимум ${DISK_MIN_MB}MB)"
  exit 1
elif (( AVAILABLE_DISK_MB < DISK_WARN_MB )); then
  warn "Мало свободного места: ${AVAILABLE_DISK_MB}MB. Рекомендуется >= ${DISK_WARN_MB}MB"
else
  log "Свободное место: ${AVAILABLE_DISK_MB}MB"
fi

TOTAL_RAM_MB="$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)"
if (( TOTAL_RAM_MB < RAM_WARN_MB )); then
  warn "RAM ${TOTAL_RAM_MB}MB. На слабых серверах сборка frontend может быть медленной/тяжелой."
else
  log "RAM: ${TOTAL_RAM_MB}MB"
fi

detect_server_ip() {
  local ip
  if [[ "${SERVER_IP}" != "auto" ]]; then
    echo "${SERVER_IP}"
    return 0
  fi

  ip="$(curl -4fsS --max-time 5 https://api.ipify.org || true)"
  if [[ -n "${ip}" ]]; then
    echo "${ip}"
    return 0
  fi

  ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  if [[ -n "${ip}" ]]; then
    echo "${ip}"
    return 0
  fi

  echo "127.0.0.1"
}

SERVER_IP="$(detect_server_ip)"
log "SERVER_IP=${SERVER_IP}"

FRONTEND_URL="http://${SERVER_IP}:${FRONTEND_PORT}"
BACKEND_BASE_URL="http://${SERVER_IP}:${BACKEND_PORT}"
VITE_API_BASE_URL="${BACKEND_BASE_URL}/api"
CORS_ORIGINS="${FRONTEND_URL},http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}"

mkdir -p data/uploads data/generated backend/data

cat > backend/.env <<EOF
APP_NAME=Protocol Normalizer MVP
APP_ENV=${APP_ENV}
DEBUG=${DEBUG}
DATABASE_URL=sqlite:///./data/app.db
UPLOADS_DIR=./data/uploads
GENERATED_DIR=./data/generated
TOPIC_DICTIONARY_PATH=./data/topics.json
TASK_KEYWORDS_PATH=./data/task_keywords.json
MOCK_USERS_PATH=./data/mock_users.json
BITRIX_MODE=${BITRIX_MODE}
BITRIX_BASE_URL=
BITRIX_WEBHOOK=
AUTOSAVE_ENABLED=true
TOPIC_MATCH_THRESHOLD=0.34
TOPIC_REQUIRED_AS_ERROR=false
CORS_ORIGINS=${CORS_ORIGINS}
EOF

cat > .env <<EOF
FRONTEND_PORT=${FRONTEND_PORT}
BACKEND_PORT=${BACKEND_PORT}
VITE_API_BASE_URL=${VITE_API_BASE_URL}
VITE_USE_MOCK_API=${VITE_USE_MOCK_API}
SERVER_IP=${SERVER_IP}
EOF

log "Сгенерированы backend/.env и .env"

if [[ "${VITE_API_BASE_URL}" != "${BACKEND_BASE_URL}/api" ]]; then
  err "Несогласованный VITE_API_BASE_URL=${VITE_API_BASE_URL} (ожидалось ${BACKEND_BASE_URL}/api)"
  exit 1
fi

log "Запускаю docker compose up -d --build ..."
docker compose up -d --build

sleep 3

log "Проверяю статус контейнеров..."
docker compose ps

HEALTH_OK=1
if ! curl -fsS --max-time 10 "${BACKEND_BASE_URL}/health" >/dev/null; then
  HEALTH_OK=0
  warn "Backend healthcheck не прошел: ${BACKEND_BASE_URL}/health"
fi

if ! curl -fsS --max-time 10 "${FRONTEND_URL}" >/dev/null; then
  HEALTH_OK=0
  warn "Frontend недоступен: ${FRONTEND_URL}"
fi

if ! curl -fsS --max-time 10 "${BACKEND_BASE_URL}/openapi.json" | grep -q "\"/api/protocols/upload\""; then
  HEALTH_OK=0
  warn "Upload API недоступен или OpenAPI не содержит /api/protocols/upload"
fi

echo
log "Деплой завершен."
log "Frontend URL: ${FRONTEND_URL}"
log "Backend docs: ${BACKEND_BASE_URL}/docs"
log "Healthcheck: ${BACKEND_BASE_URL}/health"

if [[ "${HEALTH_OK}" -ne 1 ]]; then
  warn "Есть проблемы с доступностью сервисов. Диагностика:"
  warn "Последние логи backend:"
  docker compose logs --tail=200 backend || true
  warn "Последние логи frontend:"
  docker compose logs --tail=120 frontend || true
  warn "- docker compose ps"
  warn "- docker compose logs --tail=200 backend frontend"
  warn "- bash status.sh"
  exit 1
fi
