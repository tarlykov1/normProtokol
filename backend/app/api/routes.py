from datetime import datetime
from pathlib import Path
import re
import shutil
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.db.session import get_db
from app.models.entities import AuditLog, Protocol, TaskCandidate, Topic
from app.models.enums import ProtocolStatus, ProtocolType, TaskStatus
from app.schemas.common import (
    BulkAssignPayload,
    BulkTaskUpdatePayload,
    MergePayload,
    MoveTopicPayload,
    ProtocolRead,
    PublishResponse,
    SkippedTaskRead,
    ReorderPayload,
    SplitPayload,
    TaskCreate,
    TaskPatch,
    TaskRead,
    TopicCreate,
    TopicPatch,
    TopicRead,
    ValidationResponse,
    ValidationTaskResult,
)
from app.services.bitrix.bitrix_service import BitrixUnavailableError, MockBitrixService, RealBitrixService
from app.services.exporter.docx_exporter import export_protocol_docx
from app.services.normalizer.document_classifier import classify_document
from app.services.normalizer.extractors import TaskExtractorRegistry
from app.services.normalizer.postprocess import postprocess_extracted_tasks
from app.services.normalizer.task_extractor import load_task_keywords
from app.services.parser.docx_parser import extract_docx_text
from app.services.topics.matcher import load_topics
from app.services.validator.document_validator import suggest_protocol_status
from app.services.validator.task_validator import validate_duplicates, validate_task
from app.api.migration_routes import router as migration_router

router = APIRouter(prefix="/api", tags=["protocols"])
extractor_registry = TaskExtractorRegistry()


def _bitrix_service():
    if settings.bitrix_mode == "real":
        return RealBitrixService(settings.bitrix_base_url, settings.bitrix_webhook)
    return MockBitrixService(settings.mock_users_path)


def _safe_filename(name: str) -> str:
    base = Path(name).name
    safe = re.sub(r"[^a-zA-Zа-яА-Я0-9_.-]", "_", base)
    return f"{uuid4().hex}_{safe}"


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


def _build_skipped_task_detail(task: TaskCandidate, reason: str) -> SkippedTaskRead:
    return SkippedTaskRead(
        task_id=task.id,
        normalized_text=task.normalized_text,
        assignee_b24_name=task.assignee_b24_name,
        assignee_raw=task.assignee_raw,
        reason=reason,
        errors=task.errors or [],
        warnings=task.warnings or [],
    )


def _skip_reason_for_task(task: TaskCandidate, is_publish_failure: bool = False) -> str:
    if getattr(task, "item_kind", "task") != "task":
        return "Элемент повестки не публикуется как поручение"
    if task.status == TaskStatus.excluded.value:
        return "Задача исключена из публикации"
    if is_publish_failure:
        return "Не удалось создать задачу в Bitrix24"
    if task.errors:
        assignee_errors = [item for item in task.errors if "исполн" in item.lower() or "bitrix24" in item.lower()]
        if assignee_errors:
            return "Не найден исполнитель в Bitrix24"
        return "Задача не прошла валидацию"
    return "Задача не прошла валидацию"


def _remove_file_if_exists(path_value: str | None) -> bool:
    if not path_value:
        return False
    path = Path(path_value)
    if not path.exists():
        return False
    path.unlink()
    return True


