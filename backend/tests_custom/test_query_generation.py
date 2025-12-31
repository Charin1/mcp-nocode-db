import requests
import json

BASE_URL = "http://localhost:8000"
EMAIL = "admin@example.com"
PASSWORD = "password"

def test_query_generation():
    print(f"--- Starting Query Generation Test ---")
    
    # 1. Login
    print(f"Logging in...")
    try:
        auth_response = requests.post(
            f"{BASE_URL}/auth/token",
            data={"username": EMAIL, "password": PASSWORD},
            timeout=5
        )
        auth_response.raise_for_status()
        access_token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print("✅ Logged in.")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        return

    # 2. Call Generate Query Endpoint
    print(f"Calling /api/query/generate...")
    payload = {
        "db_id": "postgres_docker",
        "model_provider": "groq",
        "natural_language_query": "show me top 10 customers by total order amount"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/api/query/generate", headers=headers, json=payload, timeout=30)
        
        if resp.status_code == 200:
            print(f"✅ Query Generated:")
            print(json.dumps(resp.json(), indent=2))
        else:
            print(f"❌ Query Generation Failed: {resp.text}")
    except Exception as e:
        print(f"❌ Request Error: {e}")

if __name__ == "__main__":
    test_query_generation()
