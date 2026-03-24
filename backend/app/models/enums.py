from enum import Enum


class ProtocolType(str, Enum):
    auto = "auto"
    memo_meeting = "memo_meeting"
    memo_preparation = "memo_preparation"
    memo_mixed_sections = "memo_mixed_sections"
    memo_hierarchical = "memo_hierarchical"
    simple = "simple"
    # Backward-compatible aliases for previous MVP options.
    standard = "standard"
    topics = "topics"
    blocks = "blocks"
    projects = "projects"


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
    extracted = "extracted"
    needs_review = "needs_review"
    needs_completion = "needs_completion"
    valid = "valid"
    excluded = "excluded"
    published = "published"
    error = "error"
    needs_confirmation = "needs_confirmation"
