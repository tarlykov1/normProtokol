from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.migration import VerificationResult
from app.schemas.migration import (
    CommentsMigrateRequest,
    CreateRunResponse,
    DomainSyncRequest,
    ExecutePipelineRequest,
    FileRefsMigrateRequest,
    TasksMigrateRequest,
    UsersOverrideRequest,
    UsersSyncRequest,
    VerifyCountsRequest,
)
from app.services.migration.data_plane import DataPlaneMigrationService

router = APIRouter(prefix="/migration", tags=["migration"])


@router.post("/runs", response_model=CreateRunResponse)
def create_run(db: Session = Depends(get_db)):
    run = DataPlaneMigrationService(db).create_run()
    return CreateRunResponse(run_id=run.id, status=run.status)


@router.post("/users/map")
def sync_users(payload: UsersSyncRequest, db: Session = Depends(get_db)):
    return DataPlaneMigrationService(db).sync_users(payload.run_id, payload.source_users, payload.target_users)


@router.get("/users/unresolved")
def unresolved_users(run_id: int = Query(...), status: str | None = Query(default=None), db: Session = Depends(get_db)):
    rows = DataPlaneMigrationService(db).get_unresolved_users(run_id, status)
    return [
        {
            "id": row.id,
            "source_id": row.source_id,
            "status": row.status,
            "target_id": row.target_id,
            "resolution_strategy": row.resolution_strategy,
            "match_reason": row.match_reason,
            "risk_notes": row.risk_notes,
            "meta": row.meta,
        }
        for row in rows
    ]


@router.post("/users/review/override")
def override_user(payload: UsersOverrideRequest, db: Session = Depends(get_db)):
    row = DataPlaneMigrationService(db).override_user_mapping(payload.run_id, payload.source_id, payload.target_id)
    return {"source_id": row.source_id, "target_id": row.target_id, "status": row.status, "resolution_strategy": row.resolution_strategy}


@router.post("/groups/sync")
def sync_groups(payload: DomainSyncRequest, db: Session = Depends(get_db)):
    report = DataPlaneMigrationService(db).sync_container_domain(payload.run_id, "groups", payload.source_items, payload.target_items)
    return report.__dict__


@router.post("/projects/sync")
def sync_projects(payload: DomainSyncRequest, db: Session = Depends(get_db)):
    report = DataPlaneMigrationService(db).sync_container_domain(payload.run_id, "projects", payload.source_items, payload.target_items)
    return report.__dict__


@router.post("/tasks/migrate")
def migrate_tasks(payload: TasksMigrateRequest, db: Session = Depends(get_db)):
    report = DataPlaneMigrationService(db).migrate_tasks(payload.run_id, payload.tasks)
    return report.__dict__


@router.post("/comments/migrate")
def migrate_comments(payload: CommentsMigrateRequest, db: Session = Depends(get_db)):
    report = DataPlaneMigrationService(db).migrate_comments(payload.run_id, payload.comments)
    return report.__dict__


@router.post("/files/migrate")
def migrate_file_refs(payload: FileRefsMigrateRequest, db: Session = Depends(get_db)):
    report = DataPlaneMigrationService(db).migrate_file_refs(payload.run_id, payload.file_refs)
    return report.__dict__


@router.post("/verify/counts")
def verify_counts(payload: VerifyCountsRequest, db: Session = Depends(get_db)):
    return DataPlaneMigrationService(db).verify_counts(payload.run_id, payload.source_counts)


@router.post("/verify/relations")
def verify_relations(run_id: int = Query(...), db: Session = Depends(get_db)):
    return DataPlaneMigrationService(db).verify_relations(run_id)


@router.post("/verify/integrity")
def verify_integrity(run_id: int = Query(...), db: Session = Depends(get_db)):
    return DataPlaneMigrationService(db).verify_integrity(run_id)


@router.post("/verify/files")
def verify_files(run_id: int = Query(...), db: Session = Depends(get_db)):
    return DataPlaneMigrationService(db).verify_files(run_id)


@router.get("/verify/results")
def list_verification_results(run_id: int = Query(...), db: Session = Depends(get_db)):
    rows = db.query(VerificationResult).filter(VerificationResult.run_id == run_id).order_by(VerificationResult.id.desc()).all()
    return [
        {"domain": row.domain, "check_type": row.check_type, "status": row.status, "details": row.details, "created_at": row.created_at.isoformat()}
        for row in rows
    ]


@router.post("/execute")
def execute_pipeline(payload: ExecutePipelineRequest, db: Session = Depends(get_db)):
    svc = DataPlaneMigrationService(db)
    users = svc.sync_users(payload.run_id, payload.source_users, payload.target_users)
    unresolved = svc.get_unresolved_users(payload.run_id)
    if unresolved:
        return {
            "status": "blocked",
            "blocked_domain": "users",
            "unresolved_users": len(unresolved),
            "users": users,
        }

    groups = svc.sync_container_domain(payload.run_id, "groups", payload.source_groups, payload.target_groups).__dict__
    projects = svc.sync_container_domain(payload.run_id, "projects", payload.source_projects, payload.target_projects).__dict__
    tasks = svc.migrate_tasks(payload.run_id, payload.tasks).__dict__
    comments = svc.migrate_comments(payload.run_id, payload.comments).__dict__
    files = svc.migrate_file_refs(payload.run_id, payload.file_refs).__dict__

    return {
        "status": "completed",
        "users": users,
        "groups": groups,
        "projects": projects,
        "tasks": tasks,
        "comments": comments,
        "file_refs": files,
    }


@router.post("/resume")
def resume_pipeline(payload: ExecutePipelineRequest, start_from: str = Query(...), db: Session = Depends(get_db)):
    svc = DataPlaneMigrationService(db)
    allowed = ["groups", "projects", "tasks", "comments", "file_refs"]
    if start_from not in allowed:
        raise HTTPException(status_code=400, detail=f"start_from must be one of: {', '.join(allowed)}")

    result: dict[str, object] = {"status": "completed", "start_from": start_from}
    if start_from in ["groups", "projects", "tasks", "comments", "file_refs"]:
        result["groups"] = svc.sync_container_domain(payload.run_id, "groups", payload.source_groups, payload.target_groups).__dict__
    if start_from in ["projects", "tasks", "comments", "file_refs"]:
        result["projects"] = svc.sync_container_domain(payload.run_id, "projects", payload.source_projects, payload.target_projects).__dict__
    if start_from in ["tasks", "comments", "file_refs"]:
        result["tasks"] = svc.migrate_tasks(payload.run_id, payload.tasks).__dict__
    if start_from in ["comments", "file_refs"]:
        result["comments"] = svc.migrate_comments(payload.run_id, payload.comments).__dict__
    if start_from in ["file_refs"]:
        result["file_refs"] = svc.migrate_file_refs(payload.run_id, payload.file_refs).__dict__

    return result
