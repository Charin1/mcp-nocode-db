
import asyncio
import json
import sys
import os

# Ensure backend is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.connectors.redis_connector import RedisConnector

async def test_redis_crud():
    print("Starting Redis CRUD Test...")
    
    # Configuration for local redis
    db_config = {
        "engine": "redis",
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "allow_mutations": True
    }
    
    connector = RedisConnector(db_config)
    
    # 1. Connect
    print("Connecting...")
    await connector.connect()
    
    try:
        # 2. SET (String)
        print("Testing SET...")
        set_query = "SET test:key 'Hello Redis'"
        result = await connector.execute_query(set_query)
        print(f"SET Result: {result}")
        assert result["rows_affected"] == 1
        
        # 3. GET (String)
        print("Testing GET...")
        get_result = await connector.get_sample_data("test:key")
        print(f"GET Result: {get_result}")
        assert get_result["json_result"]["value"] == "Hello Redis"

        # 4. EXPIRE (Test mutation and TTL effect - though we won't wait for it to expire)
        print("Testing EXPIRE...")
        expire_query = "EXPIRE test:key 60"
        result = await connector.execute_query(expire_query)
        print(f"EXPIRE Result: {result}")
        
        # 5. HSET (Hash)
        print("Testing HSET...")
        hset_query = "HSET test:hash field1 'value1' field2 'value2'"
        result = await connector.execute_query(hset_query)
        print(f"HSET Result: {result}")
        
        # 6. HGETALL (Hash)
        print("Testing HGETALL (via sample data)...")
        hget_result = await connector.get_sample_data("test:hash")
        print(f"HGETALL Result: {hget_result}")
        assert hget_result["json_result"]["value"]["field1"] == "value1"

        # 7. DEL (Cleanup)
        print("Testing DEL...")
        del_query = "DEL test:key test:hash"
        result = await connector.execute_query(del_query)
        print(f"DEL Result: {result}")
        assert result["json_result"] >= 1


    except Exception as e:
        print(f"❌ Test Failed: {e}")
        raise e
    finally:
        await connector.disconnect()
        print("✅ Redis CRUD Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_redis_crud())
