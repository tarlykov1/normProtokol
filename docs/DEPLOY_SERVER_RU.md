# Развертывание NormProtokol на сервере (Ubuntu + Docker)

Ниже — практичный production-сценарий для VPS/выделенного сервера с Linux.

## 1) Что понадобится

- Сервер Ubuntu 22.04/24.04 (минимум 2 CPU, 4 GB RAM, 20+ GB disk).
- Домен (например, `norm.example.com`) с A-записью на IP сервера.
- Доступ по SSH под пользователем с `sudo`.

## 2) Подготовка сервера

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg git nginx certbot python3-certbot-nginx
```

Установите Docker и плагин Compose:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo apt install -y docker-compose-plugin
```

> После добавления в группу `docker` перелогиньтесь в SSH-сессию.

## 3) Клонирование проекта

```bash
cd /opt
sudo git clone <ВАШ_GIT_URL> normProtokol
sudo chown -R $USER:$USER /opt/normProtokol
cd /opt/normProtokol
```

## 4) Настройка backend окружения

В `docker-compose.yml` backend уже читает переменные из `backend/.env.example`,
но для сервера лучше создать отдельный файл `backend/.env`.

```bash
cp backend/.env.example backend/.env
```

Минимально проверьте/измените в `backend/.env`:

- `CORS_ORIGINS` — укажите ваш frontend-домен (например `https://norm.example.com`).
- `BITRIX_MODE` — `mock` для теста или `real` для боевого Bitrix.
- `DATABASE_URL` — по умолчанию SQLite, для MVP этого достаточно.

## 5) Настройка frontend API URL

В `docker-compose.yml` для frontend по умолчанию стоит:

- `VITE_API_BASE_URL=http://localhost:8000/api`

Для сервера измените на публичный адрес backend через ваш домен (удобнее через `/api` на том же домене):

- `VITE_API_BASE_URL=https://norm.example.com/api`

## 6) Запуск контейнеров

```bash
docker compose up -d --build
```

Проверка:

```bash
docker compose ps
curl -f http://127.0.0.1:8000/health
```

## 7) Reverse proxy через Nginx

Создайте конфиг `/etc/nginx/sites-available/normprotokol`:

```nginx
server {
    listen 80;
    server_name norm.example.com;

    client_max_body_size 25m;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:5173/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Включение конфига:

```bash
sudo ln -s /etc/nginx/sites-available/normprotokol /etc/nginx/sites-enabled/normprotokol
sudo nginx -t
sudo systemctl reload nginx
```

## 8) SSL (Let's Encrypt)

```bash
sudo certbot --nginx -d norm.example.com --redirect -m you@example.com --agree-tos -n
```

Проверка автопродления:

```bash
systemctl status certbot.timer
```

## 9) Обновление проекта

```bash
cd /opt/normProtokol
git pull
docker compose up -d --build
```

## 10) Полезная диагностика

```bash
docker compose logs -f backend
docker compose logs -f frontend
curl -I https://norm.example.com
curl -I https://norm.example.com/api/health
```

## 11) Минимальный production-hardening (рекомендовано)

- Закрыть входящие порты, оставить только `22`, `80`, `443` (через UFW/Cloud firewall).
- Делать бэкап директории `data/` (там SQLite и загруженные/сгенерированные файлы).
- Периодически обновлять образы и ОС (`apt upgrade`, `docker compose build --pull`).
- Если нагрузка вырастет — вынести БД из SQLite в PostgreSQL.

---

Если хотите, могу дать второй вариант: **без Nginx**, только через Cloudflare Tunnel/Traefik, либо подготовить готовые файлы `docker-compose.prod.yml` и `nginx.conf` под ваш домен.
