
import asyncio
import os
import sys
import argparse
import json
from typing import List

# Add backend to path to import modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from backend.services.db_manager import DbManager
    from backend.services.connectors.base_connector import BaseConnector
except ImportError:
    # If running from inside backend directory
    sys.path.append(os.getcwd())
    from services.db_manager import DbManager
    from services.connectors.base_connector import BaseConnector

async def execute_sql_file(connector: BaseConnector, file_path: str):
    """Reads and executes SQL commands from a file."""
    print(f"Reading seed file: {file_path}")
    if not os.path.exists(file_path):
        print(f"Error: Seed file not found at {file_path}")
        return

    with open(file_path, 'r') as f:
        sql_content = f.read()

    # Split by semicolon to get individual statements
    # This is a simple split and might break on semicolons inside strings
    # For a seed file, this is usually acceptable
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]

    print(f"Found {len(statements)} statements to execute.")
    
    # We need to access the underlying connection/cursor for raw execution if execute_query wraps it too much
    # But connector.execute_query expects a single string.
    # Let's try to use connector.execute_query for each statement.
    
    for i, statement in enumerate(statements):
        try:
            # Skip empty statements
            if not statement:
                continue
                
            # print(f"Executing statement {i+1}...")
            await connector.execute_query(statement)
        except Exception as e:
            print(f"Error executing statement {i+1}: {e}")
            # Continue with next statement? Or stop? 
            # Usually strict stopping is better, but allow continuing for now to see full output
            # print(f"Statement: {statement}")

    print("Seeding completed for this file.")

async def seed_db(target_db: str = None):
    print("Initializing DbManager...")
    manager = DbManager()
    
    databases = manager.config.get("databases", {})
    
    dbs_to_seed = []
    if target_db:
        if target_db not in databases:
            print(f"Error: Database '{target_db}' not found in configuration.")
            return
        dbs_to_seed.append(target_db)
    else:
        dbs_to_seed = list(databases.keys())

    print(f"Databases to seed: {dbs_to_seed}")

    base_path = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    # Adjust for running from root vs backend
    if base_path.endswith('backend'):
        seed_dir = os.path.join(base_path, 'seed_data')
    else:
        seed_dir = os.path.join(base_path, 'backend', 'seed_data')

    for db_id in dbs_to_seed:
        db_config = databases[db_id]
        engine = db_config.get("engine")
        
        print(f"\n--- Seeding {db_id} ({engine}) ---")
        
        try:
            connector = manager.get_connector(db_id)
            
            seed_file = None
            if engine == "postgresql":
                seed_file = "postgres_seed.sql"
            elif engine == "mysql":
                seed_file = "mysql_seed.sql"
            elif engine == "mongodb":
                seed_file = "mongo_seed.json"
                full_path = os.path.join(seed_dir, seed_file)
                print(f"Reading seed file: {full_path}")
                
                if not os.path.exists(full_path):
                    print(f"Error: Seed file not found at {full_path}")
                    continue

                with open(full_path, 'r') as f:
                    mongo_data = json.load(f)
                
                for collection_name, documents in mongo_data.items():
                    print(f"Seeding collection: {collection_name} with {len(documents)} documents...")
                    payload = json.dumps({
                        "collection": collection_name,
                        "operation": "insert_many",
                        "data": documents
                    })
                    try:
                        await connector.execute_query(payload)
                    except Exception as e:
                        print(f"Error seeding collection {collection_name}: {e}")
                
                print("MongoDB seeding completed.")
                continue

            elif engine == "redis":
                seed_file = "redis_seed.txt"
                full_path = os.path.join(seed_dir, seed_file)
                print(f"Reading seed file: {full_path}")
                
                if not os.path.exists(full_path):
                    print(f"Error: Seed file not found at {full_path}")
                    continue

                with open(full_path, 'r') as f:
                    lines = f.readlines()

                print(f"Executing Redis commands from {seed_file}...")
                for line in lines:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue
                    
                    try:
                        # Redis connector expects the full command string
                        await connector.execute_query(line)
                    except Exception as e:
                        print(f"Error executing Redis command '{line}': {e}")
                
                print("Redis seeding completed.")
                continue

            elif engine == "sqlite":
                # Assuming sqlite might use postgres syntax or has its own
                # For now, let's skip or try postgres if compatible
                print(f"Skipping auto-seed for {engine} (no mapping defined)")
                continue
            else:
                print(f"No seed mapping for engine: {engine}")
                continue

            full_path = os.path.join(seed_dir, seed_file)
            await execute_sql_file(connector, full_path)
            
        except Exception as e:
            print(f"Failed to seed {db_id}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed database(s) with initial data.")
    parser.add_argument("--db", type=str, help="Specific database ID to seed (e.g., 'mysql_local'). If omitted, tries to seed all known types.")
    
    args = parser.parse_args()
    
    asyncio.run(seed_db(args.db))
