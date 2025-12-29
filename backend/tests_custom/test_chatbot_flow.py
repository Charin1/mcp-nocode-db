import requests
import sys
import json

BASE_URL = "http://localhost:8000"
EMAIL = "admin@example.com"
PASSWORD = "password"

def test_chatbot_flow():
    print(f"--- Starting Chatbot Flow Test ---")
    
    # 1. Login
    print(f"\n1. Logging in as {EMAIL}...")
    try:
        auth_response = requests.post(
            f"{BASE_URL}/auth/token",
            data={"username": EMAIL, "password": PASSWORD},
            timeout=5
        )
        auth_response.raise_for_status()
        tokens = auth_response.json()
        access_token = tokens["access_token"]
        print(f"✅ Login successful. Token obtained.")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # 2. Get Config (to get DB ID)
    print(f"\n2. Fetching App Config...")
    try:
        config_response = requests.get(f"{BASE_URL}/api/config", headers=headers, timeout=5)
        config_response.raise_for_status()
        config = config_response.json()
        databases = config.get("databases", [])
        if not databases:
            print("❌ No databases found in config.")
            return
        
        db_id = databases[0]["id"]
        print(f"✅ Config fetched. Using Connection: {db_id}")
    except Exception as e:
        print(f"❌ Config fetch failed: {e}")
        return

    # 3. Send Chatbot Message
    print(f"\n3. Sending Chatbot Message to DB '{db_id}'...")
    payload = {
        "db_id": db_id,
        "model_provider": "groq", # Testing with Groq
        "messages": [
            {"role": "user", "content": "Show me all tables"}
        ]
    }
    
    try:
        # Using a shorter timeout to detect hangs faster than 3 minutes
        chat_response = requests.post(
            f"{BASE_URL}/api/chatbot/message",
            headers=headers,
            json=payload,
            timeout=30 
        )
        print(f"Status Code: {chat_response.status_code}")
        if chat_response.status_code == 200:
            print(f"✅ Response: {json.dumps(chat_response.json(), indent=2)}")
        else:
            print(f"❌ Request failed: {chat_response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out! The backend is hanging.")
    except Exception as e:
        print(f"❌ Request error: {e}")

if __name__ == "__main__":
    test_chatbot_flow()
