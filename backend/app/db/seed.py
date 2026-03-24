import json
from datetime import datetime, timezone
from pathlib import Path


def ensure_seed_file(path: Path, payload: list | dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        _write_seed_file(path, payload)


def _write_seed_file(path: Path, payload: list | dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _repair_seed_file(path: Path, payload: list | dict, reason: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak-{ts}")
    if path.exists():
        path.rename(backup)
        print(f"[seed] Invalid seed file moved to backup: {backup} ({reason})", flush=True)
    else:
        print(f"[seed] Creating missing seed file: {path} ({reason})", flush=True)
    _write_seed_file(path, payload)


def _load_json_or_repair(path: Path, payload: list | dict, expected_type: type[list] | type[dict]) -> None:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        _repair_seed_file(path, payload, f"invalid JSON: {exc}")
        return

    if not isinstance(data, expected_type):
        expected = "list" if expected_type is list else "dict"
        _repair_seed_file(path, payload, f"invalid top-level type, expected {expected}")


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
    topics_payload = [
        {
            "id": "topic_244",
            "title": "Проект 244",
            "keywords": ["244", "осаз", "хгкм", "интеграция"],
            "synonyms": ["проект 244", "узел 244"],
        }
    ]
    users_payload = [
        {"id": "101", "name": "Иванов И.И."},
        {"id": "102", "name": "Петров П.П."},
        {"id": "103", "name": "Сидорова А.А."},
    ]
    keywords_payload = {"keywords": ["поручить", "подготовить", "обеспечить", "направить", "согласовать", "выполнить", "предоставить", "организовать", "рассмотреть", "доработать", "завершить", "проработать"]}

    ensure_seed_file(
        topics_path,
        topics_payload,
    )
    ensure_seed_file(
        users_path,
        users_payload,
    )
    ensure_seed_file(
        task_keywords_path,
        keywords_payload,
    )

    _load_json_or_repair(topics_path, topics_payload, list)
    _load_json_or_repair(users_path, users_payload, list)
    _load_json_or_repair(task_keywords_path, keywords_payload, dict)
