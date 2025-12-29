import requests
import json

BASE_URL = "http://localhost:8000"
EMAIL = "admin@example.com"
PASSWORD = "password"

def test_visualization():
    print(f"--- Starting Visualization Test ---")
    
    # 1. Login
    print(f"Logging in...")
    auth_response = requests.post(
        f"{BASE_URL}/auth/token",
        data={"username": EMAIL, "password": PASSWORD}
    )
    auth_response.raise_for_status()
    access_token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print("✅ Logged in.")

    # 2. Call Visualize Endpoint
    print(f"Calling /visualize...")
    payload = {
        "columns": ["product_name", "sales"],
        "rows": [
            {"product_name": "A", "sales": 100},
            {"product_name": "B", "sales": 150},
            {"product_name": "C", "sales": 80}
        ],
        "user_request": "Show me a bar chart" # Optional intent
    }
    
    resp = requests.post(f"{BASE_URL}/api/chatbot/visualize", headers=headers, json=payload, timeout=10)
    
    if resp.status_code == 200:
        print(f"✅ Visualization Config Generated:")
        print(json.dumps(resp.json(), indent=2))
    else:
        print(f"❌ Visualization Failed: {resp.text}")

if __name__ == "__main__":
    test_visualization()
