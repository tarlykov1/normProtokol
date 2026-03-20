from datetime import datetime
from pathlib import Path
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.db.session import get_db
from app.models.entities import AuditLog, Protocol, TaskCandidate, Topic
from app.schemas.common import (
    AssignPayload,
    BulkAssignPayload,
    BulkDeadlinePayload,
    BulkTopicPayload,
    MergePayload,
    MoveTopicPayload,
    ProtocolRead,
    PublishReport,
    ReorderPayload,
    SplitPayload,
    TaskCreate,
    TaskPatch,
    TaskRead,
    TopicCreate,
    TopicRead,
)
from app.services.bitrix.bitrix_service import BitrixService
from app.services.exporter.docx_exporter import export_protocol_docx
from app.services.normalizer.text_normalizer import normalize_text
from app.services.parser.docx_parser import extract_docx_text
from app.services.parser.task_extractor import extract_task_candidates
from app.services.validator.task_validator import validate_duplicates, validate_task

router = APIRouter(prefix="/api")
bitrix = BitrixService(mock_mode=settings.bitrix_mock_mode)


def _get_protocol(db: Session, protocol_id: int) -> Protocol:
    protocol = (
        db.query(Protocol)
        .options(joinedload(Protocol.tasks), joinedload(Protocol.topics))
        .filter(Protocol.id == protocol_id)
        .first()
    )
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return protocol


