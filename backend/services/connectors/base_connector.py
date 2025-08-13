from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseConnector(ABC):
    """Abstract Base Class for all database connectors."""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.engine = db_config.get("engine")

    @abstractmethod
    async def connect(self):
        """Establish a connection to the database."""
        pass

    @abstractmethod
    async def disconnect(self):
        """Close the connection to the database."""
        pass

    @abstractmethod
    async def get_schema(self) -> List[Dict[str, Any]]:
        """
        Retrieve the schema of the database.
        e.g., list of tables for SQL, collections for MongoDB.
        """
        pass
    
    @abstractmethod
    async def get_schema_for_prompt(self) -> str:
        """
        Retrieve the schema in a string format suitable for an LLM prompt.
        """
        pass

    @abstractmethod
    async def get_sample_data(self, object_name: str) -> Dict[str, Any]:
        """
        Retrieve a few sample rows/documents from a specific table/collection.
        """
        pass

    @abstractmethod
    async def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Execute a raw query and return the results.
        """
        pass

    @abstractmethod
    def is_mutation(self, query: str) -> bool:
        """
        Check if a query is a mutation (e.g., INSERT, UPDATE, DELETE).
        This is a security measure.
        """
        pass