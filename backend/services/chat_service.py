import sqlite3
import yaml
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from models.chat import ChatSession, ChatMessageDB

class ChatService:
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

            # Create projects table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            # Create sessions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    db_id TEXT NOT NULL,
                    title TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            
            # Migration: Check if project_id exists in chat_sessions, if not add it
            cursor.execute("PRAGMA table_info(chat_sessions)")
            columns = [info[1] for info in cursor.fetchall()]
            if "project_id" not in columns:
                print("Migrating chat_sessions: Adding project_id column")
                cursor.execute("ALTER TABLE chat_sessions ADD COLUMN project_id INTEGER DEFAULT NULL REFERENCES projects(id) ON DELETE SET NULL")

            # Create messages table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    query TEXT,
                    chart_config TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
                )
                """
            )

            conn.commit()
            conn.close()
            cls._initialized = True
            print(f"ChatService initialized with database at: {cls._db_path}")
        except Exception as e:
            print(f"FATAL: Could not initialize chat database: {e}")
            raise e

    @classmethod
    def create_project(cls, user_id: str, name: str) -> Dict[str, Any]:
        if not cls._initialized:
             cls.initialize()

        conn = sqlite3.connect(cls._db_path)
        cursor = conn.cursor()
        
        created_at = datetime.utcnow().isoformat()
        cursor.execute(
            "INSERT INTO projects (user_id, name, created_at) VALUES (?, ?, ?)",
            (user_id, name, created_at)
        )
        project_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            "id": project_id,
            "user_id": user_id,
            "name": name,
            "created_at": created_at
        }

    @classmethod
    def get_user_projects(cls, user_id: str) -> List[Dict[str, Any]]:
        if not cls._initialized:
             cls.initialize()

        conn = sqlite3.connect(cls._db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC", 
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    
    @classmethod
    def delete_project(cls, project_id: int, user_id: str) -> bool:
        if not cls._initialized:
             cls.initialize()
        
        conn = sqlite3.connect(cls._db_path)
        cursor = conn.cursor()
        
        # When deleting a project, update sessions to have NULL project_id (handled by ON DELETE SET NULL if strict schema, or manually)
        # SQLite references are tricky by default. Let's do manual update for safety if FK implementation differs.
        cursor.execute("UPDATE chat_sessions SET project_id = NULL WHERE project_id = ? AND user_id = ?", (project_id, user_id))
        
        cursor.execute("DELETE FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    @classmethod
    def create_session(cls, user_id: str, db_id: str, title: str = None, project_id: int = None) -> ChatSession:
        if not cls._initialized:
             cls.initialize() # Auto-init if needed

        conn = sqlite3.connect(cls._db_path)
        cursor = conn.cursor()
        
        created_at = datetime.utcnow().isoformat()
        if not title:
            title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        cursor.execute(
            "INSERT INTO chat_sessions (user_id, db_id, title, project_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, db_id, title, project_id, created_at)
        )
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Note: ChatSession model might need update if we want to return project_id field in Pydantic
        # For now, base fields are fine, but returning project_id is better.
        # Let's assume the callers might want it.
        # We need to make sure ChatSession pydantic model supports extra fields or has project_id if strict.
        # But we haven't updated Pydantic model yet. Let's assume we will or it ignores extra kwtargs.
        return ChatSession(
            id=session_id,
            user_id=user_id,
            db_id=db_id,
            title=title,
            created_at=created_at,
            project_id=project_id 
        )

    @classmethod
    def get_user_sessions(cls, user_id: str, search_query: str = None) -> List[Dict[str, Any]]:
        # Returns Dict instead of ChatSession object directly to include project_id easily without strict validation issues yet
        if not cls._initialized:
             cls.initialize()

        conn = sqlite3.connect(cls._db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if search_query:
            query = "SELECT * FROM chat_sessions WHERE user_id = ? AND title LIKE ? ORDER BY created_at DESC"
            params = (user_id, f"%{search_query}%")
        else:
            query = "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY created_at DESC"
            params = (user_id,)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Return dicts to support project_id field
        return [dict(row) for row in rows]

    @classmethod
    def rename_session(cls, session_id: int, user_id: str, new_title: str) -> bool:
        if not cls._initialized:
             cls.initialize()

        conn = sqlite3.connect(cls._db_path)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE chat_sessions SET title = ? WHERE id = ? AND user_id = ?", 
            (new_title, session_id, user_id)
        )
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
        
    @classmethod
    def move_session_to_project(cls, session_id: int, user_id: str, project_id: Optional[int]) -> bool:
        if not cls._initialized:
             cls.initialize()

        conn = sqlite3.connect(cls._db_path)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE chat_sessions SET project_id = ? WHERE id = ? AND user_id = ?", 
            (project_id, session_id, user_id)
        )
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0

    @classmethod
    def delete_session(cls, session_id: int, user_id: str) -> bool:
        if not cls._initialized:
             cls.initialize()

        conn = sqlite3.connect(cls._db_path)
        cursor = conn.cursor()

        # Cascade delete is configured in table creation, but sqlite needs foreign keys enabled?
        # By default sqlite foreign keys are OFF. We should enable or manually delete messages.
        # Let's enable FK support or manually delete.
        cursor.execute("PRAGMA foreign_keys = ON")
        
        cursor.execute(
            "DELETE FROM chat_sessions WHERE id = ? AND user_id = ?", 
            (session_id, user_id)
        )
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0


    @classmethod
    def get_session(cls, session_id: int, user_id: str) -> Optional[ChatSession]:
        if not cls._initialized:
             cls.initialize()

        conn = sqlite3.connect(cls._db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM chat_sessions WHERE id = ? AND user_id = ?", 
            (session_id, user_id)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            # We construct ChatSession. Note: if ChatSession definition doesn't have project_id, it will be ignored or raise error depending on config.
            # Assuming standard Pydantic.
            return ChatSession(**dict(row))
        return None


    @classmethod
    def add_message(cls, session_id: int, role: str, content: str, query: str = None, chart_config: Dict = None) -> ChatMessageDB:
        if not cls._initialized:
             cls.initialize()

        conn = sqlite3.connect(cls._db_path)
        cursor = conn.cursor()

        created_at = datetime.utcnow().isoformat()
        chart_config_json = json.dumps(chart_config) if chart_config else None

        cursor.execute(
            """
            INSERT INTO chat_messages (session_id, role, content, query, chart_config, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (session_id, role, content, query, chart_config_json, created_at)
        )
        msg_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return ChatMessageDB(
            id=msg_id,
            session_id=session_id,
            role=role,
            content=content,
            query=query,
            chart_config=chart_config,
            created_at=created_at
        )

    @classmethod
    def get_session_messages(cls, session_id: int) -> List[ChatMessageDB]:
        if not cls._initialized:
             cls.initialize()

        conn = sqlite3.connect(cls._db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY id ASC", 
            (session_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        messages = []
        for row in rows:
            d = dict(row)
            if d.get('chart_config'):
                try:
                    d['chart_config'] = json.loads(d['chart_config'])
                except:
                    d['chart_config'] = None
            messages.append(ChatMessageDB(**d))
            
        return messages
