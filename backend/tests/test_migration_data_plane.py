import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.base import Base
from app.models import entities as _entities  # noqa: F401
from app.models import migration as _migration  # noqa: F401
from app.services.migration.data_plane import DataPlaneMigrationService
from app.db.session import engine


def _build_service():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    return DataPlaneMigrationService(db), db


def test_user_matching_and_ambiguous_handling():
    svc, db = _build_service()
    run = svc.create_run()
    result = svc.sync_users(
        run.id,
        source_users=[
            {"id": "1", "xml_id": "x-1", "email": "a@x.com", "login": "alpha"},
            {"id": "2", "email": "dup@x.com", "login": "dup"},
            {"id": "3", "email": "nomatch@x.com", "login": "none"},
        ],
        target_users=[
            {"id": "10", "xml_id": "x-1", "email": "other@x.com", "login": "other"},
            {"id": "11", "email": "dup@x.com", "login": "dup-a"},
            {"id": "12", "email": "dup@x.com", "login": "dup-b"},
        ],
    )
    assert result == {"matched": 1, "ambiguous": 1, "unmatched": 1}
    unresolved = svc.get_unresolved_users(run.id)
    assert len(unresolved) == 2
    assert {row.status for row in unresolved} == {"ambiguous", "unmatched"}
    db.close()


def test_unresolved_users_block_task_migration():
    svc, db = _build_service()
    run = svc.create_run()
    svc.sync_users(run.id, source_users=[{"id": "1", "login": "nope"}], target_users=[])
    groups = svc.sync_container_domain(run.id, "groups", [{"id": "g1", "name": "G"}], [])
    assert groups.status == "blocked"
    tasks = svc.migrate_tasks(run.id, [{"id": "t1", "author_id": "1", "responsible_id": "1"}])
    assert tasks.status == "blocked"
    assert tasks.blocked == 1
    db.close()


def test_task_comment_and_file_ref_migration_and_verification():
    svc, db = _build_service()
    run = svc.create_run()
    svc.sync_users(
        run.id,
        source_users=[{"id": "1", "login": "alpha"}],
        target_users=[{"id": "10", "login": "alpha"}],
    )
    svc.sync_container_domain(run.id, "groups", [{"id": "g1", "name": "grp"}], [])
    svc.sync_container_domain(run.id, "projects", [{"id": "p1", "name": "prj"}], [])
    task_report = svc.migrate_tasks(
        run.id,
        [{"id": "t1", "author_id": "1", "responsible_id": "1", "group_id": "g1", "project_id": "p1"}],
    )
    assert task_report.status == "completed"
    comment_report = svc.migrate_comments(run.id, [{"id": "c1", "task_id": "t1", "author_id": "1", "text": "ok"}])
    assert comment_report.status == "completed"
    file_report = svc.migrate_file_refs(run.id, [{"id": "f1", "task_id": "t1", "name": "spec.pdf"}])
    assert file_report.status == "completed"

    relations = svc.verify_relations(run.id)
    assert relations["status"] == "passed"
    files = svc.verify_files(run.id)
    assert files["status"] == "partial"
    assert files["details"]["partial_payload_copy_pending"] == 1
    db.close()


def test_api_users_review_and_override_flow():
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    run_resp = client.post("/api/migration/runs")
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run_id"]

    map_resp = client.post(
        "/api/migration/users/map",
        json={
            "run_id": run_id,
            "source_users": [{"id": "u1", "login": "missing"}],
            "target_users": [],
        },
    )
    assert map_resp.status_code == 200

    unresolved = client.get(f"/api/migration/users/unresolved?run_id={run_id}")
    assert unresolved.status_code == 200
    assert unresolved.json()[0]["status"] == "unmatched"

    override = client.post(
        "/api/migration/users/review/override",
        json={"run_id": run_id, "source_id": "u1", "target_id": "u1-target"},
    )
    assert override.status_code == 200
    assert override.json()["status"] == "resolved"


def test_cli_regression_new_commands(tmp_path, capsys, monkeypatch):
    from app import cli

    source = tmp_path / "source.json"
    target = tmp_path / "target.json"
    source.write_text(json.dumps([{"id": "u1", "login": "alpha"}]), encoding="utf-8")
    target.write_text(json.dumps([{"id": "10", "login": "alpha"}]), encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["cli", "run:create"])
    cli.main()
    out = capsys.readouterr().out.strip()
    run_id = json.loads(out)["run_id"]

    monkeypatch.setattr("sys.argv", ["cli", "users:map", "--run-id", str(run_id), "--source", str(source), "--target", str(target)])
    cli.main()
    out = capsys.readouterr().out.strip()
    assert json.loads(out)["matched"] == 1
