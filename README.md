# Protocol Normalizer MVP (FastAPI + React)

MVP веб-инструмента для загрузки «грязных» `.docx` протоколов, выделения задач-кандидатов, ручной нормализации, сохранения черновиков, генерации итогового Word и публикации в Bitrix24 (mock mode по умолчанию).

## 1) Архитектура

### Backend (FastAPI)
Модульная структура:
- `parser`: извлечение текста из `.docx`, поиск задач-кандидатов, эвристики по исполнителю/сроку.
- `normalizer`: детерминированная нормализация текста.
- `validator`: правила валидации задач и поиск дублей.
- `exporter`: генерация нормализованного `.docx` через `python-docx`.
- `bitrix integration`: `BitrixService` (mock mode / реальная интеграция расширяется позже).
- `api`: REST endpoints для CRUD, массовых операций, draft, validate, publish.
- `db`: SQLAlchemy + Alembic + SQLite.

### Frontend (React + TypeScript)
5 рабочих экранов:
1. Upload
2. Нормализация (inline-редактирование, массовые операции)
3. Группировка по темам (drag-and-drop)
4. Подтверждение
5. Результат публикации

Автосохранение черновика: каждые 10 секунд вызывается `save-draft`.
Сессия восстанавливается через `localStorage(lastProtocolId)` + `GET /draft`.

## 2) Структура каталогов

```text
backend/
  app/
    api/routes.py
    core/config.py
    db/{session.py,seed.py}
    models/{base.py,entities.py}
    schemas/common.py
    services/
      parser/{docx_parser.py,task_extractor.py}
      normalizer/text_normalizer.py
      validator/task_validator.py
      exporter/docx_exporter.py
      bitrix/bitrix_service.py
    data/topics.json
    main.py
  alembic/
    env.py
    versions/0001_init.py
  requirements.txt
frontend/
  src/
    api/client.ts
    pages/App.tsx
    types/index.ts
    styles.css
  package.json
  Dockerfile
docker-compose.yml
.env.example
README.md
```

## 3) Быстрый запуск

### Локально без Docker
```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Во втором терминале:
```bash
cd frontend
npm install
npm run dev
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

### Через Docker Compose
```bash
docker-compose up --build
```

## 4) Конфигурация (.env)
См. `.env.example`.
Ключевые параметры:
- `DATABASE_URL` — SQLite URL
- `TOPIC_DICTIONARY_PATH` — словарь тем
- `BITRIX_MOCK_MODE=true` — включен mock сотрудников и публикации
- `BITRIX_WEBHOOK_URL` — для реальной интеграции

## 5) API (основные endpoints)

### Upload + parse
- `POST /api/protocols/upload` (multipart file `.docx`)

### Task editing
- `GET /api/protocols/{id}`
- `PATCH /api/tasks/{id}`
- `POST /api/tasks`
- `DELETE /api/tasks/{id}`
- `POST /api/tasks/{id}/split`
- `POST /api/tasks/merge`
- `POST /api/tasks/reorder`
- `POST /api/tasks/move-to-topic`

### Assignee / bulk
- `GET /api/assignees/search?q=`
- `POST /api/tasks/{id}/assign`
- `POST /api/tasks/bulk-assign`
- `POST /api/tasks/bulk-topic`
- `POST /api/tasks/bulk-deadline`

### Draft + restore
- `POST /api/protocols/{id}/save-draft`
- `GET /api/protocols/{id}/draft`

### Export + publish
- `POST /api/protocols/{id}/generate-docx`
- `GET /api/protocols/{id}/download-docx`
- `POST /api/protocols/{id}/validate`
- `POST /api/protocols/{id}/publish`

## 6) Примеры запросов

```bash
# upload
curl -F "file=@./sample.docx" http://localhost:8000/api/protocols/upload

# validate
curl -X POST http://localhost:8000/api/protocols/1/validate

# generate docx
curl -X POST http://localhost:8000/api/protocols/1/generate-docx

# publish
curl -X POST http://localhost:8000/api/protocols/1/publish
```

## 7) Тесты

```bash
PYTHONPATH=backend pytest backend/tests -q
```

Покрыты минимальные юнит-тесты:
- parser/topic matcher
- validator

## 8) Seed / mock данные

- Словарь тем: `backend/app/data/topics.json`
- Mock пользователи Bitrix24: `backend/app/services/bitrix/bitrix_service.py`

При необходимости расширения:
- добавить реальные REST-вызовы Bitrix24 в `BitrixService`
- вынести тему/ключевые слова в БД + UI справочник
- добавить optimistic locking/revision для черновиков
