from enum import Enum


class ProtocolStatus(str, Enum):
    uploaded = "uploaded"
    parsed = "parsed"
    needs_review = "needs_review"
    ready_to_publish = "ready_to_publish"
    published = "published"
    partially_published = "partially_published"
    publish_error = "publish_error"


class TaskStatus(str, Enum):
    draft = "draft"
    needs_confirmation = "needs_confirmation"
    valid = "valid"
    error = "error"
    excluded = "excluded"
    published = "published"
