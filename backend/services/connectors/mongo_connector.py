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
        Expects query to be a JSON string.
        Supported operations:
        - {"collection": "...", "filter": ...}  (Defaults to find)
        - {"collection": "...", "operation": "find", "filter": ...}
        - {"collection": "...", "operation": "insert_one", "data": ...}
        - {"collection": "...", "operation": "insert_many", "data": [...]}
        - {"collection": "...", "operation": "update_one", "filter": ..., "update": ...}
        - {"collection": "...", "operation": "update_many", "filter": ..., "update": ...}
        - {"collection": "...", "operation": "delete_one", "filter": ...}
        - {"collection": "...", "operation": "delete_many", "filter": ...}
        """
        await self.connect()
        try:
            query_data = json.loads(query)
            collection_name = query_data.get("collection")
            
            if not collection_name:
                # Fallback: try to find user's intent or use the first collection
                collections = await self.db.list_collection_names()
                if not collections:
                    return {"error": "No collections found in database."}
                collection_name = collections[0]

            operation = query_data.get("operation", "find")
            coll = self.db[collection_name]
            
            if operation == "find":
                filter_obj = query_data.get("filter", {})
                cursor = coll.find(filter_obj).limit(100)
                results = await cursor.to_list(length=100)
                for doc in results:
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])
                return {"json_result": results, "rows_affected": len(results)}

            elif operation == "insert_one":
                data = query_data.get("data")
                if not data:
                    return {"error": "No data provided for insert_one"}
                result = await coll.insert_one(data)
                return {"json_result": {"inserted_id": str(result.inserted_id)}, "rows_affected": 1}

            elif operation == "insert_many":
                data = query_data.get("data")
                if not data or not isinstance(data, list):
                    return {"error": "Data must be a list for insert_many"}
                result = await coll.insert_many(data)
                return {"json_result": {"inserted_ids": [str(id) for id in result.inserted_ids]}, "rows_affected": len(result.inserted_ids)}

            elif operation == "update_one":
                filter_obj = query_data.get("filter", {})
                update_obj = query_data.get("update")
                if not update_obj:
                    return {"error": "No update object provided for update_one"}
                result = await coll.update_one(filter_obj, update_obj)
                return {"json_result": {"modified_count": result.modified_count}, "rows_affected": result.modified_count}

            elif operation == "update_many":
                filter_obj = query_data.get("filter", {})
                update_obj = query_data.get("update")
                if not update_obj:
                    return {"error": "No update object provided for update_many"}
                result = await coll.update_many(filter_obj, update_obj)
                return {"json_result": {"modified_count": result.modified_count}, "rows_affected": result.modified_count}

            elif operation == "delete_one":
                filter_obj = query_data.get("filter", {})
                result = await coll.delete_one(filter_obj)
                return {"json_result": {"deleted_count": result.deleted_count}, "rows_affected": result.deleted_count}

            elif operation == "delete_many":
                filter_obj = query_data.get("filter", {})
                result = await coll.delete_many(filter_obj)
                return {"json_result": {"deleted_count": result.deleted_count}, "rows_affected": result.deleted_count}

            else:
                return {"error": f"Unsupported operation: {operation}"}

        except Exception as e:
            raise RuntimeError(f"MongoDB query failed: {e}")

    def is_mutation(self, query: str) -> bool:
        try:
            query_data = json.loads(query)
            operation = query_data.get("operation", "find")
            return operation in ["insert_one", "insert_many", "update_one", "update_many", "delete_one", "delete_many"]
        except:
            return False