@router.post("/protocols/upload", response_model=ProtocolRead)
def upload_protocol(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    destination = settings.uploads_dir / f"{timestamp}_{file.filename}"
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extracted_text, chunks = extract_docx_text(destination)
    normalized = normalize_text(extracted_text)

    protocol = Protocol(
        original_filename=file.filename,
        original_file_path=str(destination),
        extracted_text=normalized,
        status="parsed",
    )
    db.add(protocol)
    db.flush()

    parsed_tasks = extract_task_candidates(chunks)
    topic_cache: dict[str, Topic] = {}

    for task_data in parsed_tasks:
        topic_id = None
        topic_title = task_data.get("topic_auto_candidate")
        conf = task_data.pop("topic_confidence", 0.0)
        if topic_title and conf >= 0.34:
            if topic_title not in topic_cache:
                topic_obj = Topic(
                    protocol_id=protocol.id,
                    title=topic_title,
                    source_type="auto",
                    confidence=conf,
                    is_confirmed=conf > 0.66,
                    order_index=len(topic_cache),
                )
                db.add(topic_obj)
                db.flush()
                topic_cache[topic_title] = topic_obj
            topic_id = topic_cache[topic_title].id

        task = TaskCandidate(protocol_id=protocol.id, topic_id=topic_id, **task_data)
        if task.deadline_raw:
            task.deadline_iso = task.deadline_raw
        db.add(task)

    db.commit()
    db.refresh(protocol)
    return _get_protocol(db, protocol.id)


@router.get("/protocols/{protocol_id}", response_model=ProtocolRead)
def get_protocol(protocol_id: int, db: Session = Depends(get_db)):
    return _get_protocol(db, protocol_id)


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def patch_task(task_id: int, payload: TaskPatch, db: Session = Depends(get_db)):
    task = db.query(TaskCandidate).filter(TaskCandidate.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old = {k: getattr(task, k) for k in payload.model_dump(exclude_none=True)}
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(task, field, value)

    db.add(AuditLog(protocol_id=task.protocol_id, entity_type="task", entity_id=task.id, action="patch", old_value=old, new_value=payload.model_dump(exclude_none=True)))
    db.commit()
    db.refresh(task)
    return task


@router.post("/tasks", response_model=TaskRead)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = TaskCandidate(protocol_id=payload.protocol_id, topic_id=payload.topic_id, normalized_text=payload.normalized_text, source_fragment=payload.normalized_text)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TaskCandidate).filter(TaskCandidate.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"status": "deleted"}


@router.post("/tasks/{task_id}/split")
def split_task(task_id: int, payload: SplitPayload, db: Session = Depends(get_db)):
    task = db.query(TaskCandidate).filter(TaskCandidate.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    parts = [p.strip() for p in task.normalized_text.split(payload.separator) if p.strip()]
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Not enough parts to split")
    task.normalized_text = parts[0]
    for part in parts[1:]:
        db.add(TaskCandidate(protocol_id=task.protocol_id, topic_id=task.topic_id, normalized_text=part, source_fragment=task.source_fragment, assignee_b24_id=task.assignee_b24_id, assignee_b24_name=task.assignee_b24_name, deadline_iso=task.deadline_iso, status="draft"))
    db.commit()
    return {"status": "split", "created": len(parts) - 1}


@router.post("/tasks/merge", response_model=TaskRead)
def merge_tasks(payload: MergePayload, db: Session = Depends(get_db)):
    if len(payload.task_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 tasks")
    tasks = db.query(TaskCandidate).filter(TaskCandidate.id.in_(payload.task_ids)).order_by(TaskCandidate.id).all()
    merged = tasks[0]
    merged.normalized_text = " ; ".join(t.normalized_text for t in tasks)
    for t in tasks[1:]:
        db.delete(t)
    db.commit()
    db.refresh(merged)
    return merged


@router.post("/tasks/reorder")
def reorder_tasks(payload: ReorderPayload, db: Session = Depends(get_db)):
    for item in payload.task_orders:
        task = db.query(TaskCandidate).filter(TaskCandidate.id == item["id"]).first()
        if task:
            task.order_index = item["order_index"]
    db.commit()
    return {"status": "ok"}


@router.post("/tasks/move-to-topic")
def move_tasks(payload: MoveTopicPayload, db: Session = Depends(get_db)):
    tasks = db.query(TaskCandidate).filter(TaskCandidate.id.in_(payload.task_ids)).all()
    for t in tasks:
        t.topic_id = payload.topic_id
    db.commit()
    return {"status": "ok", "count": len(tasks)}


@router.get("/assignees/search")
def assignee_search(q: str = Query(default="")):
    return [a.__dict__ for a in bitrix.search_users(q)]


@router.post("/tasks/{task_id}/assign")
def assign_task(task_id: int, payload: AssignPayload, db: Session = Depends(get_db)):
    task = db.query(TaskCandidate).filter(TaskCandidate.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.assignee_b24_id = payload.assignee_b24_id
    task.assignee_b24_name = payload.assignee_b24_name
    db.commit()
    return {"status": "ok"}


@router.post("/tasks/bulk-assign")
def bulk_assign(payload: BulkAssignPayload, db: Session = Depends(get_db)):
    tasks = db.query(TaskCandidate).filter(TaskCandidate.id.in_(payload.task_ids)).all()
    for t in tasks:
        t.assignee_b24_id = payload.assignee_b24_id
        t.assignee_b24_name = payload.assignee_b24_name
    db.commit()
    return {"status": "ok", "count": len(tasks)}


@router.post("/tasks/bulk-topic")
def bulk_topic(payload: BulkTopicPayload, db: Session = Depends(get_db)):
    tasks = db.query(TaskCandidate).filter(TaskCandidate.id.in_(payload.task_ids)).all()
    for t in tasks:
        t.topic_id = payload.topic_id
    db.commit()
    return {"status": "ok", "count": len(tasks)}


@router.post("/tasks/bulk-deadline")
def bulk_deadline(payload: BulkDeadlinePayload, db: Session = Depends(get_db)):
    tasks = db.query(TaskCandidate).filter(TaskCandidate.id.in_(payload.task_ids)).all()
    for t in tasks:
        t.deadline_iso = payload.deadline_iso
    db.commit()
    return {"status": "ok", "count": len(tasks)}


@router.post("/topics", response_model=TopicRead)
def create_topic(payload: TopicCreate, db: Session = Depends(get_db)):
    topic = Topic(protocol_id=payload.protocol_id, title=payload.title, source_type="manual", is_confirmed=True)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@router.post("/protocols/{protocol_id}/save-draft")
def save_draft(protocol_id: int, db: Session = Depends(get_db)):
    protocol = _get_protocol(db, protocol_id)
    protocol.draft_saved_at = datetime.utcnow()
    protocol.status = "draft_saved"
    db.commit()
    return {"status": "saved", "draft_saved_at": protocol.draft_saved_at}


@router.get("/protocols/{protocol_id}/draft", response_model=ProtocolRead)
def get_draft(protocol_id: int, db: Session = Depends(get_db)):
    return _get_protocol(db, protocol_id)


@router.post("/protocols/{protocol_id}/generate-docx")
def generate_docx(protocol_id: int, db: Session = Depends(get_db)):
    protocol = _get_protocol(db, protocol_id)
    output = settings.exports_dir / f"protocol_{protocol_id}_draft.docx"
    export_protocol_docx(protocol, output)
    protocol.normalized_docx_path = str(output)
    protocol.status = "docx_generated"
    db.commit()
    return {"status": "generated", "path": str(output)}


@router.get("/protocols/{protocol_id}/download-docx")
def download_docx(protocol_id: int, db: Session = Depends(get_db)):
    protocol = _get_protocol(db, protocol_id)
    path = protocol.normalized_docx_path or protocol.published_docx_path
    if not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(path=path, filename=Path(path).name, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@router.post("/protocols/{protocol_id}/validate")
def validate_protocol(protocol_id: int, db: Session = Depends(get_db)):
    protocol = _get_protocol(db, protocol_id)
    require_topic = False
    errors_count = 0
    warnings_count = 0

    dup_map = validate_duplicates(protocol.tasks)
    for task in protocol.tasks:
        errors, warnings = validate_task(task, require_topic=require_topic)
        if task.id in dup_map:
            warnings.append(dup_map[task.id])
        task.errors = errors
        task.warnings = warnings
        errors_count += len(errors)
        warnings_count += len(warnings)

    db.commit()
    return {"errors": errors_count, "warnings": warnings_count}


@router.post("/protocols/{protocol_id}/publish", response_model=PublishReport)
def publish_protocol(protocol_id: int, db: Session = Depends(get_db)):
    protocol = _get_protocol(db, protocol_id)

    smart_process_id = bitrix.create_smart_process(protocol.id)
    published_task_ids: list[int] = []
    failed_task_ids: list[int] = []
    errors: list[str] = []

    for task in protocol.tasks:
        task_errors, task_warnings = validate_task(task)
        task.errors = task_errors
        task.warnings = task_warnings

        if task_errors:
            failed_task_ids.append(task.id)
            errors.extend([f"Task {task.id}: {e}" for e in task_errors])
            continue

        task.bitrix_task_id = bitrix.create_task(protocol.id, task.id, task.normalized_text[:50], task.assignee_b24_id or "", task.deadline_iso)
        task.status = "published"
        published_task_ids.append(task.id)

    protocol.bitrix_smart_process_id = smart_process_id
    protocol.bitrix_publish_status = "partial" if failed_task_ids else "success"
    protocol.status = "published"

    if protocol.normalized_docx_path:
        published_path = settings.exports_dir / f"protocol_{protocol_id}_published.docx"
        shutil.copy(protocol.normalized_docx_path, published_path)
        protocol.published_docx_path = str(published_path)

    db.commit()

    return PublishReport(
        smart_process_id=smart_process_id,
        published_task_ids=published_task_ids,
        failed_task_ids=failed_task_ids,
        errors=errors,
    )
