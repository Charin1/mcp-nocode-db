import os
import google.generativeai as genai
from openai import OpenAI
from groq import AsyncGroq
import yaml
import json
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from models.query import GeneratedQuery, ChatMessage


class LLMService:
    cache = {}
    def __init__(self):
        with open("config/config.yaml", "r") as f:
            self.config = yaml.safe_load(f)["llm"]

        # Configure Google Gemini
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            genai.configure(api_key=google_api_key)

        # Configure OpenAI
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        if self.openai_api_key:
             self.openai_client = OpenAI(api_key=self.openai_api_key)

        # Configure Groq
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_client = None
        if self.groq_api_key:
             self.groq_client = AsyncGroq(api_key=self.groq_api_key)

    async def generate_query(
        self, provider: str, natural_language_query: str, schema: str, engine: str
    ) -> GeneratedQuery:
        prompt = self._build_prompt(natural_language_query, schema, engine)

        if provider.lower() == "gemini":
            return await self._generate_with_gemini(prompt, engine)
        elif provider.lower() == "chatgpt":
            return await self._generate_with_chatgpt(prompt, engine)
        elif provider.lower() == "groq":
            return await self._generate_with_groq(prompt, engine)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    async def generate_response_from_messages(
        self, db_id: str, provider: str, messages: List[ChatMessage], schema: str, engine: str, tools: List[Dict[str, Any]] = None
    ) -> ChatMessage:
        last_user_message = next((m.content for m in reversed(messages) if m.role == 'user'), None)

        # Skip caching if tools are involved, as context matters more
        if last_user_message and not tools:
            cache_key = (db_id, last_user_message)
            if cache_key in self.cache:
                print(f"Returning cached response for: {cache_key}")
                return self.cache[cache_key]

        if provider.lower() == "gemini":
            prompt = self._build_chat_prompt(messages, schema, engine, tools)
            raw_response = await self._generate_chat_with_gemini(prompt)
        elif provider.lower() == "chatgpt":
            system_prompt = self._build_chat_system_prompt(schema, engine, tools)
            raw_response = await self._generate_chat_with_chatgpt(system_prompt, messages)
        elif provider.lower() == "groq":
            system_prompt = self._build_chat_system_prompt(schema, engine, tools)
            raw_response = await self._generate_chat_with_groq(system_prompt, messages)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        response = self._parse_chat_response(raw_response, engine)

        if last_user_message and not tools:
            cache_key = (db_id, last_user_message)
            print(f"Caching response for: {cache_key}")
            self.cache[cache_key] = response
        
        return response

    def _build_prompt(self, nl_query: str, schema: str, engine: str) -> str:
        if engine in ["postgresql", "mysql", "sqlite"]:
            return f"""
                Your task is to convert a natural language query into a valid, safe, and parameterized SQL query for a {engine} database.
                ### Instructions
                1.  **ONLY generate SELECT statements.** Never generate INSERT, UPDATE, DELETE, DROP, or any other DDL/DML statements.
                2.  Use named parameters (e.g., `:param_name`) for all literal values in the WHERE clause.
                3.  Return the output in two parts, separated by a `----JSON----` line.
                    - The first part is the SQL query.
                    - The second part is a valid JSON object mapping the parameter names to their values.
                4.  If a value looks like a date or timestamp, ensure the parameter value is a string in 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS' format.
                5.  Analyze the user's query and the database schema carefully.
                ### Database Schema
                {schema}
                ### Natural Language Query
                "{nl_query}"
                ### Your Output
                """

            return f"""
                You are a MongoDB Query Generator. You are NOT a conversational assistant.
                Your ONLY task is to output a JSON object representing a MongoDB query filter.

                ### INPUT
                Natural Language Query: "{nl_query}"
                Database Schema: {schema}

                ### OUTPUT REQUIREMENTS
                1. Output MUST be valid JSON.
                2. Output MUST be enclosed in ```json``` markdown code blocks.
                3. Do NOT include any explanations, introductions, or other text. ONLY the JSON block.
                4. The JSON must have exactly two keys:
                   - "collection": The name of the collection to start with.
                   - "operation": "find" (default) or "aggregate".
                   - "filter": (If operation is "find") The query filter object.
                   - "pipeline": (If operation is "aggregate") The aggregation pipeline list.
                5. Use "aggregate" and $lookup for queries involving relationships (joins).
                6. Use MongoDB operators like $gt, $lt, $in, $regex, etc.

                ### EXAMPLES
                
                Example 1 (Simple Find):
                Input: "Find users older than 25"
                Output:
                ```json
                {{
                  "collection": "users",
                  "operation": "find",
                  "filter": {{ "age": {{ "$gt": 25 }} }}
                }}
                ```
                
                Example 2 (Aggregation/Relationship):
                Input: "Get sales with product details"
                Output:
                ```json
                {{
                  "collection": "sales",
                  "operation": "aggregate",
                  "pipeline": [
                    {{
                        "$lookup": {{
                            "from": "products",
                            "localField": "product_id",
                            "foreignField": "_id",
                            "as": "product_info"
                        }}
                    }},
                    {{ "$unwind": "$product_info" }}
                  ]
                }}
                ```
                
                ### YOUR RESPONSE
                """
        elif engine == "redis":
            return f"""
                Your task is to convert a natural language query into a single, valid Redis CLI command.
                ### Instructions
                1.  Your output MUST be ONLY the command and its arguments.
                2.  Do NOT include any explanations, introductory text, or markdown formatting like ```.
                3.  Do NOT include the word 'redis' or 'redis-cli' before the command.
                ### Database Schema (Sample Keys and Types)
                {schema}
                ### Example
                Natural Language Query: "Show me all the information for the user with profile key 'user:profile:1'"
                Your Output: HGETALL user:profile:1
                ### Your Turn
                Natural Language Query: "{nl_query}"
                Your Output:
                """
        else:
            return f"""
                Given the database schema:
                {schema}
                Convert the following natural language query into a {engine} query:
                "{nl_query}"
                """

    def _build_chat_prompt(
        self, messages: List[ChatMessage], schema: str, engine: str, tools: List[Dict[str, Any]] = None
    ) -> str:
        history = "\n".join([f"{m.role}: {m.content}" for m in messages])

        tools_instruction = ""
        if tools:
            import json
            print(f"DEBUG: Injecting tools into prompt: {[t['name'] for t in tools]}")
            tools_json = json.dumps(tools, indent=2)
            tools_instruction = f"""
            ### Available Tools
            You have access to the following tools:
            {tools_json}

            To use a tool, you MUST use the following format:
            Thought: Do I need to use a tool? Yes
            Action: the name of the tool to use
            Action Input: the input to the tool in JSON format
            Observation: <leave this blank>
            
            When you have a final answer, or if you don't need to use a tool, use:
            Thought: Do I need to use a tool? No
            Final Answer: [your response here]
            """

        if engine == "multi-db":
             return f"""
            You are an intelligent Database Router and Query Generator.
            You have access to valid schemas from multiple databases.

            ### Instructions
            1.  **Analyze**: Look at the user's request and the "Internal Database Connection Schemas" below.
            2.  **Identify**: Determine which specific database contains the tables or data needed.
            3.  **Generate**: Write the valid query for that database's specific engine (SQL, MongoDB, Redis, etc.).
            4.  **Format**: You MUST output the query with the Database ID prefix.
                Format:
                ```
                DB_ID: <db_id_from_schema>
                <query>
                ```
                Example:
                ```
                DB_ID: users_db
                SELECT * FROM users WHERE active = true;
                ```

            {tools_instruction}
            ### Internal Database Connection Schemas
            {schema}
            ### Conversation History
            {history}
            ### Your Response
            """

        elif engine in ["postgresql", "mysql", "sqlite"]:
            return f"""
            You are an expert SQL Query Generator for a {engine.upper()} database.
            You are NOT a conversational assistant. You are a code generation engine.
            Your ONLY purpose is to output valid SQL queries.

            ### Instructions
            1.  **Response Format**:
                - Output the SQL query inside ```sql``` markdown blocks.
                - **NO** introductory text (e.g., "Here is the query").
                - **NO** explaining the query unless asked.
                - **ONLY** the SQL block when generating a query.

            2.  **Orchestration**:
                - If the user asks for data, generate a SQL SELECT query.
                - **ONLY generate SELECT statements.** Never generate INSERT, UPDATE, DELETE, DROP, or DDL.
                - If the user asks a general question *unrelated* to data retrieval, you may answer briefly.

            3.  **SQL Query Guidelines**:
                - Use proper JOIN syntax when combining tables.
                - Use appropriate WHERE clauses for filtering.
                - Use ORDER BY for sorting, LIMIT for pagination.
                - Use aggregate functions (COUNT, SUM, AVG, etc.) when needed.

            4.  **Context**:
                - Use the provided conversation history for context.

            {tools_instruction}
            ### Internal Database Schema
            {schema}
            ### Conversation History
            {history}
            ### Your Response
            """

        elif engine == "mongodb":
            return f"""
            You are an expert MongoDB Query Generator. 
            You are NOT a conversational assistant. You are a code generation engine.
            Your ONLY purpose is to output valid JSON configuration for MongoDB queries.

            ### Instructions
            1.  **Response Format**:
                - Output MUST be a single, valid JSON object.
                - Enclose the JSON in ```json``` markdown blocks.
                - **NO** introductory text.
                - **ONLY** the JSON block.

            2.  **Orchestration**:
                - If the user asks for data, generate the MongoDB JSON.
                - Check **Available Tools** first.

            3.  **MongoDB Query Format**:
                - Return a JSON object with:
                  - "collection": "name"
                  - "operation": "find" or "aggregate"
                  - "filter": {{}} (for find)
                  - "pipeline": [] (for aggregate)
                - Do NOT use JavaScript connection code or `db.collection` syntax. Just the JSON.

            4.  **Context**:
                - Use the provided conversation history for context.

            {tools_instruction}
            ### Internal Database Schema
            {schema}
            ### Conversation History
            {history}
            ### Your Response
            """

        elif engine == "redis":
            return f"""
            You are an expert Redis Command Generator.
            You are NOT a conversational assistant. You are a code generation engine.
            Your ONLY purpose is to output valid Redis CLI commands.

            ### Instructions
            1.  **Response Format**:
                - Output the Redis command inside ```redis``` markdown blocks.
                - **NO** introductory text.
                - **ONLY** the command.

            2.  **Orchestration**:
                - If the user asks for data, generate the appropriate Redis command.
                - Common commands: GET, SET, HGETALL, HGET, HSET, KEYS, SCAN, LRANGE, etc.

            {tools_instruction}
            ### Internal Database Schema (Sample Keys)
            {schema}
            ### Conversation History
            {history}
            ### Your Response
            """

        else:
            # Fallback for unknown engines
            return f"""
            You are a helpful database query assistant for a {engine} database.
            
            ### Instructions
            Generate appropriate queries based on the user's request.
            
            {tools_instruction}
            ### Database Schema
            {schema}
            ### Conversation History
            {history}
            ### Your Response
            """

    def _build_chat_system_prompt(self, schema: str, engine: str, tools: List[Dict[str, Any]] = None) -> str:
        tools_instruction = ""
        if tools:
            import json
            tools_json = json.dumps(tools, indent=2)
            tools_instruction = f"""
            ### Available Tools
            You have access to the following tools:
            {tools_json}

            To use a tool, you MUST use the following format:
            Thought: Do I need to use a tool? Yes
            Action: the name of the tool to use
            Action Input: the input to the tool in JSON format
            Observation: <leave this blank>
            
            When you have a final answer, or if you don't need to use a tool, use:
            Thought: Do I need to use a tool? No
            Final Answer: [your response here]
            """

        if engine in ["postgresql", "mysql", "sqlite"]:
            return f"""
            You are an expert SQL Query Generator for a {engine.upper()} database.
            You are NOT a conversational assistant. You are a code generation engine.
            Your ONLY purpose is to output valid SQL queries.

            ### Instructions
            1.  **Response Format**:
                - Output the SQL query inside ```sql``` markdown blocks.
                - **NO** introductory text (e.g., "Here is the query").
                - **NO** explaining the query unless asked.
                - **ONLY** the SQL block when generating a query.

            2.  **Orchestration**:
                - If the user asks for data, generate a SQL SELECT query.
                - **ONLY generate SELECT statements.** Never generate INSERT, UPDATE, DELETE, DROP, or DDL.
                - If the user asks a general question *unrelated* to data retrieval, you may answer briefly.

            3.  **SQL Query Guidelines**:
                - Use proper JOIN syntax when combining tables.
                - Use appropriate WHERE clauses for filtering.
                - Use ORDER BY for sorting, LIMIT for pagination.
                - Use aggregate functions (COUNT, SUM, AVG, etc.) when needed.

            4.  **Context**:
                - Use the provided conversation history for context.

            {tools_instruction}
            ### Internal Database Schema
            {schema}
            """

        elif engine == "mongodb":
            return f"""
            You are an expert MongoDB Query Generator. 
            You are NOT a conversational assistant. You are a code generation engine.
            Your ONLY purpose is to output valid JSON configuration for MongoDB queries.

            ### Instructions
            1.  **Response Format**:
                - Output MUST be a single, valid JSON object.
                - Enclose the JSON in ```json``` markdown blocks.
                - **NO** introductory text (e.g., "Here is the query").
                - **NO** explaining the query.
                - **NO** "Note:" or "Example:".
                - **ONLY** the JSON block.

            2.  **Orchestration**:
                - If the user asks for data, generate the MongoDB JSON.
                - If the user asks a general question *unrelated* to data retrieval, you may answer briefly.
                - But if the intent is to QUERY DATA, you must return JSON ONLY.
                - Check **Available Tools** first.

            3.  **MongoDB Query Format**:
                - Return a JSON object with:
                  - "collection": "name"
                  - "operation": "find" or "aggregate"
                  - "filter": {{}} (for find)
                  - "pipeline": [] (for aggregate)
                - Do NOT use JavaScript connection code or `db.collection` syntax. Just the JSON.

            4.  **Context**:
                - Use the provided conversation history for context.

            {tools_instruction}
            ### Internal Database Schema
            {schema}
            """

        elif engine == "redis":
            return f"""
            You are an expert Redis Command Generator.
            You are NOT a conversational assistant. You are a code generation engine.
            Your ONLY purpose is to output valid Redis CLI commands.

            ### Instructions
            1.  **Response Format**:
                - Output the Redis command inside ```redis``` markdown blocks.
                - **NO** introductory text.
                - **ONLY** the command.

            2.  **Orchestration**:
                - If the user asks for data, generate the appropriate Redis command.
                - Common commands: GET, SET, HGETALL, HGET, HSET, KEYS, SCAN, LRANGE, etc.

            {tools_instruction}
            ### Internal Database Schema (Sample Keys)
            {schema}
            """

        else:
            return f"""
            You are a helpful database query assistant for a {engine} database.
            
            ### Instructions
            Generate appropriate queries based on the user's request.
            
            {tools_instruction}
            ### Database Schema
            {schema}
            """

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _generate_with_gemini(self, prompt: str, engine: str) -> GeneratedQuery:
        try:
            model_name = self.config["providers"]["gemini"]["model"]
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async(prompt)
            raw_text = ""
            if response.candidates and response.candidates[0].content.parts:
                raw_text = response.candidates[0].content.parts[0].text
            else:
                return GeneratedQuery(
                    raw_query="",
                    error="Error from Gemini API: Received an empty or blocked response.",
                    query_type=engine,
                )
            cleaned_text = (
                raw_text.strip()
                .replace("```sql", "")
                .replace("```json", "")
                .replace("```redis", "")
                .replace("```", "")
            )
            return self._parse_llm_response(cleaned_text, engine)
        except Exception as e:
            # Raise for retry unless it's a fatal error? For simplicity retry all exceptions for now
            raise e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _generate_with_chatgpt(self, prompt: str, engine: str) -> GeneratedQuery:
        if not self.openai_client:
            return GeneratedQuery(
                raw_query="", 
                error="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.", 
                query_type=engine
            )
        try:
            model_name = self.config["providers"]["chatgpt"]["model"]
            response = self.openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that converts natural language to database queries.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            raw_text = response.choices[0].message.content.strip()
            return self._parse_llm_response(raw_text, engine)
        except Exception as e:
            raise e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _generate_with_groq(self, prompt: str, engine: str) -> GeneratedQuery:
        if not self.groq_client:
            return GeneratedQuery(
                raw_query="", 
                error="Groq API key not configured. Please set GROQ_API_KEY environment variable.", 
                query_type=engine
            )
        try:
            model_name = self.config["providers"]["groq"]["model"]
            response = await self.groq_client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that converts natural language to database queries.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            raw_text = response.choices[0].message.content.strip()
            return self._parse_llm_response(raw_text, engine)
        except Exception as e:
            raise e

    def _parse_llm_response(self, text: str, engine: str) -> GeneratedQuery:
        print(f"DEBUG: Raw LLM Response: {repr(text)}") 

        if engine in ["postgresql", "mysql", "sqlite"]:
            import re
            separator_pattern = r"-+\s*JSON\s*-+"
            split = re.split(separator_pattern, text, maxsplit=1, flags=re.IGNORECASE)
            
            if len(split) == 2:
                sql_part = split[0].strip()
                json_part = split[1].strip()
                
                sql_part = re.sub(r"^```sql\s*", "", sql_part, flags=re.IGNORECASE)
                sql_part = re.sub(r"```$", "", sql_part).strip()
                json_part = re.sub(r"^```json\s*", "", json_part, flags=re.IGNORECASE)
                json_part = re.sub(r"```$", "", json_part).strip()
                
                try:
                    params = json.loads(json_part) if json_part else None
                    return GeneratedQuery(
                        raw_query=sql_part, params=params, query_type="sql"
                    )
                except json.JSONDecodeError:
                    return GeneratedQuery(
                        raw_query=sql_part,
                        error="LLM returned invalid JSON for parameters.",
                        query_type="sql",
                    )
            else:
                 cleaned_text = re.sub(r"^```sql\s*", "", text, flags=re.IGNORECASE)
                 cleaned_text = re.sub(r"```$", "", cleaned_text).strip()
                 if ":" not in cleaned_text: 
                     return GeneratedQuery(
                        raw_query=cleaned_text,
                        params=None, 
                        query_type="sql"
                     )
                     
                 return GeneratedQuery(
                    raw_query=text,
                    error="LLM did not return the expected SQL----JSON---- format.",
                    query_type="sql",
                )

        elif engine == "mongodb":
            import re
            # Try to find a JSON block
            match = re.search(r"```(json|mongodb)\s*([\s\S]*?)```", text, re.IGNORECASE)
            if match:
                cleaned_text = match.group(2).strip()
            else:
                # If no code block, try to parse the whole text as JSON as a fallback
                # or maybe it's just raw JSON without backticks
                cleaned_text = text.strip()

            try:
                json.loads(cleaned_text)
                return GeneratedQuery(raw_query=cleaned_text, query_type="mongo_json")
            except json.JSONDecodeError:
                # Fallback: Check if it's a JS-style query like db.users.find({...})
                # Pattern: db.collection.find(filter)
                js_find_pattern = r"db\.(\w+)\.find\((.*)\)"
                js_agg_pattern = r"db\.(\w+)\.aggregate\((.*)\)"
                
                find_match = re.search(js_find_pattern, cleaned_text, re.DOTALL)
                agg_match = re.search(js_agg_pattern, cleaned_text, re.DOTALL)
                
                if find_match:
                    collection = find_match.group(1)
                    filter_str = find_match.group(2).strip()
                    if not filter_str: 
                        filter_str = "{}"
                    # Try to ensure the filter string is valid JSON
                    try:
                        # If it's just {}, it's valid
                        # If keys are not quoted (e.g. {name: "foo"}), json.loads will fail.
                        # This constitutes a best-effort fix.
                        import demjson3 # If available, or use simple regex fix
                        # For now, let's assume LLM gives valid JSON inside parens or clean it up
                        pass 
                    except:
                        pass
                        
                    # Construct our internal JSON format
                    reconstructed_json = json.dumps({
                        "collection": collection,
                        "operation": "find",
                        "filter": json.loads(filter_str) if filter_str else {}
                    })
                    return GeneratedQuery(raw_query=reconstructed_json, query_type="mongo_json")

                elif agg_match:
                    collection = agg_match.group(1)
                    pipeline_str = agg_match.group(2).strip()
                    reconstructed_json = json.dumps({
                        "collection": collection,
                        "operation": "aggregate",
                        "pipeline": json.loads(pipeline_str) if pipeline_str else []
                    })
                    return GeneratedQuery(raw_query=reconstructed_json, query_type="mongo_json")

                return GeneratedQuery(
                    raw_query=cleaned_text,
                    error="LLM returned invalid format. Expected JSON or valid MongoDB JS query.",
                    query_type="mongo_json",
                )
        else:
            return GeneratedQuery(raw_query=text, query_type=engine)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _generate_chat_with_gemini(self, prompt: str) -> str:
        try:
            model_name = self.config["providers"]["gemini"]["model"]
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async(prompt)
            if response.candidates and response.candidates[0].content.parts:
                return response.candidates[0].content.parts[0].text
            else:
                return "Error from Gemini API: Received an empty or blocked response."
        except Exception as e:
            raise e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _generate_chat_with_chatgpt(
        self, system_prompt: str, messages: List[ChatMessage]
    ) -> str:
        if not self.openai_client:
             return "Error: OpenAI API key not configured."
        try:
            model_name = self.config["providers"]["chatgpt"]["model"]
            formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
            response = self.openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *formatted_messages,
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _generate_chat_with_groq(
        self, system_prompt: str, messages: List[ChatMessage]
    ) -> str:
        if not self.groq_client:
             return "Error: Groq API key not configured."
        try:
            model_name = self.config["providers"]["groq"]["model"]
            formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
            response = await self.groq_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *formatted_messages,
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise e

    def _parse_chat_response(self, text: str, engine: str) -> ChatMessage:
        import re
        
        if engine in ["postgresql", "mysql", "sqlite"]:
            query_block_tag = "sql"
        elif engine == "redis":
            query_block_tag = "redis"
        elif engine == "mongodb":
            query_block_tag = "json"
        elif engine == "multi-db":
            # For multi-db, we accept sql or text, but let's try sql first as most common
            query_block_tag = "sql"
        else:
            query_block_tag = "text"

        pattern = rf"```{query_block_tag}\s*([\s\S]*?)```"
        match = re.search(pattern, text, re.IGNORECASE)

        # Fallback for multi-db if sql tag not found, try generic or text
        if not match and engine == "multi-db":
             match = re.search(r"```(text|)\s*([\s\S]*?)```", text, re.IGNORECASE)

        # Fallback for mongodb if json tag was expected but mongodb tag was used
        if not match and engine == "mongodb":
             match = re.search(r"```(mongodb|javascript|js)\s*([\s\S]*?)```", text, re.IGNORECASE)
        
        if match:
            query = match.group(1).strip()
            return ChatMessage(
                role="assistant",
                content="I have generated a query for you. Please review and confirm if you would like to execute it.",
                query=query,
            )
        
        generic_pattern = r"```\s*([\s\S]*?)```"
        generic_match = re.search(generic_pattern, text)
        
        if generic_match:
            potential_query = generic_match.group(1).strip()
            # If multi-db, we trust the block if it has DB_ID: inside
            if engine == "multi-db" and "DB_ID:" in potential_query:
                 return ChatMessage(
                    role="assistant",
                    content="I have generated a query for you. Please review and confirm if you would like to execute it.",
                    query=potential_query,
                )

            sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "WITH", "CREATE", "ALTER", "DROP", "SHOW", "DESCRIBE"]
            if any(potential_query.upper().startswith(kw) for kw in sql_keywords):
                return ChatMessage(
                    role="assistant",
                    content="I have generated a query for you. Please review and confirm if you would like to execute it.",
                    query=potential_query,
                )
            redis_keywords = ["GET", "SET", "HGETALL", "HGET", "HSET", "KEYS", "SCAN", "DEL", "LPUSH", "RPUSH", "LRANGE"]
            if any(potential_query.upper().startswith(kw) for kw in redis_keywords):
                return ChatMessage(
                    role="assistant",
                    content="I have generated a command for you. Please review and confirm if you would like to execute it.",
                    query=potential_query,
                )
        
        sql_pattern = r"(?:^|\n)(SELECT\s+[\s\S]*?(?:;|$))"
        sql_match = re.search(sql_pattern, text, re.IGNORECASE)
        if sql_match and engine in ["postgresql", "mysql", "sqlite"]:
            query = sql_match.group(1).strip().rstrip(';') + ';'
            return ChatMessage(
                role="assistant",
                content="I have generated a query for you. Please review and confirm if you would like to execute it.",
                query=query,
            )
        
        # Check for ReAct pattern
        react_pattern = r"Action:\s*(.*?)\nAction Input:\s*(\{.*?\})"
        react_match = re.search(react_pattern, text, re.DOTALL)
        if react_match:
            tool_name = react_match.group(1).strip()
            tool_input = react_match.group(2).strip()
            try:
                import json
                tool_args = json.loads(tool_input)
                # Return a special message indicating a tool call
                # We reuse 'query' field for the tool call details or create a new way
                # For now, let's format it as a special internal command so the router can pick it up
                # Or better, we trust the router to inspect the content if we mark it?
                # Let's use the 'query' field to store the tool call JSON for now
                tool_call_payload = json.dumps({"tool": tool_name, "args": tool_args})
                return ChatMessage(
                    role="assistant",
                    content=text,  # Keep the thought process
                    query=f"__TOOL_CALL__:{tool_call_payload}"
                )
            except:
                pass

        return ChatMessage(role="assistant", content=text)