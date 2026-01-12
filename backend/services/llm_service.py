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
        elif engine == "mongodb":
            return f"""
                Your task is to convert a natural language query into a valid MongoDB query object for use in `db.collection.find()`.
                ### Instructions
                1.  Your output MUST be a single, valid JSON object.
                2.  This JSON object should represent the `filter` part of a `find` operation.
                3.  Use appropriate MongoDB query operators (e.g., `$gt`, `$lt`, `$in`, `$regex`).
                4.  For date-based queries, assume the dates in the database are stored in ISODate format. Use the format `{{"$gte": {{"$date": "YYYY-MM-DDTHH:mm:ssZ"}}}}`.
                5.  Analyze the user's query and the database schema (collections and fields) carefully.
                ### Database Schema (Collections and sample fields)
                {schema}
                ### Natural Language Query
                "{nl_query}"
                ### Your Output (JSON filter object only)
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
            query_language = "SQL query"
            query_block_tag = "sql"
        elif engine == "redis":
            query_language = "Redis command"
            query_block_tag = "redis"
        else:
            query_language = f"{engine} query"
            query_block_tag = "text"

        return f"""
            You are a helpful and friendly database assistant chatbot.
            Your goal is to help the user explore a database by answering their questions.
            You can either have a conversation or, if the user asks for specific data,
            you can generate a {query_language} for a {engine} database.

            ### Instructions
            1.  If the user is asking a question that requires data, generate a **read-only query or command**.
            2.  When you generate a query, **ONLY return the query inside a ```{query_block_tag} ... ``` block.** Do not include any other text in your response.
            3.  If the user is just chatting or asking a general question, respond in a friendly, conversational manner.
            4.  Use the provided conversation history for context.

            {tools_instruction}
            ### Database Schema
            {schema}
            ### Conversation History
            {history}
            ### Your Response
            """

    def _build_chat_system_prompt(self, schema: str, engine: str, tools: List[Dict[str, Any]] = None) -> str:
        if engine in ["postgresql", "mysql", "sqlite"]:
            query_language = "SQL query"
            query_block_tag = "sql"
        elif engine == "redis":
            query_language = "Redis command"
            query_block_tag = "redis"
        else:
            query_language = f"{engine} query"
            query_block_tag = "text"

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

        return f"""
            You are a helpful and friendly database assistant chatbot.
            Your goal is to help the user explore a database by answering their questions.
            You can either have a conversation or, if the user asks for specific data,
            you can generate a {query_language} for a {engine} database.

            ### Instructions
            1.  If the user is asking a question that requires data, generate a **read-only query or command**.
            2.  When you generate a query, **ONLY return the query inside a ```{query_block_tag} ... ``` block.** Do not include any other text in your response.
            3.  If the user is just chatting or asking a general question, respond in a friendly, conversational manner.
            4.  Use the provided conversation history for context.

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
            try:
                json.loads(text)
                return GeneratedQuery(raw_query=text, query_type="mongo_json")
            except json.JSONDecodeError:
                return GeneratedQuery(
                    raw_query=text,
                    error="LLM did not return a valid JSON object for the MongoDB query.",
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
        else:
            query_block_tag = "text"

        pattern = rf"```{query_block_tag}\s*([\s\S]*?)```"
        match = re.search(pattern, text, re.IGNORECASE)
        
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