import redis.asyncio as redis
from typing import List, Dict, Any

from .base_connector import BaseConnector

class RedisConnector(BaseConnector):

    def __init__(self, db_config: Dict[str, Any]):
        super().__init__(db_config)
        self.pool = None

    async def connect(self):
        if not self.pool:
            try:
                self.pool = redis.ConnectionPool(
                    host=self.db_config['host'],
                    port=self.db_config.get('port', 6379),
                    db=self.db_config.get('db', 0),
                    password=self.db_config.get('password'),
                    decode_responses=True
                )
            except Exception as e:
                raise ConnectionError(f"Failed to create Redis connection pool: {e}")

    async def disconnect(self):
        if self.pool:
            await self.pool.aclose() # Use aclose() for async pools
            self.pool = None

    async def get_schema(self) -> List[Dict[str, Any]]:
        print("\n--- DEBUG: ENTERING get_schema for Redis ---")
        try:
            await self.connect()
            print("--- DEBUG: Connection successful ---")

            r = redis.Redis.from_pool(self.pool)
            print(f"--- DEBUG: Redis client created: {r} ---")
            
            schema_data = []
            
            print("--- DEBUG: About to call r.scan() ---")
            cursor, key_list = await r.scan(count=100)
            print(f"--- DEBUG: r.scan() successful. Found {len(key_list)} keys. ---")
            
            for i, key in enumerate(key_list):
                print(f"--- DEBUG: Processing key #{i+1}: {key} ---")
                key_type = await r.type(key)
                print(f"--- DEBUG: Key '{key}' is of type '{key_type}' ---")
                schema_data.append({
                    "name": key,
                    "type": key_type,
                })
            
            print("--- DEBUG: Finished processing all keys ---")
            
        except Exception as e:
            # If any error happens, we will now definitely see it
            print(f"\n!!!!!! FATAL ERROR in get_schema: {e} !!!!!!\n")
            # Re-raise the exception to make sure it still causes a 500 error
            raise e
            
        finally:
            await self.disconnect()
            print("--- DEBUG: Disconnected successfully ---\n")
            
        print("--- DEBUG: EXITING get_schema successfully ---")
        return schema_data

    async def get_schema_for_prompt(self) -> str:
        schema_list = await self.get_schema()
        prompt_str = "Redis Keys (sample):\n"
        for key in schema_list:
            prompt_str += f"- Key: '{key['name']}', Type: {key['type']}\n"
        return prompt_str.strip()

    async def get_sample_data(self, key_name: str) -> Dict[str, Any]:
        await self.connect()
        r = redis.Redis.from_pool(self.pool)
        try:
            key_type = await r.type(key_name)
            value = None
            if key_type == 'string':
                value = await r.get(key_name)
            elif key_type == 'list':
                value = await r.lrange(key_name, 0, 9)
            elif key_type == 'hash':
                value = await r.hgetall(key_name)
            elif key_type == 'set':
                value = await r.srandmember(key_name, 10)
            elif key_type == 'zset':
                value = await r.zrange(key_name, 0, 9, withscores=True)
            else:
                value = "Preview for this type is not supported."

            ttl = await r.ttl(key_name)
            return {"json_result": {"key": key_name, "type": key_type, "value": value, "ttl": ttl}}
        finally:
            await self.disconnect()

    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        await self.connect()
        r = redis.Redis.from_pool(self.pool)
        try:
            # FIX 2: Correctly handle arguments for commands.
            # The original code passed a list where a string was expected.
            parts = query.strip().split()
            command = parts[0].upper()
            args = parts[1:]
            
            # Use the generic execute_command for simplicity and power.
            # The security check is handled by the is_mutation method.
            result = await r.execute_command(*parts)

            return {"json_result": result, "rows_affected": 1 if result is not None else 0}
        except Exception as e:
            raise RuntimeError(f"Redis command failed: {e}")
        finally:
            await self.disconnect()

    def is_mutation(self, query: str) -> bool:
        query_normalized = query.strip().upper()
        mutation_keywords = ["SET", "DEL", "HSET", "LPUSH", "RPUSH", "SADD", "ZADD", "INCR", "DECR", "FLUSHDB", "FLUSHALL"]
        return any(query_normalized.startswith(keyword) for keyword in mutation_keywords)