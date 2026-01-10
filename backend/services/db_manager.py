import yaml
from typing import Dict, Any, List

from services.connectors.base_connector import BaseConnector
from services.connectors.postgres_connector import PostgresConnector
from services.connectors.mongo_connector import MongoConnector
from services.connectors.redis_connector import RedisConnector
from services.connectors.mysql_connector import MySqlConnector
from services.connectors.sqlite_connector import SQLiteConnector
# from services.connectors.elasticsearch_connector import ElasticsearchConnector
# from services.connectors.bigquery_connector import BigQueryConnector
from models.database import AppConfig, DBConnection


class DbManager:
    _instance = None
    _connectors: Dict[str, BaseConnector] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DbManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        with open("config/config.yaml", "r") as f:
            self.config = yaml.safe_load(f)
        self._initialize_connectors()

    def _initialize_connectors(self):
        db_configs = self.config.get("databases", {})
        for db_id, db_info in db_configs.items():
            engine = db_info.get("engine")
            if engine == "postgresql":
                self._connectors[db_id] = PostgresConnector(db_info)
            elif engine == "mysql":
                self._connectors[db_id] = MySqlConnector(db_info)
            elif engine == "mongodb":
                self._connectors[db_id] = MongoConnector(db_info)
            elif engine == "redis":
                self._connectors[db_id] = RedisConnector(db_info)
            elif engine == "sqlite":
                self._connectors[db_id] = SQLiteConnector(db_info)
            # elif engine == "elasticsearch":
            #     self._connectors[db_id] = ElasticsearchConnector(db_info)
            # elif engine == "bigquery":
            #     self._connectors[db_id] = BigQueryConnector(db_info)
            else:
                print(
                    f"Warning: Unsupported database engine '{engine}' for db_id '{db_id}'."
                )

    def get_connector(self, db_id: str) -> BaseConnector:
        connector = self._connectors.get(db_id)
        if not connector:
            raise ValueError(f"No connector found for db_id: {db_id}")
        return connector

    def get_app_config(self) -> AppConfig:
        db_connections = []
        for db_id, db_info in self.config.get("databases", {}).items():
            db_connections.append(
                DBConnection(
                    id=db_id,
                    name=db_info.get("name"),
                    engine=db_info.get("engine"),
                    allow_mutations=db_info.get("allow_mutations", False),
                )
            )

        llm_providers = list(self.config.get("llm", {}).get("providers", {}).keys())

        return AppConfig(databases=db_connections, llm_providers=llm_providers)

    def get_db_config(self, db_id: str) -> Dict[str, Any]:
        return self.config.get("databases", {}).get(db_id)

    def get_db_engine(self, db_id: str) -> str:
        db_info = self.get_db_config(db_id)
        if not db_info:
            raise ValueError(f"Database config not found for id: {db_id}")
        return db_info.get("engine")

    async def get_schema(self, db_id: str) -> List[Dict[str, Any]]:
        connector = self.get_connector(db_id)
        return await connector.get_schema()

    async def get_schema_for_prompt(self, db_id: str) -> str:
        connector = self.get_connector(db_id)
        return await connector.get_schema_for_prompt()

    async def get_sample_data(self, db_id: str, object_name: str) -> Dict[str, Any]:
        connector = self.get_connector(db_id)
        return await connector.get_sample_data(object_name)

    async def execute_query(self, db_id: str, query: str) -> Dict[str, Any]:
        connector = self.get_connector(db_id)
        return await connector.execute_query(query)

    def is_mutation_query(self, db_id: str, query: str) -> bool:
        connector = self.get_connector(db_id)
        return connector.is_mutation(query)
