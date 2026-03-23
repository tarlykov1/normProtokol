from datetime import date
from typing import Any

from app.models.enums import TaskStatus
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

    assignees_normalized = getattr(task, "assignees_normalized", None) or []
    assignee_b24_name = getattr(task, "assignee_b24_name", None)
    candidate_names = list(dict.fromkeys([*assignees_normalized, *([assignee_b24_name] if assignee_b24_name else [])]))

    if not bitrix_service:
        if not getattr(task, "assignee_b24_id", None) and not candidate_names:
            errors.append(ASSIGNEE_MISSING_ERROR)
        return errors, warnings

    try:
        if getattr(task, "assignee_b24_id", None):
            if bitrix_service.validate_user(task.assignee_b24_id):
                return errors, warnings
            errors.append(ASSIGNEE_NOT_FOUND_ERROR)
            return errors, warnings

        if not candidate_names:
            errors.append(ASSIGNEE_MISSING_ERROR)
            return errors, warnings

        merged_matches = []
        for name in candidate_names:
            candidates = bitrix_service.search_users(name)
            normalized_query = _normalize_name(name)
            matched = [
                user
                for user in candidates
                if normalized_query in _normalize_name(user.name)
                or any(normalized_query in _normalize_name(alias) for alias in getattr(user, "aliases", []))
            ]
            merged_matches.extend(matched)

        unique_matches = {user.id: user for user in merged_matches}
        if len(unique_matches) == 1:
            user = next(iter(unique_matches.values()))
            task.assignee_b24_id = user.id
            task.assignee_b24_name = user.name
            warnings.append(f"Исполнитель найден автоматически: {user.name}")
            return errors, warnings

        if len(unique_matches) > 1:
            errors.append(ASSIGNEE_AMBIGUOUS_ERROR)
            return errors, warnings

        errors.append(ASSIGNEE_NOT_FOUND_ERROR)
    except BitrixUnavailableError:
        errors.append(ASSIGNEE_UNAVAILABLE_ERROR)
    except Exception:
        errors.append(ASSIGNEE_UNAVAILABLE_ERROR)

    return errors, warnings


def _derive_status(task: Any, errors: list[str], warnings: list[str]) -> str:
    if "not_reviewed" in (getattr(task, "markers", None) or []):
        return TaskStatus.excluded.value
    if errors:
        return TaskStatus.needs_completion.value
    if warnings:
        return TaskStatus.needs_review.value
    return TaskStatus.valid.value


def validate_task(
    task: Any,
    require_topic_error: bool = False,
    bitrix_service: BaseBitrixService | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = list(getattr(task, "errors", None) or [])
    warnings: list[str] = list(getattr(task, "warnings", None) or [])

    text = (task.normalized_text or "").strip()
    if not text:
        errors.append("Задача содержит только тему или контекст без действия. Доработайте формулировку поручения.")

    if task.topic_id is None:
        (errors if require_topic_error else warnings).append("Тема не определена")

    if "not_reviewed" in (getattr(task, "markers", None) or []):
        warnings.append("Пункт отмечен как «Не рассматривали». Подтвердите исключение из публикации.")
        dedup_errors = list(dict.fromkeys(errors))
        dedup_warnings = list(dict.fromkeys(warnings))
        setattr(task, "status", _derive_status(task, dedup_errors, dedup_warnings))
        return dedup_errors, dedup_warnings

    assignee_errors, assignee_warnings = _resolve_assignee(task, bitrix_service)
    errors.extend(assignee_errors)
    warnings.extend(assignee_warnings)

    if getattr(task, "deadline_iso", None) and not _is_valid_iso(task.deadline_iso):
        errors.append("Некорректный формат срока")
    if getattr(task, "deadline_kind", None) == "empty_deadline":
        errors.append("У задачи не указан срок. Добавьте дату в формате ДД.ММ.ГГГГ.")
    elif getattr(task, "deadline_kind", None) == "text_deadline":
        warnings.append("Срок «к исполнению» не может быть опубликован как календарная дата. Уточните дату или подтвердите, что срок нефиксированный.")

    if len(getattr(task, "assignees_normalized", None) or []) > 1:
        warnings.append("Задача содержит несколько исполнителей. Уточните основного ответственного для публикации.")

    dedup_errors = list(dict.fromkeys(errors))
    dedup_warnings = list(dict.fromkeys(warnings))

    setattr(task, "status", _derive_status(task, dedup_errors, dedup_warnings))
    return dedup_errors, dedup_warnings


def validate_duplicates(tasks: list[Any]) -> dict[int, str]:
    seen: dict[str, int] = {}
    duplicates: dict[int, str] = {}
    for task in tasks:
        key = (task.normalized_text or "").strip().lower()
        if not key:
            continue
        if key in seen:
            duplicates[task.id] = "Обнаружен дубль задачи"
        else:
            seen[key] = task.id
    return duplicates
