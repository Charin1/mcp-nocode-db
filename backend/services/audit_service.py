import sqlite3
import yaml
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


class AuditLogEntry(BaseModel):
    id: int
    timestamp: str
    username: str
    db_id: str
    natural_query: Optional[str] = None
    generated_query: Optional[str] = None
    executed: bool
    success: bool
    error: Optional[str] = None
    rows_returned: Optional[int] = None


class SavedQueryEntry(BaseModel):
    id: int
    username: str
    db_id: str
    name: str
    natural_language_query: Optional[str] = None
    raw_query: str
    created_at: str


class AuditService:
    _db_path = None
    _initialized = False

    @classmethod
    def initialize(cls):
        if cls._initialized:
            return

        with open("config/config.yaml", "r") as f:
            config = yaml.safe_load(f)

        cls._db_path = config["metadata_db"]["path"]

        try:
            conn = sqlite3.connect(cls._db_path)
            cursor = conn.cursor()

            # Create audit_logs table
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                username TEXT NOT NULL,
                db_id TEXT NOT NULL,
                natural_query TEXT,
                generated_query TEXT,
                executed BOOLEAN NOT NULL,
                success BOOLEAN NOT NULL,
                error TEXT,
                rows_returned INTEGER
            )
            """
            )

            # Create saved_queries table
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS saved_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                db_id TEXT NOT NULL,
                name TEXT NOT NULL,
                natural_language_query TEXT,
                raw_query TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
            )

            conn.commit()
            conn.close()
            cls._initialized = True
            print(f"Audit service initialized with database at: {cls._db_path}")
        except Exception as e:
            print(f"FATAL: Could not initialize audit database: {e}")
            raise e

    @classmethod
    def log(cls, **kwargs):
        if not cls._initialized:
            print("Warning: AuditService not initialized. Log will be skipped.")
            return

        conn = sqlite3.connect(cls._db_path)
        cursor = conn.cursor()

        query = """
        INSERT INTO audit_logs (timestamp, username, db_id, natural_query, generated_query, executed, success, error, rows_returned)
        VALUES (:timestamp, :username, :db_id, :natural_query, :generated_query, :executed, :success, :error, :rows_returned)
        """

        params = {
            "timestamp": datetime.utcnow().isoformat(),
            "username": kwargs.get("username"),
            "db_id": kwargs.get("db_id"),
            "natural_query": kwargs.get("natural_query"),
            "generated_query": kwargs.get("generated_query"),
            "executed": kwargs.get("executed"),
            "success": kwargs.get("success"),
            "error": kwargs.get("error"),
            "rows_returned": kwargs.get("rows_returned"),
        }

        cursor.execute(query, params)
        conn.commit()
        conn.close()

    @classmethod
    def get_logs(cls, limit: int = 100) -> List[AuditLogEntry]:
        if not cls._initialized:
            return []

        conn = sqlite3.connect(cls._db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [AuditLogEntry(**row) for row in rows]

    @classmethod
    def save_query(cls, username: str, db_id: str, name: str, natural_query: str, raw_query: str):
        if not cls._initialized:
            return

        conn = sqlite3.connect(cls._db_path)
        cursor = conn.cursor()

        query = """
        INSERT INTO saved_queries (username, db_id, name, natural_language_query, raw_query, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (username, db_id, name, natural_query, raw_query, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()

    @classmethod
    def get_saved_queries(cls, username: str) -> List[SavedQueryEntry]:
        if not cls._initialized:
            return []

        conn = sqlite3.connect(cls._db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM saved_queries WHERE username = ? ORDER BY created_at DESC", (username,))
        rows = cursor.fetchall()
        conn.close()

        return [SavedQueryEntry(**row) for row in rows]

    @classmethod
    def delete_saved_query(cls, query_id: int, username: str):
        if not cls._initialized:
            return

        conn = sqlite3.connect(cls._db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM saved_queries WHERE id = ? AND username = ?", (query_id, username))
        conn.commit()
        conn.close()
