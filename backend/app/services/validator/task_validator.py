from datetime import date
from typing import Any


def _is_valid_iso(value: str | None) -> bool:
    if not value:
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def validate_task(task: Any, require_topic_error: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not task.normalized_text.strip():
        errors.append("normalized_text is empty")
    if task.topic_id is None:
        (errors if require_topic_error else warnings).append("topic_id is null")
    if not task.assignee_b24_id:
        errors.append("assignee_b24_id is null")
    if task.deadline_iso and not _is_valid_iso(task.deadline_iso):
        errors.append("deadline_iso invalid")
    if not task.deadline_iso:
        warnings.append("deadline missing")

    return errors, warnings


def validate_duplicates(tasks: list[Any]) -> dict[int, str]:
    seen: dict[str, int] = {}
    duplicates: dict[int, str] = {}
    for task in tasks:
        key = task.normalized_text.strip().lower()
        if not key:
            continue
        if key in seen:
            duplicates[task.id] = "duplicate normalized_text"
        else:
            seen[key] = task.id
    return duplicates
