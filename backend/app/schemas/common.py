from datetime import datetime
from pydantic import BaseModel


class TopicRead(BaseModel):
    id: int
    protocol_id: int
    title: str
    order_index: int
    source_type: str
    confidence: float
    is_confirmed: bool

    class Config:
        from_attributes = True


class TaskRead(BaseModel):
    id: int
    protocol_id: int
    topic_id: int | None
    source_fragment: str
    normalized_text: str
    topic_auto_candidate: str | None
    topic_candidate_list: list
    assignee_raw: str | None
    assignee_b24_id: str | None
    assignee_b24_name: str | None
    deadline_raw: str | None
    deadline_iso: str | None
    status: str
    warnings: list
    errors: list
    order_index: int
    bitrix_task_id: str | None

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


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


class AssignPayload(BaseModel):
    assignee_b24_id: str
    assignee_b24_name: str


class BulkAssignPayload(BaseModel):
    task_ids: list[int]
    assignee_b24_id: str
    assignee_b24_name: str


class BulkTopicPayload(BaseModel):
    task_ids: list[int]
    topic_id: int


class BulkDeadlinePayload(BaseModel):
    task_ids: list[int]
    deadline_iso: str


class MoveTopicPayload(BaseModel):
    task_ids: list[int]
    topic_id: int | None


class MergePayload(BaseModel):
    task_ids: list[int]


class ReorderPayload(BaseModel):
    task_orders: list[dict]


class SplitPayload(BaseModel):
    separator: str = ";"


class TopicCreate(BaseModel):
    protocol_id: int
    title: str


class PublishReport(BaseModel):
    smart_process_id: str
    published_task_ids: list[int]
    failed_task_ids: list[int]
    errors: list[str]
