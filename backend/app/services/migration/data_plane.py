from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.migration import DomainExecution, EntityMapping, MigratedRecord, MigrationRun, VerificationResult

DEPENDENCIES: dict[str, list[str]] = {
    "users": [],
    "groups": ["users"],
    "projects": ["users"],
    "tasks": ["users", "groups", "projects"],
    "comments": ["tasks", "users"],
    "file_refs": ["tasks"],
}


@dataclass
class MigrationReport:
    status: str
    migrated: int
    blocked: int
    errors: list[dict[str, Any]]


class DataPlaneMigrationService:
    def __init__(self, db: Session):
        self.db = db

    def create_run(self) -> MigrationRun:
        run = MigrationRun(status="draft")
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def _upsert_mapping(
        self,
        run_id: int,
        domain: str,
        source_id: str,
        status: str,
        target_id: str | None = None,
        resolution_strategy: str | None = None,
        match_reason: str | None = None,
        risk_notes: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> EntityMapping:
        record = (
            self.db.query(EntityMapping)
            .filter(EntityMapping.run_id == run_id, EntityMapping.domain == domain, EntityMapping.source_id == str(source_id))
            .one_or_none()
        )
        if record is None:
            record = EntityMapping(run_id=run_id, domain=domain, source_id=str(source_id), status=status)
            self.db.add(record)
        record.status = status
        record.target_id = str(target_id) if target_id is not None else None
        record.resolution_strategy = resolution_strategy
        record.match_reason = match_reason
        record.risk_notes = risk_notes
        record.meta = meta
        self.db.flush()
        return record

    def _execute_status(self, run_id: int, domain: str, status: str, details: dict[str, Any]) -> None:
        self.db.add(DomainExecution(run_id=run_id, domain=domain, status=status, details=details))
        self.db.flush()

    def sync_users(self, run_id: int, source_users: list[dict[str, Any]], target_users: list[dict[str, Any]]) -> dict[str, Any]:
        target_by_xml = {str(u.get("xml_id")): u for u in target_users if u.get("xml_id")}
        target_by_email: dict[str, list[dict[str, Any]]] = {}
        target_by_login: dict[str, list[dict[str, Any]]] = {}
        for target in target_users:
            if target.get("email"):
                target_by_email.setdefault(str(target["email"]).lower(), []).append(target)
            if target.get("login"):
                target_by_login.setdefault(str(target["login"]).lower(), []).append(target)

        result = {"matched": 0, "ambiguous": 0, "unmatched": 0}
        for src in source_users:
            source_id = str(src["id"])
            xml_id = src.get("xml_id")
            if xml_id and str(xml_id) in target_by_xml:
                tgt = target_by_xml[str(xml_id)]
                self._upsert_mapping(
                    run_id,
                    "users",
                    source_id,
                    status="resolved",
                    target_id=str(tgt["id"]),
                    resolution_strategy="xml_id",
                    match_reason=f"Matched by XML_ID={xml_id}",
                )
                result["matched"] += 1
                continue

            email = str(src.get("email") or "").lower()
            if email and len(target_by_email.get(email, [])) == 1:
                tgt = target_by_email[email][0]
                self._upsert_mapping(
                    run_id,
                    "users",
                    source_id,
                    status="resolved",
                    target_id=str(tgt["id"]),
                    resolution_strategy="email",
                    match_reason=f"Matched by email={email}",
                )
                result["matched"] += 1
                continue

            login = str(src.get("login") or "").lower()
            if login and len(target_by_login.get(login, [])) == 1:
                tgt = target_by_login[login][0]
                self._upsert_mapping(
                    run_id,
                    "users",
                    source_id,
                    status="resolved",
                    target_id=str(tgt["id"]),
                    resolution_strategy="login",
                    match_reason=f"Matched by login={login}",
                )
                result["matched"] += 1
                continue

            email_candidates = target_by_email.get(email, []) if email else []
            login_candidates = target_by_login.get(login, []) if login else []
            candidates = {str(item["id"]) for item in [*email_candidates, *login_candidates]}
            if len(candidates) > 1:
                self._upsert_mapping(
                    run_id,
                    "users",
                    source_id,
                    status="ambiguous",
                    resolution_strategy="manual_review",
                    match_reason="Multiple candidates found by email/login",
                    risk_notes="Unsafe automatic resolution",
                    meta={"candidate_ids": sorted(candidates)},
                )
                result["ambiguous"] += 1
            else:
                self._upsert_mapping(
                    run_id,
                    "users",
                    source_id,
                    status="unmatched",
                    resolution_strategy="manual_review",
                    match_reason="No unique candidate found",
                )
                result["unmatched"] += 1

        self._execute_status(run_id, "users", "completed", result)
        self.db.commit()
        return result

    def get_unresolved_users(self, run_id: int, status: str | None = None) -> list[EntityMapping]:
        q = self.db.query(EntityMapping).filter(EntityMapping.run_id == run_id, EntityMapping.domain == "users")
        if status:
            q = q.filter(EntityMapping.status == status)
        else:
            q = q.filter(EntityMapping.status.in_(["ambiguous", "unmatched"]))
        return q.order_by(EntityMapping.id.asc()).all()

    def override_user_mapping(self, run_id: int, source_id: str, target_id: str) -> EntityMapping:
        row = self._upsert_mapping(
            run_id,
            "users",
            str(source_id),
            status="resolved",
            target_id=str(target_id),
            resolution_strategy="manual_override",
            match_reason="Manual override from review queue",
            risk_notes="Operator approved",
        )
        self.db.commit()
        return row

    def _ensure_dependencies(self, run_id: int, domain: str) -> list[str]:
        unresolved: list[str] = []
        for dep in DEPENDENCIES.get(domain, []):
            dep_rows = self.db.query(EntityMapping).filter(EntityMapping.run_id == run_id, EntityMapping.domain == dep).all()
            if any(item.status != "resolved" for item in dep_rows):
                unresolved.append(dep)
        return unresolved

    def sync_container_domain(self, run_id: int, domain: str, source_items: list[dict[str, Any]], target_items: list[dict[str, Any]]) -> MigrationReport:
        unresolved = self._ensure_dependencies(run_id, domain)
        if unresolved:
            report = MigrationReport(status="blocked", migrated=0, blocked=len(source_items), errors=[{"reason": "unresolved dependencies", "domains": unresolved}])
            self._execute_status(run_id, domain, "blocked", report.__dict__)
            self.db.commit()
            return report

        target_by_key = {str(item.get("external_key") or item.get("name")).lower(): item for item in target_items}
        migrated = 0
        errors: list[dict[str, Any]] = []
        for src in source_items:
            source_id = str(src["id"])
            key = str(src.get("external_key") or src.get("name")).lower()
            target = target_by_key.get(key)
            if not target:
                target_id = f"created-{domain}-{source_id}"
                risk = None
            else:
                target_id = str(target["id"])
                risk = "Reused existing target entity"

            self._upsert_mapping(
                run_id,
                domain,
                source_id,
                status="resolved",
                target_id=target_id,
                resolution_strategy="external_key_or_name",
                match_reason=f"Matched by {key}",
                risk_notes=risk,
            )
            self.db.add(MigratedRecord(run_id=run_id, domain=domain, source_id=source_id, target_id=target_id, payload=src))
            migrated += 1

        report = MigrationReport(status="completed", migrated=migrated, blocked=0, errors=errors)
        self._execute_status(run_id, domain, "completed", report.__dict__)
        self.db.commit()
        return report

    def migrate_tasks(self, run_id: int, tasks: list[dict[str, Any]]) -> MigrationReport:
        unresolved = self._ensure_dependencies(run_id, "tasks")
        if unresolved:
            report = MigrationReport(status="blocked", migrated=0, blocked=len(tasks), errors=[{"reason": "unresolved dependencies", "domains": unresolved}])
            self._execute_status(run_id, "tasks", "blocked", report.__dict__)
            self.db.commit()
            return report

        users = self._mapping_index(run_id, "users")
        groups = self._mapping_index(run_id, "groups")
        projects = self._mapping_index(run_id, "projects")
        migrated, blocked = 0, 0
        errors: list[dict[str, Any]] = []

        for task in tasks:
            refs_ok = True
            missing_refs: list[str] = []
            for key, mapping in [("author_id", users), ("responsible_id", users), ("group_id", groups), ("project_id", projects)]:
                value = task.get(key)
                if value is not None and str(value) not in mapping:
                    refs_ok = False
                    missing_refs.append(key)
            if not refs_ok:
                blocked += 1
                errors.append({"task_id": str(task.get("id")), "missing_refs": missing_refs})
                continue

            source_id = str(task["id"])
            target_id = f"task-{source_id}"
            self._upsert_mapping(
                run_id,
                "tasks",
                source_id,
                status="resolved",
                target_id=target_id,
                resolution_strategy="create_or_update",
                match_reason="Task migrated with mapped references",
            )
            self.db.add(MigratedRecord(run_id=run_id, domain="tasks", source_id=source_id, target_id=target_id, payload=task))
            migrated += 1

        status = "completed" if blocked == 0 else "partial"
        report = MigrationReport(status=status, migrated=migrated, blocked=blocked, errors=errors)
        self._execute_status(run_id, "tasks", status, report.__dict__)
        self.db.commit()
        return report

    def migrate_comments(self, run_id: int, comments: list[dict[str, Any]]) -> MigrationReport:
        unresolved = self._ensure_dependencies(run_id, "comments")
        if unresolved:
            report = MigrationReport(status="blocked", migrated=0, blocked=len(comments), errors=[{"reason": "unresolved dependencies", "domains": unresolved}])
            self._execute_status(run_id, "comments", "blocked", report.__dict__)
            self.db.commit()
            return report

        users = self._mapping_index(run_id, "users")
        tasks = self._mapping_index(run_id, "tasks")
        migrated, blocked, errors = 0, 0, []
        for comment in comments:
            if str(comment.get("author_id")) not in users or str(comment.get("task_id")) not in tasks:
                blocked += 1
                errors.append({"comment_id": str(comment.get("id")), "reason": "missing task/user mapping"})
                continue
            source_id = str(comment["id"])
            target_id = f"comment-{source_id}"
            self._upsert_mapping(run_id, "comments", source_id, "resolved", target_id, "create", "Comment migrated")
            self.db.add(MigratedRecord(run_id=run_id, domain="comments", source_id=source_id, target_id=target_id, payload=comment))
            migrated += 1

        status = "completed" if blocked == 0 else "partial"
        report = MigrationReport(status=status, migrated=migrated, blocked=blocked, errors=errors)
        self._execute_status(run_id, "comments", status, report.__dict__)
        self.db.commit()
        return report

    def migrate_file_refs(self, run_id: int, file_refs: list[dict[str, Any]]) -> MigrationReport:
        unresolved = self._ensure_dependencies(run_id, "file_refs")
        if unresolved:
            report = MigrationReport(status="blocked", migrated=0, blocked=len(file_refs), errors=[{"reason": "unresolved dependencies", "domains": unresolved}])
            self._execute_status(run_id, "file_refs", "blocked", report.__dict__)
            self.db.commit()
            return report

        tasks = self._mapping_index(run_id, "tasks")
        migrated, blocked, errors = 0, 0, []
        for item in file_refs:
            if str(item.get("task_id")) not in tasks:
                blocked += 1
                errors.append({"file_ref_id": str(item.get("id")), "reason": "missing task mapping"})
                continue
            source_id = str(item["id"])
            target_id = f"fileref-{source_id}"
            self._upsert_mapping(
                run_id,
                "file_refs",
                source_id,
                "resolved",
                target_id,
                "metadata_reference_only",
                "File reference metadata migrated; payload copy not implemented",
                risk_notes="partial: payload transfer pending",
            )
            self.db.add(MigratedRecord(run_id=run_id, domain="file_refs", source_id=source_id, target_id=target_id, payload=item))
            migrated += 1

        status = "completed" if blocked == 0 else "partial"
        report = MigrationReport(status=status, migrated=migrated, blocked=blocked, errors=errors)
        self._execute_status(run_id, "file_refs", status, report.__dict__)
        self.db.commit()
        return report

    def _mapping_index(self, run_id: int, domain: str) -> dict[str, str]:
        rows = self.db.query(EntityMapping).filter(EntityMapping.run_id == run_id, EntityMapping.domain == domain, EntityMapping.status == "resolved").all()
        return {row.source_id: str(row.target_id) for row in rows if row.target_id}

    def verify_counts(self, run_id: int, source_counts: dict[str, int]) -> dict[str, Any]:
        details: dict[str, dict[str, int]] = {}
        for domain, source_count in source_counts.items():
            target_count = self.db.query(MigratedRecord).filter(MigratedRecord.run_id == run_id, MigratedRecord.domain == domain).count()
            details[domain] = {"source": source_count, "target": target_count, "delta": target_count - source_count}
        status = "passed" if all(v["delta"] == 0 for v in details.values()) else "warning"
        self.db.add(VerificationResult(run_id=run_id, domain="all", check_type="counts", status=status, details=details))
        self.db.commit()
        return {"status": status, "details": details}

    def verify_relations(self, run_id: int) -> dict[str, Any]:
        tasks = self.db.query(MigratedRecord).filter(MigratedRecord.run_id == run_id, MigratedRecord.domain == "tasks").all()
        users = self._mapping_index(run_id, "users")
        groups = self._mapping_index(run_id, "groups")
        projects = self._mapping_index(run_id, "projects")
        violations: list[dict[str, Any]] = []
        for task in tasks:
            payload = task.payload or {}
            for key, ref_idx in [("author_id", users), ("responsible_id", users), ("group_id", groups), ("project_id", projects)]:
                value = payload.get(key)
                if value is not None and str(value) not in ref_idx:
                    violations.append({"domain": "tasks", "id": task.source_id, "missing": key})

        comments = self.db.query(MigratedRecord).filter(MigratedRecord.run_id == run_id, MigratedRecord.domain == "comments").all()
        task_map = self._mapping_index(run_id, "tasks")
        for comment in comments:
            payload = comment.payload or {}
            if str(payload.get("author_id")) not in users:
                violations.append({"domain": "comments", "id": comment.source_id, "missing": "author_id"})
            if str(payload.get("task_id")) not in task_map:
                violations.append({"domain": "comments", "id": comment.source_id, "missing": "task_id"})

        file_refs = self.db.query(MigratedRecord).filter(MigratedRecord.run_id == run_id, MigratedRecord.domain == "file_refs").all()
        for file_ref in file_refs:
            payload = file_ref.payload or {}
            if str(payload.get("task_id")) not in task_map:
                violations.append({"domain": "file_refs", "id": file_ref.source_id, "missing": "task_id"})

        status = "passed" if not violations else "failed"
        details = {"violations": violations}
        self.db.add(VerificationResult(run_id=run_id, domain="all", check_type="relations", status=status, details=details))
        self.db.commit()
        return {"status": status, "details": details}

    def verify_integrity(self, run_id: int) -> dict[str, Any]:
        unresolved = self.db.query(EntityMapping).filter(EntityMapping.run_id == run_id, EntityMapping.status.in_(["ambiguous", "unmatched"]))
        unresolved_count = unresolved.count()
        conflicting = (
            self.db.query(EntityMapping.domain, EntityMapping.target_id)
            .filter(EntityMapping.run_id == run_id, EntityMapping.status == "resolved")
            .group_by(EntityMapping.domain, EntityMapping.target_id)
            .having("count(*) > 1")
            .all()
        )
        status = "passed" if unresolved_count == 0 and not conflicting else "failed"
        details = {
            "unresolved_mappings": unresolved_count,
            "conflicting_target_bindings": [{"domain": d, "target_id": t} for d, t in conflicting],
        }
        self.db.add(VerificationResult(run_id=run_id, domain="all", check_type="integrity", status=status, details=details))
        self.db.commit()
        return {"status": status, "details": details}

    def verify_files(self, run_id: int) -> dict[str, Any]:
        refs = self.db.query(EntityMapping).filter(EntityMapping.run_id == run_id, EntityMapping.domain == "file_refs", EntityMapping.status == "resolved").all()
        partial = [row.source_id for row in refs if row.resolution_strategy == "metadata_reference_only"]
        status = "partial" if partial else "passed"
        details = {
            "migrated_refs": len(refs),
            "partial_payload_copy_pending": len(partial),
            "note": "Metadata/reference layer implemented; heavy payload transfer is not implemented in this sprint.",
        }
        self.db.add(VerificationResult(run_id=run_id, domain="file_refs", check_type="files", status=status, details=details))
        self.db.commit()
        return {"status": status, "details": details}
