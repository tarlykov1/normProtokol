import sqlite3
import subprocess
from datetime import datetime, timezone
import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings


REQUIRED_COLUMNS = {
    "protocols": {"protocol_type"},
    "task_candidates": {
        "section_name",
        "parent_context",
        "context_label",
        "assignees_raw",
        "assignees_normalized",
        "deadline_kind",
        "deadline_note",
        "markers",
    },
}


def _sqlite_path(database_url: str) -> Path:
    if database_url.startswith("sqlite:///"):
        return Path(database_url.replace("sqlite:///", "", 1)).resolve()
    parsed = urlparse(database_url)
    return Path(unquote(parsed.path)).resolve()


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    return row is not None


def _missing_columns(conn: sqlite3.Connection, table: str, required: set[str]) -> set[str]:
    if not _table_exists(conn, table):
        return required
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    return required - existing


def _run_alembic(*args: str) -> None:
    subprocess.run([sys.executable, "-m", "alembic", *args], check=True)


def _log(message: str) -> None:
    print(f"[db_prepare] {message}", flush=True)


def _backup_and_reset_sqlite(db_path: Path) -> Path:
    backup_name = f"{db_path.stem}.bak-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}{db_path.suffix}"
    backup_path = db_path.with_name(backup_name)
    db_path.rename(backup_path)
    _log(f"Incompatible DB moved to backup: {backup_path}")
    return backup_path


def main() -> None:
    _log(f"Preparing database for URL: {settings.database_url}")

    if not settings.database_url.startswith("sqlite"):
        _log("Non-SQLite DB detected, running alembic upgrade head")
        _run_alembic("upgrade", "head")
        return

    db_path = _sqlite_path(settings.database_url)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        _log(f"SQLite DB does not exist yet ({db_path}), creating via alembic")
        _run_alembic("upgrade", "head")
        return

    conn = sqlite3.connect(db_path)
    try:
        has_alembic = _table_exists(conn, "alembic_version")
        if has_alembic:
            _log("Found alembic_version table, applying migrations")
            _run_alembic("upgrade", "head")
            return

        missing: dict[str, set[str]] = {}
        for table, columns in REQUIRED_COLUMNS.items():
            absent = _missing_columns(conn, table, columns)
            if absent:
                missing[table] = absent

        if missing:
            details = "; ".join(f"{table}: {', '.join(sorted(cols))}" for table, cols in missing.items())
            strategy = os.getenv("SQLITE_INCOMPATIBLE_STRATEGY", "backup_reset").strip().lower()
            message = (
                "Обнаружена старая SQLite-схема без alembic_version. "
                f"Не хватает колонок ({details}). "
                "Рекомендуется backup + пересоздание базы."
            )
            if strategy != "backup_reset":
                raise RuntimeError(f"{message} Текущая стратегия={strategy}, авто-восстановление отключено.")

            _log(message)
            conn.close()
            _backup_and_reset_sqlite(db_path)
            _log("Recreating SQLite DB from alembic migrations")
            _run_alembic("upgrade", "head")
            return

        _log("Legacy SQLite schema is compatible, stamping alembic head")
        _run_alembic("stamp", "head")
        _run_alembic("upgrade", "head")
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        _log(f"FATAL: {exc}")
        raise
