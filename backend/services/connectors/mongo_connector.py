import motor.motor_asyncio
import json
from typing import List, Dict, Any
from .base_connector import BaseConnector

class MongoConnector(BaseConnector):
    def __init__(self, db_config: Dict[str, Any]):
        super().__init__(db_config)
        self.client = None
        self.db = None

    async def connect(self):
        if not self.client:
            connection_string = self.db_config.get("connection_string", "mongodb://localhost:27017/")
            self.client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)
            # In MongoDB, we might want to specify a default DB in the config or connection string
            # For now, we'll assume the dbname is provided or we'll list all dbs
            self.dbname = self.db_config.get("dbname", "admin")
            self.db = self.client[self.dbname]

    async def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

    async def get_schema(self) -> List[Dict[str, Any]]:
        await self.connect()
        schema_data = []
        collections = await self.db.list_collection_names()
        for coll_name in collections:
            # For MongoDB, "schema" is dynamic. We'll fetch one sample document to see fields.
            sample = await self.db[coll_name].find_one()
            fields = list(sample.keys()) if sample else []
            schema_data.append({
                "name": coll_name,
                "fields": fields
            })
        return schema_data

    async def get_schema_for_prompt(self) -> str:
        schema_list = await self.get_schema()
        prompt_str = "MongoDB Collections and Fields:\n"
        for coll in schema_list:
            prompt_str += f"- Collection: '{coll['name']}', Fields: {', '.join(coll['fields'])}\n"
        return prompt_str.strip()

    async def get_sample_data(self, collection_name: str) -> Dict[str, Any]:
        await self.connect()
        cursor = self.db[collection_name].find().limit(10)
        docs = await cursor.to_list(length=10)
        # Convert ObjectId to string for JSON serialization
        for doc in docs:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
        return {"json_result": docs}

    async def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Executes a MongoDB query. 
        Expects query to be a JSON string representing the filter for find().
        """
        await self.connect()
        try:
            # We assume for now the user is querying the first collection they see or we need a way to specify collection
            # This is a simplification. A better way would be to parse the query or have a multi-part query.
            # For this tool's NL-to-Mongo, we'll try to guess the collection or require it in the prompt.
            # Let's assume the query is a JSON like: {"collection": "users", "filter": {...}}
            query_data = json.loads(query)
            collection_name = query_data.get("collection")
            filter_obj = query_data.get("filter", {})
            
            if not collection_name:
                # Fallback: try to find user's intent or use the first collection
                collections = await self.db.list_collection_names()
                if not collections:
                    return {"error": "No collections found in database."}
                collection_name = collections[0]

            cursor = self.db[collection_name].find(filter_obj).limit(100)
            results = await cursor.to_list(length=100)
            
            for doc in results:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                    
            return {"json_result": results, "rows_affected": len(results)}
        except Exception as e:
            raise RuntimeError(f"MongoDB query failed: {e}")

    def is_mutation(self, query: str) -> bool:
        # Currently only supporting read-only find() via execute_query
        return False
