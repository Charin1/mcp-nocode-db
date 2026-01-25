
import asyncio
import json
import sys
import os

# Ensure backend is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import MongoConnector directly, avoiding DbManager and heavy dependencies
from services.connectors.mongo_connector import MongoConnector

async def seed_mongo():
    print("Starting MongoDB Standalone Seed...")
    
    # Configuration for local mongo
    # Ideally this reads from config.yaml but yaml might be safe to import
    # We'll hardcode default or try to read yaml
    import yaml
    
    # Config is in backend/config/config.yaml
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(backend_dir, "config", "config.yaml")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    mongo_config = config.get("databases", {}).get("mongo_local")
    if not mongo_config:
        print("Error: mongo_local config not found")
        return

    print(f"Using config: {mongo_config}")
    
    connector = MongoConnector(mongo_config)
    seed_file = "mongo_seed.json"
    seed_dir = os.path.join(backend_dir, "seed_data")
    full_path = os.path.join(seed_dir, seed_file)
    
    print(f"Reading seed file: {full_path}")
    if not os.path.exists(full_path):
        print(f"Error: Seed file not found at {full_path}")
        return

    with open(full_path, 'r') as f:
        mongo_data = json.load(f)
    
    await connector.connect()
    
    for collection_name, documents in mongo_data.items():
        print(f"Seeding collection: {collection_name} with {len(documents)} documents...")
        payload = json.dumps({
            "collection": collection_name,
            "operation": "insert_many",
            "data": documents
        })
        try:
            result = await connector.execute_query(payload)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error seeding collection {collection_name}: {e}")
    
    await connector.disconnect()
    print("MongoDB seeding completed.")

if __name__ == "__main__":
    asyncio.run(seed_mongo())
