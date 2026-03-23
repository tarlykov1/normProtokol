from datetime import date
from typing import Any

from app.services.bitrix.bitrix_service import BaseBitrixService, BitrixUnavailableError


ASSIGNEE_NOT_FOUND_ERROR = "Исполнитель не найден в Bitrix24. Выберите другого исполнителя или отправьте заявку."
ASSIGNEE_UNAVAILABLE_ERROR = "Сейчас нет подключения к Bitrix24. Повторите позже или отправьте заявку."
ASSIGNEE_AMBIGUOUS_ERROR = "Найдено несколько исполнителей в Bitrix24. Уточните ФИО или выберите исполнителя вручную."
ASSIGNEE_MISSING_ERROR = "Не указан исполнитель. Выберите исполнителя или отправьте заявку."


def _is_valid_iso(value: str | None) -> bool:
    if not value:
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _normalize_name(value: str) -> str:
    return " ".join(value.lower().replace("ё", "е").replace(".", " ").split())


def _resolve_assignee(task: Any, bitrix_service: BaseBitrixService | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not bitrix_service:
        if not task.assignee_b24_id:
            errors.append(ASSIGNEE_MISSING_ERROR)
        return errors, warnings

    try:
        if task.assignee_b24_id:
            if bitrix_service.validate_user(task.assignee_b24_id):
                return errors, warnings
            errors.append(ASSIGNEE_NOT_FOUND_ERROR)
            return errors, warnings

        if task.assignee_b24_name:
            candidates = bitrix_service.search_users(task.assignee_b24_name)
            normalized_query = _normalize_name(task.assignee_b24_name)
            matched = [
                user
                for user in candidates
                if normalized_query in _normalize_name(user.name)
                or any(normalized_query in _normalize_name(alias) for alias in getattr(user, "aliases", []))
            ]
            if len(matched) == 1:
                task.assignee_b24_id = matched[0].id
                task.assignee_b24_name = matched[0].name
                warnings.append(f"Исполнитель найден автоматически: {matched[0].name}")
                return errors, warnings
            if len(matched) > 1:
                errors.append(ASSIGNEE_AMBIGUOUS_ERROR)
                return errors, warnings
            errors.append(ASSIGNEE_NOT_FOUND_ERROR)
            return errors, warnings

        errors.append(ASSIGNEE_MISSING_ERROR)
    except BitrixUnavailableError:
        errors.append(ASSIGNEE_UNAVAILABLE_ERROR)
    except Exception:
        errors.append(ASSIGNEE_UNAVAILABLE_ERROR)

    return errors, warnings


def validate_task(
    task: Any,
    require_topic_error: bool = False,
    bitrix_service: BaseBitrixService | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not task.normalized_text.strip():
        errors.append("Текст задачи пустой")
    if task.topic_id is None:
        (errors if require_topic_error else warnings).append("Тема не определена")

    assignee_errors, assignee_warnings = _resolve_assignee(task, bitrix_service)
    errors.extend(assignee_errors)
    warnings.extend(assignee_warnings)

    if task.deadline_iso and not _is_valid_iso(task.deadline_iso):
        errors.append("Некорректный формат срока")
    if not task.deadline_iso:
        warnings.append("Срок не указан")

    return errors, warnings


def validate_duplicates(tasks: list[Any]) -> dict[int, str]:
    seen: dict[str, int] = {}
    duplicates: dict[int, str] = {}
    for task in tasks:
        key = task.normalized_text.strip().lower()
        if not key:
            continue
        if key in seen:
            duplicates[task.id] = "Обнаружен дубль задачи"
        else:
            seen[key] = task.id
    return duplicates
