# Protocol Normalizer Backend MVP

FastAPI backend for normalization of meeting protocols (`.docx`) and publishing tasks to Bitrix24 (mock/real mode).

## Stack
- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- Alembic
- SQLite
- python-docx
- pytest
- Docker / docker-compose

## Architecture (backend)
- `backend/app/api` — HTTP endpoints.
- `backend/app/services/parser` — docx text extraction.
- `backend/app/services/normalizer` — rule-based task extraction.
- `backend/app/services/topics` — topic matcher (dictionary score).
- `backend/app/services/validator` — protocol/task validation.
- `backend/app/services/exporter` — normalized docx generator.
- `backend/app/services/bitrix` — Bitrix abstraction + mock/real implementations.
- `backend/app/models`, `backend/app/db` — persistence layer.
- `backend/app/core` — configuration.

## Run locally
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Run with Docker
```bash
docker compose up --build
```

## Migrations
```bash
cd backend
alembic upgrade head
```

## Env vars
Use `.env.example`. Main variables:
- `DATABASE_URL`
- `UPLOADS_DIR`
- `GENERATED_DIR`
- `BITRIX_MODE=mock|real`
- `BITRIX_BASE_URL`, `BITRIX_WEBHOOK`
- `TOPIC_DICTIONARY_PATH`, `TASK_KEYWORDS_PATH`, `MOCK_USERS_PATH`
- `CORS_ORIGINS`

## Mock mode
Default mode is `mock`. Users are loaded from `data/mock_users.json`.

## API examples
```bash
curl -F "file=@/tmp/protocol.docx" http://localhost:8000/api/protocols/upload
curl http://localhost:8000/api/protocols/1/draft
curl -X POST http://localhost:8000/api/protocols/1/save-draft
curl -X POST http://localhost:8000/api/protocols/1/generate-docx
curl -X POST http://localhost:8000/api/protocols/1/validate
curl -X POST http://localhost:8000/api/protocols/1/publish
```

## Scenario
`upload -> edit tasks/topics -> save draft -> generate docx -> publish`

## Seeds
At startup backend creates missing seed files:
- `data/topics.json`
- `data/mock_users.json`
- `data/task_keywords.json`
