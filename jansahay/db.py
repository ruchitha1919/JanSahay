"""SQLite persistence for the local JanSahay demonstration."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jansahay.sqlite3"
CASE_STATUSES = ("New", "In Progress", "Waiting for Documents", "Resolved")


def _database_path(path: str | Path | None = None) -> Path:
    configured = path or os.environ.get("JANSAHAY_DB_PATH") or DEFAULT_DB_PATH
    return Path(configured).expanduser().resolve()


@contextmanager
def _connect(path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    database_path = _database_path(path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _password_hash(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000).hex()


def _row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def initialize_database(path: str | Path | None = None) -> None:
    """Create the schema and idempotently seed the synthetic demo account."""
    with _connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS citizens (
                citizen_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                district TEXT NOT NULL DEFAULT '',
                occupation TEXT NOT NULL DEFAULT '',
                language TEXT NOT NULL DEFAULT 'English',
                age INTEGER,
                annual_income REAL,
                land_acres REAL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                citizen_id TEXT NOT NULL REFERENCES citizens(citizen_id),
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                stage TEXT NOT NULL,
                required_documents TEXT NOT NULL DEFAULT '[]',
                assigned_volunteer TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS documents (
                document_id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                citizen_id TEXT NOT NULL REFERENCES citizens(citizen_id),
                file_name TEXT NOT NULL,
                extracted_text TEXT NOT NULL,
                explanation TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Submitted',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                citizen_id TEXT NOT NULL REFERENCES citizens(citizen_id),
                case_id TEXT REFERENCES cases(case_id) ON DELETE SET NULL,
                message TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS interactions (
                interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                citizen_id TEXT REFERENCES citizens(citizen_id) ON DELETE SET NULL,
                kind TEXT NOT NULL,
                user_input TEXT NOT NULL,
                response TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_cases_citizen ON cases(citizen_id);
            CREATE INDEX IF NOT EXISTS idx_documents_case ON documents(case_id);
            CREATE INDEX IF NOT EXISTS idx_notifications_citizen ON notifications(citizen_id);
            CREATE INDEX IF NOT EXISTS idx_interactions_citizen ON interactions(citizen_id);
            """
        )

        salt = bytes.fromhex("62f2c9b8ac6a23ddc7fe0a35f48e24b1")
        connection.execute(
            """INSERT OR IGNORE INTO citizens
               (citizen_id, name, password_hash, password_salt, district, occupation,
                language, age, annual_income, land_acres, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "JS-C10245",
                "Ravi Kumar",
                _password_hash("ravi123", salt),
                salt.hex(),
                "Karimnagar",
                "Farmer",
                "Telugu",
                42,
                180000,
                3.5,
                _now(),
            ),
        )
        connection.executemany(
            """INSERT OR IGNORE INTO cases
               (case_id, citizen_id, title, status, stage, required_documents,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                (
                    "JS-CASE1001",
                    "JS-C10245",
                    "Agricultural Subsidy Assistance",
                    "In Progress",
                    "Profile review",
                    json.dumps(["Aadhaar copy", "Land record", "Bank passbook"]),
                    _now(),
                    _now(),
                ),
                (
                    "JS-CASE1002",
                    "JS-C10245",
                    "Land Notice Assistance",
                    "Waiting for Documents",
                    "Document collection",
                    json.dumps(["Land notice", "Land record"]),
                    _now(),
                    _now(),
                ),
            ),
        )


def _next_id(connection: sqlite3.Connection, table: str, column: str, prefix: str, start: int) -> str:
    rows = connection.execute(f"SELECT {column} FROM {table} WHERE {column} LIKE ?", (f"{prefix}%",))
    numbers = []
    for row in rows:
        suffix = row[0][len(prefix):]
        if suffix.isdigit():
            numbers.append(int(suffix))
    return f"{prefix}{max(numbers, default=start - 1) + 1:05d}"


