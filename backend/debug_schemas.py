import requests

def debug_schemas():
    # 1. Login
    try:
        auth = requests.post("http://127.0.0.1:8000/auth/token", data={"username": "admin@example.com", "password": "password"}, timeout=5)
        auth.raise_for_status()
        token = auth.json()["access_token"]
        print(f"Token ok.")
    except Exception as e:
        print(f"Login failed: {e}")
        return

    # 2. Get Schemas
    try:
        res = requests.get("http://127.0.0.1:8000/api/schemas", headers={"Authorization": f"Bearer {token}"}, timeout=30)
        print(f"Status: {res.status_code}")
        print(res.text)
    except Exception as e:
        print(f"Get schemas failed: {e}")

if __name__ == "__main__":
    debug_schemas()
