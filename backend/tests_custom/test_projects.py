import sys
import os
# import pytest (removed)
from fastapi.testclient import TestClient

# Add generic backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from main import app
from services.chat_service import ChatService
from services.security import create_access_token, register_new_user

client = TestClient(app)

# Mock user for testing
test_username = "testuser_proj@example.com"
test_password = "password123"

# Register user (idempotent due to check inside register_new_user)
register_new_user(test_username, test_password)

# Generate token
token = create_access_token({"sub": test_username})
headers = {"Authorization": f"Bearer {token}"}

def test_project_workflow():
    # 1. Create a Project
    response = client.post(
        "/api/chatbot/projects",
        json={"name": "Test Project Alpha"},
        headers=headers
    )
    assert response.status_code == 200
    project_id = response.json()["id"]
    assert response.json()["name"] == "Test Project Alpha"

    # 2. List Projects
    response = client.get("/api/chatbot/projects", headers=headers)
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) >= 1
    assert any(p["id"] == project_id for p in projects)

    # 3. Create a Session in the Project
    response = client.post(
        "/api/chatbot/sessions",
        json={"db_id": "test_db", "title": "Chat In Project", "project_id": project_id},
        headers=headers
    )
    assert response.status_code == 200
    session_id_1 = response.json()["id"]
    assert response.json()["project_id"] == project_id

    # 4. Create a Session outside Project
    response = client.post(
        "/api/chatbot/sessions",
        json={"db_id": "test_db", "title": "Chat Outside Project"},
        headers=headers
    )
    assert response.status_code == 200
    session_id_2 = response.json()["id"]
    assert response.json()["project_id"] is None

    # 5. Move Session 2 into Project
    response = client.put(
        f"/api/chatbot/sessions/{session_id_2}",
        json={"project_id": project_id},
        headers=headers
    )
    assert response.status_code == 200

    # Verify Move
    response = client.get(f"/api/chatbot/sessions?q=Outside", headers=headers)
    assert response.status_code == 200
    sessions = response.json()
    target_session = next(s for s in sessions if s["id"] == session_id_2)
    assert target_session["project_id"] == project_id

    # 6. Delete Project
    response = client.delete(f"/api/chatbot/projects/{project_id}", headers=headers)
    assert response.status_code == 200

    # Verify Project Deleted
    response = client.get("/api/chatbot/projects", headers=headers)
    projects = response.json()
    assert not any(p["id"] == project_id for p in projects)

    # Verify Sessions Unlinked (or Deleted, depending on logic)
    # Our logic in delete_project was: UPDATE sessions SET project_id = NULL
    response = client.get(f"/api/chatbot/sessions/{session_id_1}", headers=headers)
    assert response.status_code == 200
    assert response.json()["session"]["project_id"] is None # Should be unlinked

    print("Project workflow test passed!")

if __name__ == "__main__":
    test_project_workflow()
