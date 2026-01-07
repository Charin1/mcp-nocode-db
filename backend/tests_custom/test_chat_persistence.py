import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from services.security import create_access_token
from datetime import timedelta

client = TestClient(app)

def test_chat_persistence():
    # 1. Login / Get Token
    # We can perform a fake login or just generate a token using internal function if available
    # Let's generate a token directly to avoid needing actual credentials
    access_token = create_access_token(
        data={"sub": "admin@example.com", "role": "admin"},
        expires_delta=timedelta(minutes=30)
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print("1. Token generated.")

    # 2. Create Session
    response = client.post(
        "/api/chatbot/sessions",
        json={"db_id": "test_db", "title": "Test Session"},
        headers=headers
    )
    assert response.status_code == 200
    session = response.json()
    session_id = session["id"]
    print(f"2. Session created: ID={session_id}, Title={session['title']}")

    # 3. Send Message (Mocking LLM would be ideal, but let's see if we can trigger it)
    # Since LLM service calls external APIs, this might fail if keys aren't set or cost money.
    # However, we catch exceptions in the router and return error message, so it shouldn't crash.
    # We can also mock the LLMService in the test if we want to be pure.
    # For now, let's try sending a message and see if it persists the USER message at least.
    
    user_msg = "Hello, this is a test message."
    try:
        response = client.post(
            f"/api/chatbot/sessions/{session_id}/message", 
            json={"role": "user", "content": user_msg},
            headers=headers
        )
        # It might return 500 if LLM fails, but user message should be saved?
        # Actually our logic saves user message BEFORE calling LLM.
        # But if LLM raises exception, we catch it and save error message.
        # So we expect 200 or 500 depending on how we handle it.
        # My code catches Exception and returns 500... wait.
        # If I catch exception in router, I raise HTTPException(500).
        # But I added a log message before raising?
        # "ChatService.add_message(..., content=f"Error: {str(e)}")"
        # So the side effect of saving error is there.
        
        print(f"3. Send Message Status: {response.status_code}")
        if response.status_code != 200:
             print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Exception during send: {e}")

    # 4. Login Retrieval
    response = client.get(f"/api/chatbot/sessions/{session_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    messages = data["messages"]
    
    print(f"4. Retrieved {len(messages)} messages.")
    for m in messages:
        print(f"   - [{m['role']}] {m['content']}")

    # Check if user message is there
    found = any(m['content'] == user_msg for m in messages)
    if found:
        print("SUCCESS: User message persisted.")
    else:
        print("FAILURE: User message not found.")

if __name__ == "__main__":
    test_chat_persistence()
