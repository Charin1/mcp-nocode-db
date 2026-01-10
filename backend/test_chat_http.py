import asyncio
import httpx
import os

BASE_URL = "http://localhost:8000"

async def test_chat_flow():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Login
        print("Logging in...")
        try:
            response = await client.post("/auth/token", data={
                "username": "admin@example.com",
                "password": "password"
            })
            if response.status_code != 200:
                print(f"Login failed: {response.text}")
                return
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("Login successful.")
        except Exception as e:
            print(f"Login request failed: {e}")
            return

        # 2. Create Project
        print("Creating Project...")
        project_data = {"name": "Test Project HTTP"}
        response = await client.post("/api/chatbot/projects", json=project_data, headers=headers)
        if response.status_code != 200:
            print(f"Create Project failed: {response.text}")
            return
        project = response.json()
        project_id = project["id"]
        print(f"Project created: {project_id}")

        # 3. Create Session (Start Conversation)
        print("Creating Session...")
        # Check backend/routers/chatbot.py for signature
        # @router.post("/projects/{project_id}/sessions", response_model=ChatSession)
        # async def create_function_session(project_id: int, request: CreateSessionRequest...)
        
        session_data = {
            "title": "New Conversation",
            "db_id": "sqlite",
            "project_id": project_id
        }
        response = await client.post("/api/chatbot/sessions", json=session_data, headers=headers)
        if response.status_code != 200:
            print(f"Create Session failed: {response.text}")
            return
        session = response.json()
        print(f"Session created: {session['id']}")
        print("Chat Flow Success!")

if __name__ == "__main__":
    asyncio.run(test_chat_flow())
