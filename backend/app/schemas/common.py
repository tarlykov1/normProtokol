from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class TopicRead(BaseModel):
    id: int
    protocol_id: int
    title: str
    order_index: int
    source_type: str
    confidence: float | None
    is_confirmed: bool

    model_config = {"from_attributes": True}


class TaskRead(BaseModel):
    id: int
    protocol_id: int
    topic_id: int | None
    source_fragment: str
    normalized_text: str
    topic_auto_candidate: str | None
    topic_candidate_list: list[str] | None
    assignee_raw: str | None
    assignee_b24_id: str | None
    assignee_b24_name: str | None
    deadline_raw: str | None
    deadline_iso: str | None
    status: str
    warnings: list[str]
    errors: list[str]
    order_index: int
    bitrix_task_id: str | None

    @field_validator("topic_candidate_list", mode="before")
    @classmethod
    def _normalize_topic_candidate_list(cls, value):
        if value is None:
            return None
        if isinstance(value, list):
            normalized: list[str] = []
            for item in value:
                if isinstance(item, str):
                    normalized.append(item)
                elif isinstance(item, dict) and item.get("title"):
                    normalized.append(str(item["title"]))
            return normalized
        return None

    model_config = {"from_attributes": True}


class ProtocolRead(BaseModel):
    id: int
    original_filename: str
    extracted_text: str
    status: str
    created_at: datetime
    updated_at: datetime
    draft_saved_at: datetime | None
    normalized_docx_path: str | None
    published_docx_path: str | None
    bitrix_smart_process_id: str | None
    bitrix_publish_status: str | None
    topics: list[TopicRead]
    tasks: list[TaskRead]

    model_config = {"from_attributes": True}


class TaskPatch(BaseModel):
    topic_id: int | None = None
    normalized_text: str | None = None
    assignee_b24_id: str | None = None
    assignee_b24_name: str | None = None
    deadline_iso: str | None = None
    status: str | None = None


class TaskCreate(BaseModel):
    protocol_id: int
    normalized_text: str
    topic_id: int | None = None


class MoveTopicPayload(BaseModel):
    task_ids: list[int]
    topic_id: int | None


class MergePayload(BaseModel):
    task_ids: list[int]


class ReorderItem(BaseModel):
    id: int
    order_index: int


class ReorderPayload(BaseModel):
    task_orders: list[ReorderItem]


class SplitPayload(BaseModel):
    separator: str = ";"


class TopicCreate(BaseModel):
    protocol_id: int
    title: str


class TopicPatch(BaseModel):
    title: str | None = None
    is_confirmed: bool | None = None


class BulkAssignPayload(BaseModel):
    topic_id: int
    task_ids: list[int]




class BulkTaskUpdatePayload(BaseModel):
    task_ids: list[int]
    assignee_b24_id: str | None = None
    assignee_b24_name: str | None = None
    deadline_iso: str | None = None
    status: str | None = None


class ValidationTaskResult(BaseModel):
    task_id: int
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ValidationResponse(BaseModel):
    protocol_status_suggestion: str
    count_valid: int
    count_warnings: int
    count_errors: int
    details: list[ValidationTaskResult]


class PublishResponse(BaseModel):
    protocol_id: int
    smart_process_id: str | None
    published_tasks: list[int]
    skipped_tasks: list[int]
    errors: list[str]
