from datetime import datetime

from app.models.entities import TaskCandidate


def _is_valid_date(value: str | None) -> bool:
    if not value:
        return False
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y"):
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def validate_task(task: TaskCandidate, require_topic: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not task.normalized_text.strip():
        errors.append("Task text is empty")
    if not task.assignee_b24_id:
        errors.append("Assignee is required")
    if task.deadline_iso and not _is_valid_date(task.deadline_iso):
        errors.append("Deadline has invalid format")
    if not task.deadline_iso:
        warnings.append("Deadline is missing")
    if not task.topic_id:
        if require_topic:
            errors.append("Topic is required")
        else:
            warnings.append("Topic is missing")

    return errors, warnings


def validate_duplicates(tasks: list[TaskCandidate]) -> dict[int, str]:
    seen: dict[str, int] = {}
    duplicates: dict[int, str] = {}
    for task in tasks:
        key = task.normalized_text.strip().lower()
        if not key:
            continue
        if key in seen:
            duplicates[task.id] = "Possible duplicate task"
        else:
            seen[key] = task.id
    return duplicates