@router.post("/demo/bootstrap", response_model=ProtocolRead, tags=["demo"])
def bootstrap_demo_protocol(db: Session = Depends(get_db)):
    protocol = Protocol(
        original_filename="demo_protocol.docx",
        original_file_path=str(settings.uploads_dir / "demo_protocol.docx"),
        extracted_text="\n".join(
            [
                "1. Поручить Иванову И.И. подготовить коммерческое предложение до 25.03.2026",
                "2. Петровой А.А. согласовать бюджет запуска до 28.03.2026",
                "3. Обновить чеклист onboarding сотрудников",
            ]
        ),
        protocol_type=ProtocolType.standard.value,
        status=ProtocolStatus.parsed.value,
    )
    db.add(protocol)
    db.flush()

    topic_sales = Topic(protocol_id=protocol.id, title="Продажи", order_index=1, source_type="auto", confidence=0.92, is_confirmed=True)
    topic_ops = Topic(protocol_id=protocol.id, title="Операционные вопросы", order_index=2, source_type="auto", confidence=0.71, is_confirmed=False)
    db.add_all([topic_sales, topic_ops])
    db.flush()

    db.add_all(
        [
            TaskCandidate(
                protocol_id=protocol.id,
                topic_id=topic_sales.id,
                source_fragment="Поручить Иванову И.И. подготовить коммерческое предложение до 25.03.2026",
                normalized_text="Подготовить коммерческое предложение для клиента Альфа",
                topic_auto_candidate="Продажи",
                topic_candidate_list=["Продажи", "Маркетинг"],
                assignee_raw="Иванов И.И.",
                assignee_b24_id="101",
                assignee_b24_name="Иванов Илья Игоревич",
                deadline_raw="25.03.2026",
                deadline_iso="2026-03-25",
                status=TaskStatus.draft.value,
                warnings=[],
                errors=[],
                order_index=1,
            ),
            TaskCandidate(
                protocol_id=protocol.id,
                topic_id=topic_ops.id,
                source_fragment="Петровой А.А. согласовать бюджет запуска до 28.03.2026",
                normalized_text="Согласовать бюджет запуска пилотного проекта",
                topic_auto_candidate="Операционные вопросы",
                topic_candidate_list=["Операционные вопросы", "Финансы"],
                assignee_raw="Петрова А.А.",
                assignee_b24_id="102",
                assignee_b24_name="Петрова Анна Александровна",
                deadline_raw="28.03.2026",
                deadline_iso="2026-03-28",
                status=TaskStatus.draft.value,
                warnings=[],
                errors=[],
                order_index=2,
            ),
            TaskCandidate(
                protocol_id=protocol.id,
                topic_id=None,
                source_fragment="Обновить чеклист onboarding сотрудников",
                normalized_text="Обновить чеклист onboarding для новых сотрудников",
                topic_auto_candidate=None,
                topic_candidate_list=["HR", "Операционные вопросы"],
                assignee_raw=None,
                assignee_b24_id=None,
                assignee_b24_name=None,
                deadline_raw=None,
                deadline_iso=None,
                status=TaskStatus.draft.value,
                warnings=["Не определен исполнитель", "Не указан срок"],
                errors=[],
                order_index=3,
            ),
        ]
    )

    db.add(
        AuditLog(
            protocol_id=protocol.id,
            entity_type="protocol",
            entity_id=protocol.id,
            action="demo_bootstrap",
            new_value={"source": "demo"},
        )
    )
    db.commit()
    return _get_protocol(db, protocol.id)

