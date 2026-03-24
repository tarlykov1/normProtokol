from app.models.enums import ProtocolStatus, TaskStatus


def suggest_protocol_status(tasks: list) -> str:
    if not tasks:
        return ProtocolStatus.needs_review.value

    valid_count = sum(1 for task in tasks if task.status == TaskStatus.valid.value)
    blocking_count = sum(1 for task in tasks if task.status in {TaskStatus.error.value, TaskStatus.needs_completion.value})

    if valid_count and blocking_count == 0:
        return ProtocolStatus.ready_to_publish.value
    return ProtocolStatus.needs_review.value
