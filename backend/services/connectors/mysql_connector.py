# Note: To use this, you'll need to `uv pip install PyMySQL`
import pymysql
import pymysql.cursors
from typing import List, Dict, Any

from .base_connector import BaseConnector

class MySqlConnector(BaseConnector):
    
    def __init__(self, db_config: Dict[str, Any]):
        super().__init__(db_config)
        self.conn = None

    async def connect(self):
        if not self.conn:
            try:
                self.conn = pymysql.connect(
                    host=self.db_config['host'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    database=self.db_config['dbname'],
                    port=self.db_config.get('port', 3306),
                    cursorclass=pymysql.cursors.DictCursor
                )
            except pymysql.MySQLError as e:
                raise ConnectionError(f"Failed to connect to MySQL: {e}")

    async def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    async def get_schema(self) -> List[Dict[str, Any]]:
        await self.connect()
        schema_data = []
        try:
            with self.conn.cursor() as cursor:
                db_name = self.db_config['dbname']
                cursor.execute("SELECT table_name, table_type FROM information_schema.tables WHERE table_schema = %s", (db_name,))
                tables = cursor.fetchall()
                for table in tables:
                    # Normalize keys to lowercase to handle potential case differences
                    table_lower = {k.lower(): v for k, v in table.items()}
                    t_name = table_lower.get('table_name')
                    t_type = table_lower.get('table_type')
                    
                    cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s AND table_schema = %s", (t_name, db_name))
                    columns = cursor.fetchall()
                    
                    cols_processed = []
                    for col in columns:
                         col_lower = {k.lower(): v for k, v in col.items()}
                         cols_processed.append({"name": col_lower['column_name'], "type": col_lower['data_type']})

                    schema_data.append({
                        "name": t_name,
                        "type": "view" if t_type == 'VIEW' else "table",
                        "columns": cols_processed
                    })
        finally:
            await self.disconnect()
        return schema_data

    async def get_schema_for_prompt(self) -> str:
        schema_list = await self.get_schema()
        prompt_str = ""
        for table in schema_list:
            columns_str = ", ".join([f"{col['name']} ({col['type']})" for col in table['columns']])
            prompt_str += f"Table `{table['name']}`: {columns_str}\n"
        return prompt_str.strip()

    async def get_sample_data(self, table_name: str) -> Dict[str, Any]:
        await self.connect()
        try:
            with self.conn.cursor() as cursor:
                # Note: MySQL uses ` for identifiers
                cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 10")
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return {"columns": columns, "rows": rows}
        finally:
            await self.disconnect()

    async def execute_query(self, query: str) -> Dict[str, Any]:
        await self.connect()
        try:
            with self.conn.cursor() as cursor:
                rows_affected = cursor.execute(query)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    self.conn.commit()
                    return {"columns": columns, "rows": rows, "rows_affected": len(rows)}
                else:
                    self.conn.commit()
                    return {"rows_affected": rows_affected, "message": "Query executed successfully."}
        except pymysql.MySQLError as e:
            self.conn.rollback()
            raise RuntimeError(f"Query execution failed: {e}")
        finally:
            await self.disconnect()

    def is_mutation(self, query: str) -> bool:
        query_normalized = query.strip().upper()
        mutation_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]
        return any(query_normalized.startswith(keyword) for keyword in mutation_keywords)