def create_citizen(
    name: str,
    password: str,
    district: str,
    occupation: str,
    language: str = "English",
    age: int | None = None,
    annual_income: float | None = None,
    land_acres: float | None = None,
    path: str | Path | None = None,
) -> str:
    name = name.strip()
    if not name or not password:
        raise ValueError("Name and password are required.")
    salt = secrets.token_bytes(16)
    with _connect(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        citizen_id = _next_id(connection, "citizens", "citizen_id", "JS-C", 10000)
        connection.execute(
            """INSERT INTO citizens
               (citizen_id, name, password_hash, password_salt, district, occupation,
                language, age, annual_income, land_acres, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                citizen_id,
                name,
                _password_hash(password, salt),
                salt.hex(),
                district.strip(),
                occupation.strip(),
                language,
                age,
                annual_income,
                land_acres,
                _now(),
            ),
        )
        return citizen_id


def get_citizen(citizen_id: str, path: str | Path | None = None) -> dict[str, Any] | None:
    with _connect(path) as connection:
        row = connection.execute(
            """SELECT citizen_id, name, district, occupation, language, age,
                      annual_income, land_acres, created_at
               FROM citizens WHERE citizen_id = ?""",
            (citizen_id,),
        ).fetchone()
    return _row_dict(row)


def authenticate(identifier: str, password: str, path: str | Path | None = None) -> dict[str, Any] | None:
    with _connect(path) as connection:
        row = connection.execute(
            """SELECT citizen_id, name, password_hash, password_salt
               FROM citizens WHERE citizen_id = ? OR lower(name) = lower(?)""",
            (identifier.strip(), identifier.strip()),
        ).fetchone()
    if row is None:
        return None
    salt = bytes.fromhex(row["password_salt"])
    if secrets.compare_digest(_password_hash(password, salt), row["password_hash"]):
        return get_citizen(row["citizen_id"], path)
    return None


def list_citizens(path: str | Path | None = None) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        rows = connection.execute(
            """SELECT citizen_id, name, district, occupation, language, age,
                      annual_income, land_acres, created_at FROM citizens ORDER BY name"""
        ).fetchall()
    return [dict(row) for row in rows]


def create_case(
    citizen_id: str,
    title: str,
    required_documents: list[str] | None = None,
    path: str | Path | None = None,
) -> str:
    with _connect(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        case_id = _next_id(connection, "cases", "case_id", "JS-CASE", 1000)
        now = _now()
        connection.execute(
            """INSERT INTO cases
               (case_id, citizen_id, title, status, stage, required_documents,
                created_at, updated_at)
               VALUES (?, ?, ?, 'New', 'Request received', ?, ?, ?)""",
            (case_id, citizen_id, title.strip(), json.dumps(required_documents or []), now, now),
        )
    return case_id


def get_case(case_id: str, path: str | Path | None = None) -> dict[str, Any] | None:
    with _connect(path) as connection:
        row = connection.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    return _case_dict(row)


def _case_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    item = _row_dict(row)
    if item is not None:
        item["required_documents"] = json.loads(item["required_documents"])
    return item


def list_cases(citizen_id: str | None = None, path: str | Path | None = None) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        if citizen_id is None:
            rows = connection.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM cases WHERE citizen_id = ? ORDER BY created_at DESC", (citizen_id,)
            ).fetchall()
    return [_case_dict(row) for row in rows if row is not None]


def update_case(
    case_id: str,
    *,
    status: str | None = None,
    stage: str | None = None,
    assigned_volunteer: str | None = None,
    path: str | Path | None = None,
) -> dict[str, Any]:
    if status is not None and status not in CASE_STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(CASE_STATUSES)}.")
    updates = {"status": status, "stage": stage, "assigned_volunteer": assigned_volunteer}
    updates = {key: value for key, value in updates.items() if value is not None}
    if not updates:
        result = get_case(case_id, path)
        if result is None:
            raise ValueError("Case not found.")
        return result
    updates["updated_at"] = _now()
    with _connect(path) as connection:
        cursor = connection.execute(
            "UPDATE cases SET " + ", ".join(f"{key} = ?" for key in updates) + " WHERE case_id = ?",
            (*updates.values(), case_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("Case not found.")
    result = get_case(case_id, path)
    if result is None:
        raise ValueError("Case not found.")
    return result


def delete_case(case_id: str, path: str | Path | None = None) -> bool:
    with _connect(path) as connection:
        cursor = connection.execute("DELETE FROM cases WHERE case_id = ?", (case_id,))
    return cursor.rowcount > 0


def add_document(
    case_id: str,
    citizen_id: str,
    file_name: str,
    extracted_text: str,
    explanation: str,
    path: str | Path | None = None,
) -> int:
    with _connect(path) as connection:
        case_row = connection.execute(
            "SELECT citizen_id FROM cases WHERE case_id = ?", (case_id,)
        ).fetchone()
        if case_row is None or case_row["citizen_id"] != citizen_id:
            raise ValueError("Choose a valid case belonging to this citizen.")
        cursor = connection.execute(
            """INSERT INTO documents
               (case_id, citizen_id, file_name, extracted_text, explanation, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (case_id, citizen_id, file_name, extracted_text, explanation, _now()),
        )
        return int(cursor.lastrowid)


def get_document(document_id: int, path: str | Path | None = None) -> dict[str, Any] | None:
    with _connect(path) as connection:
        row = connection.execute(
            "SELECT * FROM documents WHERE document_id = ?", (document_id,)
        ).fetchone()
    return _row_dict(row)


def list_documents(case_id: str, path: str | Path | None = None) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        rows = connection.execute(
            "SELECT * FROM documents WHERE case_id = ? ORDER BY created_at", (case_id,)
        ).fetchall()
    return [dict(row) for row in rows]


def update_document_status(
    document_id: int, status: str, path: str | Path | None = None
) -> dict[str, Any]:
    with _connect(path) as connection:
        cursor = connection.execute(
            "UPDATE documents SET status = ? WHERE document_id = ?", (status, document_id)
        )
        if cursor.rowcount == 0:
            raise ValueError("Document not found.")
    result = get_document(document_id, path)
    if result is None:
        raise ValueError("Document not found.")
    return result


def delete_document(document_id: int, path: str | Path | None = None) -> bool:
    with _connect(path) as connection:
        cursor = connection.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
    return cursor.rowcount > 0


def delete_citizen_documents(citizen_id: str, path: str | Path | None = None) -> int:
    with _connect(path) as connection:
        cursor = connection.execute("DELETE FROM documents WHERE citizen_id = ?", (citizen_id,))
    return cursor.rowcount


def create_notification(
    citizen_id: str,
    message: str,
    case_id: str | None = None,
    path: str | Path | None = None,
) -> int:
    with _connect(path) as connection:
        cursor = connection.execute(
            """INSERT INTO notifications (citizen_id, case_id, message, created_at)
               VALUES (?, ?, ?, ?)""",
            (citizen_id, case_id, message, _now()),
        )
        return int(cursor.lastrowid)


def list_notifications(citizen_id: str, path: str | Path | None = None) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        rows = connection.execute(
            """SELECT * FROM notifications WHERE citizen_id = ?
               ORDER BY created_at DESC, notification_id DESC""",
            (citizen_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def mark_notification_read(notification_id: int, path: str | Path | None = None) -> bool:
    with _connect(path) as connection:
        cursor = connection.execute(
            "UPDATE notifications SET is_read = 1 WHERE notification_id = ?", (notification_id,)
        )
    return cursor.rowcount > 0


def delete_notification(notification_id: int, path: str | Path | None = None) -> bool:
    with _connect(path) as connection:
        cursor = connection.execute(
            "DELETE FROM notifications WHERE notification_id = ?", (notification_id,)
        )
    return cursor.rowcount > 0


def log_interaction(
    citizen_id: str | None,
    kind: str,
    user_input: str,
    response: str,
    path: str | Path | None = None,
) -> int:
    with _connect(path) as connection:
        cursor = connection.execute(
            """INSERT INTO interactions (citizen_id, kind, user_input, response, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (citizen_id, kind, user_input, response, _now()),
        )
        return int(cursor.lastrowid)


def list_interactions(
    citizen_id: str | None = None, kind: str | None = None, path: str | Path | None = None
) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        if citizen_id is None and kind is None:
            rows = connection.execute(
                "SELECT * FROM interactions ORDER BY created_at, interaction_id"
            ).fetchall()
        elif citizen_id is None:
            rows = connection.execute(
                "SELECT * FROM interactions WHERE kind = ? ORDER BY created_at, interaction_id",
                (kind,),
            ).fetchall()
        elif kind is None:
            rows = connection.execute(
                """SELECT * FROM interactions WHERE citizen_id = ?
                   ORDER BY created_at, interaction_id""",
                (citizen_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                """SELECT * FROM interactions WHERE citizen_id = ? AND kind = ?
                   ORDER BY created_at, interaction_id""",
                (citizen_id, kind),
            ).fetchall()
    return [dict(row) for row in rows]


def update_interaction_response(
    interaction_id: int, response: str, path: str | Path | None = None
) -> bool:
    with _connect(path) as connection:
        cursor = connection.execute(
            "UPDATE interactions SET response = ? WHERE interaction_id = ?",
            (response, interaction_id),
        )
    return cursor.rowcount > 0


def delete_interaction(interaction_id: int, path: str | Path | None = None) -> bool:
    with _connect(path) as connection:
        cursor = connection.execute(
            "DELETE FROM interactions WHERE interaction_id = ?", (interaction_id,)
        )
    return cursor.rowcount > 0