@router.post("/protocols/upload", response_model=ProtocolRead, tags=["protocols"])
def upload_protocol(
    file: UploadFile = File(...),
    protocol_type: str = Form(default=ProtocolType.auto.value),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")

    requested_protocol_type = (protocol_type or ProtocolType.auto.value).strip().lower()

    destination = settings.uploads_dir / _safe_filename(file.filename)
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extracted_text, chunks = extract_docx_text(destination)
    protocol = Protocol(
        original_filename=file.filename,
        original_file_path=str(destination),
        extracted_text=extracted_text,
        protocol_type=requested_protocol_type,
        status=ProtocolStatus.parsed.value,
    )
    db.add(protocol)
    db.flush()

    topic_dict = load_topics(settings.topic_dictionary_path)
    keywords = load_task_keywords(settings.task_keywords_path)
    effective_protocol_type = requested_protocol_type
    if requested_protocol_type == ProtocolType.auto.value:
        effective_protocol_type = classify_document(chunks)
        protocol.protocol_type = effective_protocol_type

    extractor = extractor_registry.get(effective_protocol_type)
    extracted_tasks = extractor.extract(chunks, topic_dict, keywords, settings.topic_match_threshold)
    extracted_tasks = postprocess_extracted_tasks(extracted_tasks)

    topic_cache: dict[str, Topic] = {}
    for task_data in extracted_tasks:
        topic_id = None
        topic_title = task_data.get("topic_auto_candidate")
        confidence = task_data.pop("topic_confidence", 0.0)
        if topic_title:
            if topic_title not in topic_cache:
                topic = Topic(
                    protocol_id=protocol.id,
                    title=topic_title,
                    source_type="auto",
                    confidence=confidence,
                    is_confirmed=confidence > 0.66,
                    order_index=len(topic_cache),
                )
                db.add(topic)
                db.flush()
                topic_cache[topic_title] = topic
            topic_id = topic_cache[topic_title].id

        db.add(TaskCandidate(protocol_id=protocol.id, topic_id=topic_id, **task_data))

    db.commit()
    return _get_protocol(db, protocol.id)


@router.get("/protocols", response_model=list[ProtocolRead], tags=["protocols"])
def list_protocols(db: Session = Depends(get_db)):
    return db.query(Protocol).options(joinedload(Protocol.tasks), joinedload(Protocol.topics)).all()


@router.get("/protocols/{protocol_id}", response_model=ProtocolRead, tags=["protocols"])
def get_protocol(protocol_id: int, db: Session = Depends(get_db)):
    return _get_protocol(db, protocol_id)


@router.delete("/protocols/{protocol_id}", tags=["protocols"])
def delete_protocol(protocol_id: int, db: Session = Depends(get_db)):
    protocol = _get_protocol(db, protocol_id)

    removed_files = {
        "original_file": _remove_file_if_exists(protocol.original_file_path),
        "generated_docx": _remove_file_if_exists(protocol.normalized_docx_path),
        "published_docx": _remove_file_if_exists(protocol.published_docx_path),
    }

    deleted_audit_logs = db.query(AuditLog).filter(AuditLog.protocol_id == protocol.id).delete(synchronize_session=False)
    db.delete(protocol)
    db.commit()

    return {
        "status": "deleted",
        "protocol_id": protocol_id,
        "deleted_audit_logs": deleted_audit_logs,
        "removed_files": removed_files,
    }


@router.get("/protocols/{protocol_id}/draft", response_model=ProtocolRead, tags=["protocols"])
def get_draft(protocol_id: int, db: Session = Depends(get_db)):
    return _get_protocol(db, protocol_id)


@router.post("/protocols/{protocol_id}/save-draft", tags=["protocols"])
def save_draft(protocol_id: int, db: Session = Depends(get_db)):
    protocol = _get_protocol(db, protocol_id)
    protocol.draft_saved_at = datetime.utcnow()
    db.add(AuditLog(protocol_id=protocol.id, entity_type="protocol", entity_id=protocol.id, action="save_draft", new_value={"draft_saved_at": protocol.draft_saved_at.isoformat()}))
    db.commit()
    return {"status": "saved"}


@router.post("/protocols/{protocol_id}/validate", response_model=ValidationResponse, tags=["validator"])
def validate_protocol(protocol_id: int, db: Session = Depends(get_db)):
    protocol = _get_protocol(db, protocol_id)
    duplicate_map = validate_duplicates(protocol.tasks)
    service = _bitrix_service()

    details: list[ValidationTaskResult] = []
    count_errors = 0
    count_warnings = 0
    count_valid = 0

    for task in protocol.tasks:
        errors, warnings = validate_task(task, settings.topic_required_as_error, bitrix_service=service)
        if task.id in duplicate_map:
            warnings.append(duplicate_map[task.id])
        task.errors = errors
        task.warnings = warnings
        # validate_task обновляет рекомендуемый статус внутри task.status
        count_errors += len(errors)
        count_warnings += len(warnings)
        if task.status == TaskStatus.valid.value:
            count_valid += 1
        details.append(ValidationTaskResult(task_id=task.id, errors=errors, warnings=warnings))

    protocol.status = suggest_protocol_status(protocol.tasks)
    db.commit()

    return ValidationResponse(
        protocol_status_suggestion=protocol.status,
        count_valid=count_valid,
        count_warnings=count_warnings,
        count_errors=count_errors,
        details=details,
    )


@router.post("/protocols/{protocol_id}/generate-docx", tags=["exporter"])
def generate_docx(protocol_id: int, db: Session = Depends(get_db)):
    protocol = _get_protocol(db, protocol_id)
    output = settings.generated_dir / f"protocol_{protocol.id}_normalized.docx"
    export_protocol_docx(protocol, output)
    protocol.normalized_docx_path = str(output)
    db.commit()
    return {"path": str(output)}


@router.get("/protocols/{protocol_id}/download-docx", tags=["exporter"])
def download_docx(protocol_id: int, db: Session = Depends(get_db)):
    protocol = _get_protocol(db, protocol_id)
    if not protocol.normalized_docx_path:
        raise HTTPException(status_code=404, detail="Document has not been generated")
    path = Path(protocol.normalized_docx_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Generated file is missing")
    return FileResponse(path, filename=path.name, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@router.post("/protocols/{protocol_id}/publish", response_model=PublishResponse, tags=["bitrix"])
def publish_protocol(protocol_id: int, db: Session = Depends(get_db)):
    protocol = _get_protocol(db, protocol_id)
    service = _bitrix_service()

    valid_tasks = [
        t
        for t in protocol.tasks
        if t.status == TaskStatus.valid.value and not t.errors and getattr(t, "item_kind", "task") == "task"
    ]
    if not valid_tasks:
        raise HTTPException(status_code=400, detail="Нет валидных задач для публикации")

    errors: list[str] = []
    published_tasks: list[int] = []
    skipped_tasks: list[int] = []
    skipped_details: list[SkippedTaskRead] = []

    smart_process_id: str | None = None
    try:
        smart_process_id = service.create_smart_process({"protocol_id": protocol.id, "title": protocol.original_filename})
        protocol.bitrix_smart_process_id = smart_process_id
    except BitrixUnavailableError:
        error_message = "Сервис Bitrix24 временно недоступен. Попробуйте позже."
        errors.append(error_message)
        for task in protocol.tasks:
            skipped_tasks.append(task.id)
            skipped_details.append(_build_skipped_task_detail(task, "Не удалось создать задачу в Bitrix24"))
        protocol.status = ProtocolStatus.publish_error.value
        protocol.bitrix_publish_status = protocol.status
        db.commit()
        return PublishResponse(
            protocol_id=protocol.id,
            smart_process_id=smart_process_id,
            published_tasks=published_tasks,
            skipped_tasks=skipped_tasks,
            skipped_details=skipped_details,
            errors=errors,
        )

    for task in protocol.tasks:
        if task not in valid_tasks:
            skipped_tasks.append(task.id)
            skipped_details.append(_build_skipped_task_detail(task, _skip_reason_for_task(task)))
            continue
        try:
            publish_payload = {
                "task_id": task.id,
                "title": task.normalized_text,
                "responsibleId": task.assignee_b24_id,
                # Закладываем поле заранее для будущей интеграции в Bitrix24.
                "coordinator": task.coordinator,
                "assignees_display": task.assignees_display,
            }
            task_id = service.create_task(publish_payload)
            task.bitrix_task_id = task_id
            task.status = TaskStatus.published.value
            published_tasks.append(task.id)
        except BitrixUnavailableError:
            human_error = "Сервис Bitrix24 временно недоступен. Попробуйте позже."
            task.errors = [*task.errors, human_error]
            errors.append(f"Задача {task.id}: {human_error}")
            skipped_tasks.append(task.id)
            skipped_details.append(_build_skipped_task_detail(task, _skip_reason_for_task(task, is_publish_failure=True)))
        except Exception:
            human_error = "Не удалось создать задачу в Bitrix24"
            task.errors = [*task.errors, human_error]
            errors.append(f"Задача {task.id}: {human_error}")
            skipped_tasks.append(task.id)
            skipped_details.append(_build_skipped_task_detail(task, _skip_reason_for_task(task, is_publish_failure=True)))

    if protocol.normalized_docx_path:
        protocol.published_docx_path = protocol.normalized_docx_path

    if errors and published_tasks:
        protocol.status = ProtocolStatus.partially_published.value
    elif errors:
        protocol.status = ProtocolStatus.publish_error.value
    else:
        protocol.status = ProtocolStatus.published.value
    protocol.bitrix_publish_status = protocol.status

    db.commit()

    return PublishResponse(
        protocol_id=protocol.id,
        smart_process_id=smart_process_id,
        published_tasks=published_tasks,
        skipped_tasks=skipped_tasks,
        skipped_details=skipped_details,
        errors=errors,
    )


@router.patch("/tasks/{task_id}", response_model=TaskRead, tags=["tasks"])
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


@router.post("/tasks", response_model=TaskRead, tags=["tasks"])
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = TaskCandidate(protocol_id=payload.protocol_id, topic_id=payload.topic_id, normalized_text=payload.normalized_text, source_fragment=payload.normalized_text)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", tags=["tasks"])
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TaskCandidate).filter(TaskCandidate.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"status": "deleted"}


@router.post("/tasks/{task_id}/split", tags=["tasks"])
def split_task(task_id: int, payload: SplitPayload, db: Session = Depends(get_db)):
    task = db.query(TaskCandidate).filter(TaskCandidate.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    parts = [part.strip() for part in task.normalized_text.split(payload.separator) if part.strip()]
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Not enough parts")
    task.normalized_text = parts[0]
    for part in parts[1:]:
        db.add(TaskCandidate(protocol_id=task.protocol_id, topic_id=task.topic_id, normalized_text=part, source_fragment=task.source_fragment, order_index=task.order_index))
    db.commit()
    return {"status": "split", "created": len(parts) - 1}


@router.post("/tasks/merge", response_model=TaskRead, tags=["tasks"])
def merge_tasks(payload: MergePayload, db: Session = Depends(get_db)):
    tasks = db.query(TaskCandidate).filter(TaskCandidate.id.in_(payload.task_ids)).order_by(TaskCandidate.id).all()
    if len(tasks) < 2:
        raise HTTPException(status_code=400, detail="Need at least two tasks")
    anchor = tasks[0]
    anchor.normalized_text = " ; ".join(task.normalized_text for task in tasks)
    for task in tasks[1:]:
        db.delete(task)
    db.commit()
    db.refresh(anchor)
    return anchor


@router.post("/tasks/reorder", tags=["tasks"])
def reorder_tasks(payload: ReorderPayload, db: Session = Depends(get_db)):
    for item in payload.task_orders:
        task = db.query(TaskCandidate).filter(TaskCandidate.id == item.id).first()
        if task:
            task.order_index = item.order_index
    db.commit()
    return {"status": "ok"}


@router.post("/tasks/move-to-topic", tags=["tasks"])
def move_tasks(payload: MoveTopicPayload, db: Session = Depends(get_db)):
    tasks = db.query(TaskCandidate).filter(TaskCandidate.id.in_(payload.task_ids)).all()
    for task in tasks:
        task.topic_id = payload.topic_id
    db.commit()
    return {"status": "ok", "count": len(tasks)}


@router.post("/topics", response_model=TopicRead, tags=["topics"])
def create_topic(payload: TopicCreate, db: Session = Depends(get_db)):
    topic = Topic(protocol_id=payload.protocol_id, title=payload.title, source_type="manual", is_confirmed=True)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@router.patch("/topics/{topic_id}", response_model=TopicRead, tags=["topics"])
def patch_topic(topic_id: int, payload: TopicPatch, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(topic, field, value)
    db.commit()
    db.refresh(topic)
    return topic


@router.delete("/topics/{topic_id}", tags=["topics"])
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    db.delete(topic)
    db.commit()
    return {"status": "deleted"}


@router.post("/tasks/bulk-update", tags=["tasks"])
def bulk_update_tasks(payload: BulkTaskUpdatePayload, db: Session = Depends(get_db)):
    tasks = db.query(TaskCandidate).filter(TaskCandidate.id.in_(payload.task_ids)).all()
    updates = payload.model_dump(exclude_none=True)
    updates.pop("task_ids", None)

    for task in tasks:
        for field, value in updates.items():
            setattr(task, field, value)

    db.commit()
    return {"status": "ok", "count": len(tasks)}


@router.post("/topics/bulk-assign", tags=["topics"])
def bulk_assign(payload: BulkAssignPayload, db: Session = Depends(get_db)):
    tasks = db.query(TaskCandidate).filter(TaskCandidate.id.in_(payload.task_ids)).all()
    for task in tasks:
        task.topic_id = payload.topic_id
    db.commit()
    return {"status": "ok", "count": len(tasks)}


@router.get("/assignees/search", tags=["bitrix"])
def search_assignees(q: str = Query(default="")):
    service = _bitrix_service()
    try:
        return [{"id": user.id, "name": user.name} for user in service.search_users(q)]
    except BitrixUnavailableError:
        raise HTTPException(status_code=503, detail="Сервис Bitrix24 временно недоступен") from None


router.include_router(migration_router)
