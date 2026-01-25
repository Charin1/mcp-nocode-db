
import asyncio
import json
import sys
import os

# Ensure backend is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.connectors.mongo_connector import MongoConnector

async def test_mongo_crud():
    print("Starting MongoDB CRUD Test...")
    
    # Configuration for local mongo
    db_config = {
        "engine": "mongodb",
        "connection_string": "mongodb://localhost:27017/",
        "dbname": "nocode_test_db_custom"
    }
    
    connector = MongoConnector(db_config)
    
    # 1. Connect
    print("Connecting...")
    await connector.connect()
    
    # 2. Insert One
    print("Testing Insert One...")
    insert_payload = json.dumps({
        "collection": "users",
        "operation": "insert_one",
        "data": {"name": "Test User", "email": "test@example.com"}
    })
    result = await connector.execute_query(insert_payload)
    print(f"Insert One Result: {result}")
    assert result["rows_affected"] == 1
    
    # 3. Insert Many
    print("Testing Insert Many...")
    insert_many_payload = json.dumps({
        "collection": "users",
        "operation": "insert_many",
        "data": [
            {"name": "User 2", "email": "user2@example.com"},
            {"name": "User 3", "email": "user3@example.com"}
        ]
    })
    result = await connector.execute_query(insert_many_payload)
    print(f"Insert Many Result: {result}")
    assert result["rows_affected"] == 2
    
    # 4. Find
    print("Testing Find...")
    find_payload = json.dumps({
        "collection": "users",
        "filter": {"name": "Test User"}
    })
    result = await connector.execute_query(find_payload)
    print(f"Find Result: {len(result['json_result'])} docs found")
    assert len(result["json_result"]) >= 1
    assert result["json_result"][0]["name"] == "Test User"
    
    # 5. Update
    print("Testing Update...")
    update_payload = json.dumps({
        "collection": "users",
        "operation": "update_one",
        "filter": {"name": "Test User"},
        "update": {"$set": {"role": "admin"}}
    })
    result = await connector.execute_query(update_payload)
    print(f"Update Result: {result}")
    
    # Verify Update
    result = await connector.execute_query(find_payload)
    assert result["json_result"][0].get("role") == "admin"
    
    # 6. Delete
    print("Testing Delete...")
    delete_payload = json.dumps({
        "collection": "users",
        "operation": "delete_many",
        "filter": {}
    })
    result = await connector.execute_query(delete_payload)
    print(f"Delete Result: {result}")
    
    await connector.disconnect()
    print("✅ MongoDB CRUD Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_mongo_crud())
