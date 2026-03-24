import sqlite3
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlparse

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
    subprocess.run(["alembic", *args], check=True)


def main() -> None:
    if not settings.database_url.startswith("sqlite"):
        _run_alembic("upgrade", "head")
        return

    db_path = _sqlite_path(settings.database_url)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        _run_alembic("upgrade", "head")
        return

    conn = sqlite3.connect(db_path)
    try:
        has_alembic = _table_exists(conn, "alembic_version")
        if has_alembic:
            _run_alembic("upgrade", "head")
            return

        missing: dict[str, set[str]] = {}
        for table, columns in REQUIRED_COLUMNS.items():
            absent = _missing_columns(conn, table, columns)
            if absent:
                missing[table] = absent

        if missing:
            details = "; ".join(f"{table}: {', '.join(sorted(cols))}" for table, cols in missing.items())
            raise RuntimeError(
                "Обнаружена старая SQLite-схема без alembic_version. "
                f"Не хватает колонок ({details}). "
                "Сделайте backup data/app.db, затем удалите файл и повторите deploy/update."
            )

        _run_alembic("stamp", "head")
        _run_alembic("upgrade", "head")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
