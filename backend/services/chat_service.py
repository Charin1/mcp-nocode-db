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

        # Re-use metadata db path or a new one? Re-using seems safer for "one app db" approach
        cls._db_path = config["metadata_db"]["path"]

        try:
            conn = sqlite3.connect(cls._db_path)
            cursor = conn.cursor()

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
    def create_session(cls, user_id: str, db_id: str, title: str = None) -> ChatSession:
        if not cls._initialized:
             cls.initialize() # Auto-init if needed

        conn = sqlite3.connect(cls._db_path)
        cursor = conn.cursor()
        
        created_at = datetime.utcnow().isoformat()
        if not title:
            title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        cursor.execute(
            "INSERT INTO chat_sessions (user_id, db_id, title, created_at) VALUES (?, ?, ?, ?)",
            (user_id, db_id, title, created_at)
        )
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return ChatSession(
            id=session_id,
            user_id=user_id,
            db_id=db_id,
            title=title,
            created_at=created_at
        )

    @classmethod
    def get_user_sessions(cls, user_id: str) -> List[ChatSession]:
        if not cls._initialized:
             cls.initialize()

        conn = sqlite3.connect(cls._db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY created_at DESC", 
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [ChatSession(**dict(row)) for row in rows]

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
