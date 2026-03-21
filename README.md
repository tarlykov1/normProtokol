# NormProtokol MVP

End-to-end локальный MVP для нормализации протоколов совещаний из `.docx`, редактирования задач и публикации в Bitrix24 (mock/real abstraction).

## 1) Архитектура

### Контур
- **Frontend (React + TS + Vite)** — UI для загрузки, нормализации, board-view по темам, валидации и публикации.
- **Backend (FastAPI + SQLAlchemy + SQLite)** — source of truth, парсинг/эвристики, сохранение draft, генерация Word, публикация в Bitrix.
- **Storage (локальные файлы)**:
  - `data/uploads` — исходные `.docx`
  - `data/generated` — нормализованные документы для скачивания
  - `data/*.json` — словари тем, ключевые слова, mock users
- **DB (SQLite)** — протоколы, темы, задачи, audit log.

### Поток данных
1. Upload `.docx` -> backend сохраняет файл и извлекает текст.
2. Rule-based parser выделяет задачи-кандидаты, сроки, исполнителей, тему (best + candidates + confidence).
3. Frontend редактирует сущности inline, autosave вызывает `save-draft`.
4. Backend хранит состояние draft (источник истины), восстанавливает по `GET /protocols/{id}/draft`.
5. Генерация Word: `POST /generate-docx`, скачивание `GET /download-docx`.
6. Publish: backend вызывает mock/real Bitrix service, сохраняет IDs и статус публикации.

## 2) Структура проекта

```text
project-root/
  backend/
    app/
      api/
      core/
      db/
      models/
      repositories/
      schemas/
      services/
        bitrix/
        exporter/
        normalizer/
        parser/
        topics/
        validator/
      utils/
    alembic/
    tests/
      fixtures/sample_protocol.docx.b64
    .env.example
    requirements.txt
    Dockerfile
    README.md
  frontend/
    src/
      app/
      pages/
      features/
      shared/
      types/
    public/
    .env.example
    package.json
    Dockerfile
    README.md
  data/
    uploads/
    generated/
    topics.json
    task_keywords.json
    mock_users.json
  docker-compose.yml
  README.md
```

## 3) Быстрый старт (docker compose)

```bash
docker compose up --build
```

Открыть:
- Frontend: `http://localhost:5173`
- Backend OpenAPI: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## 4) Проверка сквозного сценария

1. Откройте frontend.
2. Загрузите `.docx`.
3. Проверьте задачи на странице Normalize (текст/тема/исполнитель/срок).
4. Нажмите Save Draft (или дождитесь autosave).
5. Generate Word -> Download Word.
6. Publish -> проверьте Result page (smart process id, опубликованные/пропущенные задачи).
7. Перезагрузите страницу и откройте тот же протокол — draft и generated docx доступны повторно.

## 5) API (основное)

- `POST /api/protocols/upload`
- `GET /api/protocols`
- `GET /api/protocols/{id}`
- `GET /api/protocols/{id}/draft`
- `POST /api/protocols/{id}/save-draft`
- `POST /api/protocols/{id}/validate`
- `POST /api/protocols/{id}/generate-docx`
- `GET /api/protocols/{id}/download-docx`
- `POST /api/protocols/{id}/publish`
- Tasks/Topics CRUD + split/merge/reorder/move/bulk-assign
- `GET /api/assignees/search?q=`

## 6) Ограничения MVP

- Только `.docx` (без PDF/TXT пока).
- Только rule-based parse (без LLM/ML).
- Mock Bitrix включен по умолчанию (`BITRIX_MODE=mock`).

## 7) Расширение

- Подключить `RealBitrixService` и webhook.
- Улучшить словари тем/синонимов и regex/эвристики.
- Добавить workflow ролей/подписания и более глубокий audit trail.

## Демо-режим для просмотра

Быстрый вариант из репозитория: `./scripts/run_demo.sh` (поднимает стек и создает демо-протокол автоматически). Подробно: `docs/DEMO.md`.

### Вариант 1 (backend + frontend)
1. Запустите `docker compose up --build`.
2. На странице Upload нажмите **"Открыть демо"**.
3. Система создаст демо-протокол через `POST /api/demo/bootstrap` и откроет Normalize.
4. Проверьте inline-редактирование, save draft, validate, generate/download docx и publish.

### Вариант 2 (frontend без backend)
```bash
cd frontend
VITE_USE_MOCK_API=true npm run dev
```
В этом режиме UI работает на `mockApi` и подходит для быстрого UX smoke-test.
