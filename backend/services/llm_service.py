import os
import google.generativeai as genai
from openai import OpenAI
import yaml
import json

from models.query import GeneratedQuery


class LLMService:
    def __init__(self):
        with open("config/config.yaml", "r") as f:
            self.config = yaml.safe_load(f)["llm"]

        # Configure Google Gemini
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            genai.configure(api_key=google_api_key)

        # Configure OpenAI
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate_query(
        self, provider: str, natural_language_query: str, schema: str, engine: str
    ) -> GeneratedQuery:
        prompt = self._build_prompt(natural_language_query, schema, engine)

        if provider.lower() == "gemini":
            return await self._generate_with_gemini(prompt, engine)
        elif provider.lower() == "chatgpt":
            return await self._generate_with_chatgpt(prompt, engine)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def _build_prompt(self, nl_query: str, schema: str, engine: str) -> str:
        # This is a critical part. The quality of the prompt determines the quality of the output.
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
        # Add prompts for Redis, Elasticsearch, etc.
        else:
            return f"""
                Given the database schema:
                {schema}

                Convert the following natural language query into a {engine} query:
                "{nl_query}"
                """

    async def _generate_with_gemini(self, prompt: str, engine: str) -> GeneratedQuery:
        try:
            model_name = self.config["providers"]["gemini"]["model"]
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async(prompt)

            # --- ROBUST RESPONSE HANDLING ---
            # The original `response.text` is a shortcut that fails if the
            # response has multiple parts or candidates. This is the safe way.
            raw_text = ""
            if response.candidates and response.candidates[0].content.parts:
                raw_text = response.candidates[0].content.parts[0].text
            else:
                # Handle cases where the response might be blocked or empty
                return GeneratedQuery(
                    raw_query="",
                    error="Error from Gemini API: Received an empty or blocked response.",
                    query_type=engine,
                )

            # Clean the extracted text
            cleaned_text = (
                raw_text.strip()
                .replace("```sql", "")
                .replace("```json", "")
                .replace("```", "")
            )
            return self._parse_llm_response(cleaned_text, engine)

        except Exception as e:
            # Catch other potential exceptions during the API call
            return GeneratedQuery(
                raw_query="", error=f"Error from Gemini API: {e}", query_type=engine
            )

    async def _generate_with_chatgpt(self, prompt: str, engine: str) -> GeneratedQuery:
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
            raw_text = response.choices.message.content.strip()
            return self._parse_llm_response(raw_text, engine)
        except Exception as e:
            return GeneratedQuery(
                raw_query="", error=f"Error from OpenAI API: {e}", query_type=engine
            )

    def _parse_llm_response(self, text: str, engine: str) -> GeneratedQuery:
        if engine in ["postgresql", "mysql", "sqlite"]:
            if "----JSON----" in text:
                # Split the text into two parts at the separator
                parts = text.split("----JSON----", 1)

                # Check if we got two parts as expected
                if len(parts) == 2:
                    sql_part = parts[0].strip()  # Get the first element and strip it
                    json_part = parts[1].strip()  # Get the second element and strip it

                    try:
                        # The JSON part might be empty if there are no parameters
                        params = json.loads(json_part) if json_part else None
                        return GeneratedQuery(
                            raw_query=sql_part, params=params, query_type="sql"
                        )
                    except json.JSONDecodeError:
                        # The model generated malformed JSON
                        return GeneratedQuery(
                            raw_query=sql_part,  # Still return the SQL part
                            error="LLM returned invalid JSON for parameters.",
                            query_type="sql",
                        )
                else:
                    # This case is unlikely but good to handle
                    return GeneratedQuery(
                        raw_query=text,
                        error="LLM output contained separator but could not be split correctly.",
                        query_type="sql",
                    )
            else:
                # Fallback if the model didn't follow instructions at all
                return GeneratedQuery(
                    raw_query=text,
                    error="LLM did not return the expected SQL----JSON---- format.",
                    query_type="sql",
                )

        elif engine == "mongodb":
            try:
                # The entire response should be the JSON object
                # We just validate it here. The raw text is the query itself.
                json.loads(text)
                return GeneratedQuery(raw_query=text, query_type="mongo_json")
            except json.JSONDecodeError:
                return GeneratedQuery(
                    raw_query=text,
                    error="LLM did not return a valid JSON object for the MongoDB query.",
                    query_type="mongo_json",
                )

        else:
            # For other engines, return the text as is
            return GeneratedQuery(raw_query=text, query_type=engine)
