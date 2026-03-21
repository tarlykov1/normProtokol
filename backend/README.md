# Backend (FastAPI)

## Stack
- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- Alembic
- SQLite
- python-docx
- pytest

## Локальный запуск
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Важные директории
- `app/api` — endpoints
- `app/models` — ORM модели
- `app/schemas` — DTO/Pydantic
- `app/services/parser` — чтение docx
- `app/services/normalizer` — rule-based извлечение задач
- `app/services/topics` — словарное сопоставление тем
- `app/services/validator` — ошибки/предупреждения
- `app/services/exporter` — генерация нормализованного docx
- `app/services/bitrix` — mock/real integration layer
- `tests` — unit-тесты, включая docx fixture

## Конфигурация
См. `.env.example`.
Ключевые переменные:
- `DATABASE_URL`
- `UPLOADS_DIR`
- `GENERATED_DIR`
- `TOPIC_DICTIONARY_PATH`
- `TASK_KEYWORDS_PATH`
- `MOCK_USERS_PATH`
- `BITRIX_MODE` (`mock`/`real`)
- `CORS_ORIGINS`

## Тесты
```bash
cd backend
pytest -q
```
