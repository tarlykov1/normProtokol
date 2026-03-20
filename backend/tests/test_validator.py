from app.models.entities import TaskCandidate
from app.services.validator.task_validator import validate_task


def test_validate_task_errors():
    task = TaskCandidate(protocol_id=1, normalized_text="", assignee_b24_id=None, deadline_iso="40.40.2024")
    errors, warnings = validate_task(task)
    assert "Task text is empty" in errors
    assert "Assignee is required" in errors
    assert "Deadline has invalid format" in errors
    assert warnings
