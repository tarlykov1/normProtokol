from app.models.enums import TaskStatus


def postprocess_extracted_tasks(tasks: list[dict]) -> list[dict]:
    """Дополнительная нормализация после извлечения."""

    normalized: list[dict] = []
    for task in tasks:
        markers = task.get("markers") or []
        warnings = task.get("warnings") or []
        errors = task.get("errors") or []

        if task.get("section_name") == "informational":
            task["status"] = TaskStatus.excluded.value
            warnings.append("Раздел содержит обсуждение/контекст, а не поручение. Проверьте, нужно ли создавать задачу.")

        if "out_of_agenda" in markers:
            warnings.append("Задача из блока «Вопрос вне повестки». Проверьте корректность публикации.")

        text = (task.get("normalized_text") or "").strip()
        if text and sum(1 for ch in text if ch in ";\n") > 3:
            warnings.append("Найдено несколько подпунктов. Подтвердите: это одна комплексная задача или несколько отдельных.")
            if task.get("status") == TaskStatus.extracted.value:
                task["status"] = TaskStatus.needs_review.value

        task["warnings"] = list(dict.fromkeys(warnings))
        task["errors"] = list(dict.fromkeys(errors))
        normalized.append(task)

    return normalized
