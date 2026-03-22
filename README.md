# NormProtokol MVP

Fullstack-проект (FastAPI + React/Vite), подготовленный для максимально простого деплоя на новом Ubuntu-сервере без ручного редактирования `docker-compose.yml` и `.env`.

---

## Быстрый запуск на новом сервере

### Вариант в 1 команду (если Docker уже установлен)

```bash
git clone <repo_url> && cd normProtokol && bash deploy.sh
```

### Вариант в 2 команды (рекомендуется для «чистого» сервера)

```bash
git clone <repo_url>
cd normProtokol
bash bootstrap.sh
bash deploy.sh
```

После запуска вы получите URL:
- Frontend: `http://<SERVER_IP>:<FRONTEND_PORT>`
- Backend docs: `http://<SERVER_IP>:<BACKEND_PORT>/docs`
- Health: `http://<SERVER_IP>:<BACKEND_PORT>/health`

---

## Что автоматизировано

`deploy.sh` автоматически:
- определяет IP сервера (`SERVER_IP=auto`),
- создает `backend/.env` из шаблона,
- создает корневой `.env` для Docker Compose,
- подставляет `CORS_ORIGINS` и `VITE_API_BASE_URL` под IP сервера,
- создает директории `data/uploads` и `data/generated`,
- проверяет Docker / Docker Compose,
- проверяет RAM и свободное место,
- проверяет занятость портов и при конфликте выбирает свободные,
- запускает `docker compose up -d --build`,
- выполняет post-deploy healthcheck.

`bootstrap.sh` автоматически:
- ставит `curl`, `git`, `docker.io`, `docker-compose-v2`, `ufw`,
- включает/перезапускает сервис Docker,
- добавляет пользователя в группу `docker`,
- добавляет правила UFW для портов 22/15173/18000,
- безопасен при повторном запуске (идемпотентен).

---

## Настройка параметров деплоя

По умолчанию `deploy.sh` использует встроенные значения.

Если нужна кастомизация — создайте `deploy.env`:

```bash
cp deploy.env.example deploy.env
```

Пример параметров:

```env
FRONTEND_PORT=15173
BACKEND_PORT=18000
APP_ENV=production
BITRIX_MODE=mock
SERVER_IP=auto
VITE_USE_MOCK_API=false
DEBUG=false
```

> Если `SERVER_IP=auto`, скрипт пытается определить внешний IP автоматически.

---

## Запуск по IP без домена

Сценарий «из коробки» работает без DNS/домена:
- Frontend собирается с `VITE_API_BASE_URL=http://<SERVER_IP>:<BACKEND_PORT>/api`.
- Backend получает `CORS_ORIGINS` с frontend URL по IP.
- Доступ к приложению сразу по адресу `http://<SERVER_IP>:<FRONTEND_PORT>`.

---

## Команды обслуживания

```bash
bash status.sh
```
Показывает:
- статус контейнеров,
- итоговые URL,
- проверку доступности frontend/backend.

```bash
bash logs.sh
bash logs.sh backend
bash logs.sh frontend
```
Логи сервисов (follow-режим).

```bash
bash update.sh
```
Обновление проекта (`git pull --rebase`) и redeploy.

```bash
bash clean.sh
```
Аккуратная очистка docker build cache, dangling images и неиспользуемых volumes.

---

## Диагностика проблем

Если `deploy.sh` сообщил ошибку:

1. Проверьте контейнеры:
   ```bash
   docker compose ps
   ```
2. Посмотрите логи:
   ```bash
   docker compose logs --tail=200 backend frontend
   ```
3. Запустите интегральную проверку:
   ```bash
   bash status.sh
   ```

Частые причины:
- мало RAM (особенно при сборке frontend),
- мало свободного места,
- заняты порты,
- Docker установлен, но пользователь не в группе `docker` (после `bootstrap.sh` нужен повторный вход).

---

## Архитектура сервисов

- **backend**: FastAPI (`/health`, `/docs`, `/api/*`), порт контейнера `8000`, наружу `${BACKEND_PORT}`.
- **frontend**: React/Vite (production build + Nginx), наружу `${FRONTEND_PORT}`.
- **data volume**: `./data` примонтирован в backend для БД/файлов.

---

## Разработка локально

Если нужен прежний dev-сценарий — можно запускать сервисы отдельно, но для серверного окружения рекомендуется только путь через `bootstrap.sh` + `deploy.sh`.
