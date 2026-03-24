import json
from pathlib import Path


def ensure_seed_file(path: Path, payload: list | dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)


def _load_json_or_raise(path: Path, expected_type: type[list] | type[dict]) -> None:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        raise RuntimeError(f"Seed file '{path}' is unreadable or invalid JSON") from exc

    if not isinstance(data, expected_type):
        expected = "list" if expected_type is list else "dict"
        raise RuntimeError(f"Seed file '{path}' has invalid format, expected JSON {expected}")


def seed_data(topics_path: Path, users_path: Path, task_keywords_path: Path) -> None:
    ensure_seed_file(
        topics_path,
        [
            {
                "id": "topic_244",
                "title": "Проект 244",
                "keywords": ["244", "осаз", "хгкм", "интеграция"],
                "synonyms": ["проект 244", "узел 244"],
            }
        ],
    )
    ensure_seed_file(
        users_path,
        [
            {"id": "101", "name": "Иванов И.И."},
            {"id": "102", "name": "Петров П.П."},
            {"id": "103", "name": "Сидорова А.А."},
        ],
    )
    ensure_seed_file(
        task_keywords_path,
        {"keywords": ["поручить", "подготовить", "обеспечить", "направить", "согласовать", "выполнить", "предоставить", "организовать", "рассмотреть", "доработать", "завершить", "проработать"]},
    )

    _load_json_or_raise(topics_path, list)
    _load_json_or_raise(users_path, list)
    _load_json_or_raise(task_keywords_path, dict)
