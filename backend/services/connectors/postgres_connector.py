import psycopg2
import psycopg2.extras
from typing import List, Dict, Any
import re

from .base_connector import BaseConnector


class PostgresConnector(BaseConnector):

    def __init__(self, db_config: Dict[str, Any]):
        super().__init__(db_config)
        self.conn = None

    def _get_dsn(self):
        return f"dbname='{self.db_config['dbname']}' user='{self.db_config['user']}' host='{self.db_config['host']}' password='{self.db_config['password']}' port='{self.db_config.get('port', 5432)}'"

    async def connect(self):
        if not self.conn or self.conn.closed:
            try:
                self.conn = psycopg2.connect(self._get_dsn())
            except psycopg2.OperationalError as e:
                raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")

    async def disconnect(self):
        if self.conn and not self.conn.closed:
            self.conn.close()

    async def get_schema(self) -> List[Dict[str, Any]]:
        await self.connect()
        schema_data = []
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get tables and views
                cur.execute(
                    """
                    SELECT table_name, table_type 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """
                )
                tables = cur.fetchall()
                for table in tables:
                    # Get columns for each table
                    cur.execute(
                        """
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = %s AND table_schema = 'public'
                        ORDER BY ordinal_position;
                    """,
                        (table["table_name"],),
                    )
                    columns = cur.fetchall()
                    # Fetch Constraints correctly for Postgres
                    cur.execute(
                        """
                        SELECT 
                            kcu.column_name, 
                            tc.constraint_type, 
                            ccu.table_name AS foreign_table_name,
                            ccu.column_name AS foreign_column_name 
                        FROM information_schema.table_constraints AS tc 
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                          AND tc.table_schema = kcu.table_schema
                        LEFT JOIN information_schema.constraint_column_usage AS ccu
                          ON ccu.constraint_name = tc.constraint_name
                          AND ccu.table_schema = tc.table_schema
                        WHERE tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY') 
                          AND tc.table_name = %s
                          AND tc.table_schema = 'public';
                        """,
                        (table["table_name"],)
                    )
                    constraints = cur.fetchall()
                    
                    col_details = {}
                    for c in constraints:
                         # psycopg2 DictRow access
                         c_col = c["column_name"]
                         c_type = c["constraint_type"]
                         
                         if c_type == 'PRIMARY KEY':
                              col_details[c_col] = "PK"
                         elif c_type == 'FOREIGN KEY':
                              ref_table = c["foreign_table_name"]
                              ref_col = c["foreign_column_name"]
                              col_details[c_col] = f"FK -> {ref_table}.{ref_col}"

                    schema_data.append(
                        {
                            "name": table["table_name"],
                            "type": (
                                "view" if table["table_type"] == "VIEW" else "table"
                            ),
                            "columns": [
                                {
                                    "name": col["column_name"], 
                                    "type": col["data_type"],
                                    "extra": col_details.get(col["column_name"], "")
                                }
                                for col in columns
                            ],
                        }
                    )
        finally:
            await self.disconnect()
        return schema_data

    async def get_schema_for_prompt(self) -> str:
        schema_list = await self.get_schema()
        prompt_str = ""
        for table in schema_list:
            columns_str = ", ".join(
                [
                    f"{col['name']} ({col['type']}" + (f", {col['extra']})" if col.get('extra') else ")")
                    for col in table["columns"]
                ]
            )
            prompt_str += f"Table {table['name']}: {columns_str}\n"
        return prompt_str.strip()

    async def get_sample_data(self, table_name: str) -> Dict[str, Any]:
        await self.connect()
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Use psycopg2's safe identifier composition
                from psycopg2 import sql

                query = sql.SQL("SELECT * FROM {table} LIMIT 10").format(
                    table=sql.Identifier(table_name)
                )
                cur.execute(query)

                columns = [desc for desc in cur.description]
                rows = [dict(row) for row in cur.fetchall()]
                return {"columns": columns, "rows": rows}
        finally:
            await self.disconnect()

    async def execute_query(
        self, query: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        await self.connect()

        if params:
            for key in params:
                query = query.replace(f":{key}", f"%({key})s")

        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(query, params)

                if cur.description:
                    columns = [desc.name for desc in cur.description]

                    rows = [dict(row) for row in cur.fetchall()]
                    self.conn.commit()
                    return {
                        "columns": columns,
                        "rows": rows,
                        "rows_affected": len(rows),
                    }
                else:
                    self.conn.commit()
                    return {
                        "rows_affected": cur.rowcount,
                        "message": "Query executed successfully.",
                    }
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Query execution failed: {e}")
        finally:
            await self.disconnect()

    def is_mutation(self, query: str) -> bool:
        # A simple but effective check for common mutation keywords at the start of a query
        query_normalized = query.strip().upper()
        mutation_keywords = [
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "CREATE",
            "ALTER",
            "TRUNCATE",
        ]
        return any(
            query_normalized.startswith(keyword) for keyword in mutation_keywords
        )
