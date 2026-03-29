import argparse
import json

from app.db.session import SessionLocal, engine
from app.models.base import Base
from app.models import entities as _entities  # noqa: F401
from app.models import migration as _migration  # noqa: F401
from app.services.migration.data_plane import DataPlaneMigrationService


def _load(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Data-plane migration CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run:create")

    users_map = sub.add_parser("users:map")
    users_map.add_argument("--run-id", type=int, required=True)
    users_map.add_argument("--source", required=True)
    users_map.add_argument("--target", required=True)

    users_review = sub.add_parser("users:review")
    users_review.add_argument("--run-id", type=int, required=True)
    users_review.add_argument("--status", default=None)

    users_override = sub.add_parser("users:override")
    users_override.add_argument("--run-id", type=int, required=True)
    users_override.add_argument("--source-id", required=True)
    users_override.add_argument("--target-id", required=True)

    groups_sync = sub.add_parser("groups:sync")
    groups_sync.add_argument("--run-id", type=int, required=True)
    groups_sync.add_argument("--source", required=True)
    groups_sync.add_argument("--target", required=True)

    projects_sync = sub.add_parser("projects:sync")
    projects_sync.add_argument("--run-id", type=int, required=True)
    projects_sync.add_argument("--source", required=True)
    projects_sync.add_argument("--target", required=True)

    tasks_migrate = sub.add_parser("tasks:migrate")
    tasks_migrate.add_argument("--run-id", type=int, required=True)
    tasks_migrate.add_argument("--source", required=True)

    verify_counts = sub.add_parser("verify:counts")
    verify_counts.add_argument("--run-id", type=int, required=True)
    verify_counts.add_argument("--source-counts", required=True)

    sub.add_parser("verify:relations").add_argument("--run-id", type=int, required=True)
    sub.add_parser("verify:integrity").add_argument("--run-id", type=int, required=True)
    sub.add_parser("verify:files").add_argument("--run-id", type=int, required=True)

    args = parser.parse_args()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    svc = DataPlaneMigrationService(db)
    try:
        if args.command == "run:create":
            run = svc.create_run()
            print(json.dumps({"run_id": run.id, "status": run.status}, ensure_ascii=False))
        elif args.command == "users:map":
            print(json.dumps(svc.sync_users(args.run_id, _load(args.source), _load(args.target)), ensure_ascii=False))
        elif args.command == "users:review":
            rows = svc.get_unresolved_users(args.run_id, args.status)
            print(json.dumps([{"source_id": r.source_id, "status": r.status, "meta": r.meta} for r in rows], ensure_ascii=False))
        elif args.command == "users:override":
            row = svc.override_user_mapping(args.run_id, args.source_id, args.target_id)
            print(json.dumps({"source_id": row.source_id, "target_id": row.target_id, "status": row.status}, ensure_ascii=False))
        elif args.command == "groups:sync":
            print(json.dumps(svc.sync_container_domain(args.run_id, "groups", _load(args.source), _load(args.target)).__dict__, ensure_ascii=False))
        elif args.command == "projects:sync":
            print(json.dumps(svc.sync_container_domain(args.run_id, "projects", _load(args.source), _load(args.target)).__dict__, ensure_ascii=False))
        elif args.command == "tasks:migrate":
            print(json.dumps(svc.migrate_tasks(args.run_id, _load(args.source)).__dict__, ensure_ascii=False))
        elif args.command == "verify:counts":
            print(json.dumps(svc.verify_counts(args.run_id, _load(args.source_counts)), ensure_ascii=False))
        elif args.command == "verify:relations":
            print(json.dumps(svc.verify_relations(args.run_id), ensure_ascii=False))
        elif args.command == "verify:integrity":
            print(json.dumps(svc.verify_integrity(args.run_id), ensure_ascii=False))
        elif args.command == "verify:files":
            print(json.dumps(svc.verify_files(args.run_id), ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    main()
