from types import SimpleNamespace

from app.services.validator.task_validator import validate_task


def test_validator_errors():
    task = SimpleNamespace(normalized_text="", topic_id=None, assignee_b24_id=None, deadline_iso="2026-13-01")
    errors, warnings = validate_task(task)
    assert errors
    assert warnings
