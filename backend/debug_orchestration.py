
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Ensure we can import services
sys.path.append(os.getcwd())

from services.llm_service import LLMService
from models.query import ChatMessage

# Mock Schema corresponding to the user's situation
SCHEMA_CONTEXT = """
Table `customers`: customer_id (int, PK), first_name (varchar), last_name (varchar), email (varchar), country (varchar)
Table `orders`: order_id (int, PK), customer_id (int, FK -> customers.customer_id), total_amount (decimal)
"""

# Mock Tool that SHOULD be selected for "bcbs" (Blue Cross Blue Shield)
MOCK_TOOLS = [
    {
        "name": "healthcare_api",
        "description": "Fetch patient counts, insurance data (BCBS, Aetna, etc), and medical records.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "insurance_provider": {"type": "string"},
                "metric": {"type": "string"}
            }
        }
    }
]

async def test_orchestration():
    print("--- Testing Orchestration Logic ---")
    llm = LLMService()
    
    # We need a provider. Assuming Gemini is configured or OpenAI.
    # We will check env vars.
    provider = "gemini" if os.getenv("GOOGLE_API_KEY") else "chatgpt" if os.getenv("OPENAI_API_KEY") else "groq"
    
    print(f"Using Provider: {provider}")
    
    messages = [
        ChatMessage(role="user", content="tell me patient count of bcbs")
    ]
    
    try:
        response = await llm.generate_response_from_messages(
            db_id="mysql_local",
            provider=provider,
            messages=messages,
            schema=SCHEMA_CONTEXT,
            engine="mysql",
            tools=MOCK_TOOLS
        )
        
        print("\n--- LLM Response ---")
        print(f"Content: {response.content}")
        print(f"Query/Tool: {response.query}")
        
        if response.query and "__TOOL_CALL__" in response.query:
             print("\nSUCCESS: LLM selected a tool.")
        else:
             print("\nFAILURE: LLM generated SQL or text instead of tool.")
             
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_orchestration())
