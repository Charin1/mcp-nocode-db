import aiosqlite
from typing import List, Dict, Any
from services.connectors.base_connector import BaseConnector

class SQLiteConnector(BaseConnector):
    def __init__(self, db_config: Dict[str, Any]):
        super().__init__(db_config)
        self.db_path = db_config.get("path")
        if not self.db_path:
            raise ValueError("SQLite config requires 'path'")
    
    async def connect(self):
        pass 

    async def disconnect(self):
        pass

    async def get_schema(self) -> List[Dict[str, Any]]:
        # Query sqlite_master
        schema = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';") as cursor:
                tables = await cursor.fetchall()
                for name, sql in tables:
                     # Get columns
                     columns = []
                     async with db.execute(f"PRAGMA table_info({name})") as col_cursor:
                         cols = await col_cursor.fetchall()
                         for col in cols:
                             # cid, name, type, notnull, dflt_value, pk
                             columns.append({"name": col[1], "type": col[2]})
                     schema.append({"name": name, "type": "table", "ddl": sql, "columns": columns})
        return schema

    async def get_schema_for_prompt(self) -> str:
        async with aiosqlite.connect(self.db_path) as db:
            # Filter out sqlite internal tables if needed
            async with db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';") as cursor:
                rows = await cursor.fetchall()
                return "\n\n".join([row[0] for row in rows if row[0]])

    async def get_sample_data(self, object_name: str) -> Dict[str, Any]:
         async with aiosqlite.connect(self.db_path) as db:
             db.row_factory = aiosqlite.Row
             try:
                async with db.execute(f"SELECT * FROM {object_name} LIMIT 3") as cursor:
                    rows = await cursor.fetchall()
                    return {"data": [dict(row) for row in rows]}
             except Exception as e:
                 return {"error": str(e)}

    async def execute_query(self, query: str) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query) as cursor:
                if query.strip().upper().startswith("SELECT") or query.strip().upper().startswith("WITH"):
                    rows = await cursor.fetchall()
                    columns = [description[0] for description in cursor.description] if cursor.description else []
                    return {"columns": columns, "rows": [dict(row) for row in rows]}
                else:
                    await db.commit()
                    return {"rows_affected": cursor.rowcount}

    def is_mutation(self, query: str) -> bool:
        normalized = query.strip().upper()
        return any(normalized.startswith(kw) for kw in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE"])
