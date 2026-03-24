from types import SimpleNamespace

from app.services.validator.task_validator import validate_task


def test_validator_errors():
    task = SimpleNamespace(normalized_text="", topic_id=None, assignee_b24_id=None, deadline_iso="2026-13-01")
    errors, warnings = validate_task(task)
    assert errors
    assert warnings


def test_validator_allows_multiple_assignees_without_warning():
    task = SimpleNamespace(
        normalized_text="Подготовить отчет",
        topic_id=1,
        assignee_b24_id="101",
        assignee_b24_name="Иванов И.И.",
        assignees_normalized=["Иванов И.И.", "Петров П.П."],
        deadline_iso="2026-04-01",
        errors=[],
        warnings=[],
        markers=[],
        item_kind="task",
    )
    errors, warnings = validate_task(task)
    assert not errors
    assert not any("несколько исполнителей" in warning.lower() for warning in warnings)
