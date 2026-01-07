import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from services.security import create_access_token
from datetime import timedelta

client = TestClient(app)

def test_chat_management():
    # 1. Login / Get Token
    access_token = create_access_token(
        data={"sub": "admin@example.com", "role": "admin"},
        expires_delta=timedelta(minutes=30)
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    print("1. Token generated.")

    # 2. Create Two Sessions
    res1 = client.post(
        "/api/chatbot/sessions",
        json={"db_id": "test_db", "title": "Alpha Session"},
        headers=headers
    )
    assert res1.status_code == 200
    id1 = res1.json()["id"]

    res2 = client.post(
        "/api/chatbot/sessions",
        json={"db_id": "test_db", "title": "Beta Session"},
        headers=headers
    )
    assert res2.status_code == 200
    id2 = res2.json()["id"]
    
    print(f"2. Created sessions: {id1} (Alpha), {id2} (Beta)")

    # 3. Search Sessions
    # Search for "Alpha"
    res_search = client.get("/api/chatbot/sessions?q=alpha", headers=headers)
    assert res_search.status_code == 200
    results = res_search.json()
    print(f"3. Search for 'alpha' returned {len(results)} results.")
    assert len(results) >= 1
    assert any(s["id"] == id1 for s in results)
    assert not any(s["id"] == id2 for s in results) # Beta shouldn't be valid for "alpha"
    print("   Search validation passed.")

    # 4. Rename Session 2
    res_rename = client.put(
        f"/api/chatbot/sessions/{id2}",
        json={"title": "Gamma Session"},
        headers=headers
    )
    assert res_rename.status_code == 200
    print("4. Rename executed.")
    
    # Verify Rename
    res_get = client.get(f"/api/chatbot/sessions/{id2}", headers=headers)
    assert res_get.json()["session"]["title"] == "Gamma Session"
    print("   Rename verification passed.")

    # 5. Delete Session 1
    res_delete = client.delete(f"/api/chatbot/sessions/{id1}", headers=headers)
    assert res_delete.status_code == 200
    print("5. Delete executed.")

    # Verify Delete
    res_get_deleted = client.get(f"/api/chatbot/sessions/{id1}", headers=headers)
    assert res_get_deleted.status_code == 404
    print("   Delete verification passed.")

if __name__ == "__main__":
    test_chat_management()
