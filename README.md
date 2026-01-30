# MCP No-Code DB Tool

[![Status](https://img.shields.io/badge/status-beta-blue)](https://github.com/charin1/mcp-nocode-db)

⚠️ This project is currently in **beta**. While it is more stable than earlier development versions, it may still contain bugs and is **not yet production-ready**.

MCP No-Code DB is a modern, web-based database tool that allows users to connect to their database and interact with it using either natural language or raw queries. It leverages Large Language Models (LLMs) like Google's Gemini, OpenAI, and Groq to translate plain English questions into executable SQL queries, providing a powerful and intuitive interface for data exploration.

---

## 📸 How It Works: A Visual Walkthrough

### Step 1: Ask a Question in Natural Language
The workflow begins by asking a question about your data in plain English. The interface features a professional, AI-native design with real-time "thinking" animations and typewriter effects.

### Step 2: Review & Execute
The application uses the selected LLM to translate your question into a precise SQL query. You can review the query and execute it with a single click.

### Step 3: Interactive Chat
For a more conversational experience, the **Chatbot** allows continuous dialogue about your data. It understands context, remembers history, and can visualize results.

---

## ✨ Features

*   **Multi-Database Support:**
    *   Connect to **PostgreSQL**, **MySQL**, **MongoDB**, **Redis**, **SQLite**, **Elasticsearch**, and **BigQuery**.
    *   Flexible architecture allows connection to both local and remote databases (Docker containers, cloud services, or local instances).
*   **Reliable Backend:**
    *   **SQLAlchemy ORM:** Robust database interactions and migration support.
    *   **Background Workers:** Uses `arq` (Redis) for reliable task processing (optional).
    *   **Smart Retries:** `Tenacity` integration ensures resilience against API flakes.
*   **Modern UI/UX:**
    *   **AI-Native Feel:** "Thinking" animations, typewriter effects, and glassmorphism styling.
    *   **Visualization:** Auto-generate charts from your data.
*   **Secure by Default:** JWT-based authentication and Role-Based Access Control (RBAC).

---

## 🔌 MCP Integration

This project implements the **Model Context Protocol (MCP)**, allowing AI assistants (like Claude Desktop) to discover and interact with your database schema and data.

### Available Tools
*   `list_tables(db_id: str)`: Lists all tables in the specified database.
*   `get_schema(db_id: str)`: Returns the full schema for the database.
*   `execute_query(db_id: str, query: str)`: Executes a raw SQL query safely.

---

## 🚀 Getting Started

You can run the application locally or via Docker, connecting to any supported database.

### 1. Installation & Setup

**Clone the Repository**
```bash
git clone <your-repository-url>
cd mcp-nocode-db
```

**Backend Setup**

Navigate to the `backend` directory and set up your virtual environment.

**Example Scripts (Choose your OS):**

<details>
<summary><strong>macOS / Linux (Ubuntu)</strong></summary>

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
</details>

<details>
<summary><strong>Windows (PowerShell)</strong></summary>

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
</details>

<details>
<summary><strong>Windows (Command Prompt)</strong></summary>

```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```
</details>

**Configure Environment**
```bash
# All Platforms
cp .env.example .env
# Add your API keys (GOOGLE_API_KEY, OPENAI_API_KEY, etc.) inside .env
```

**Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

### 2. Configuration & Database Connection

The application is database-agnostic. You configure your connections in `backend/config/config.yaml`.

**To switch databases:**
1.  Open `backend/config/config.yaml`.
2.  Enable the database you want to use (uncomment the relevant section) or add your own connection details.
3.  The request payload determines which database ID to use, or you can set a default in your application logic.

**Example Configurations:**

*   **SQLite (Default)**: Zero-config, runs locally.
*   **PostgreSQL**:
    ```yaml
    postgres_docker:
      name: "Postgres (Docker)"
      engine: "postgresql"
      host: "localhost"
      port: 5432
      user: "postgres"
      password: "mlp123"
      dbname: "sampledb"
    ```
*   **MongoDB, Redis, MySQL, BigQuery**: Uncomment the examples in `config.yaml` to enable.

### 3. Running the Server

Start the backend server (ensure your target database is running if it's external):

```bash
# In backend directory
uvicorn main:app --reload
```

Or run everything with Docker (if you prefer containerized services for Postgres/Redis):
```bash
docker-compose up --build
```

---

### 4. Database Seeding
To populate your database with sample data (parity across PostgreSQL and MySQL):

```bash
# In backend directory, ensuring you are in your venv
source .venv/bin/activate
python seed_db.py --db mysql_local
# OR
python seed_db.py --db postgres_docker
# OR
python seed_db.py --db redis_local
```

---

## 💻 Tech Stack

*   **Backend:** Python 3.13+, FastAPI, SQLAlchemy (Async), Pydantic v2, Arq (Redis), Tenacity, HTTPX
*   **Database Drivers:** asyncpg (PostgreSQL), PyMySQL (MySQL), Motor/PyMongo (MongoDB), Redis, aiosqlite (SQLite), Elasticsearch, BigQuery
*   **Frontend:** React 18, Vite 5, TailwindCSS, Zustand, Recharts, AG Grid, Axios, React Router v6
*   **AI:** Google Gemini, OpenAI, Groq
*   **Protocol:** Model Context Protocol (MCP)
*   **Auth:** JWT (python-jose), bcrypt

---

## 🛠️ Roadmap

### ✅ Completed
*   **Core Multi-Database Support:** PostgreSQL, MySQL, MongoDB, Redis, SQLite.
*   **Robust Authentication:** Secure JWT-based auth with Role-Based Access Control (RBAC).
*   **Cross-Platform Compatibility:** Universal setup for Windows, macOS, and Linux.
*   **Advanced LLM Integration:** Support for Gemini, Groq.
*   **MCP Protocol Implementation:** Initial support for Model Context Protocol compliance.

### 🚀 Upcoming
*   [ ] **Production Deployment:** Docker Compose orchestration and cloud deployment guides.
*   [ ] **Plugin System:** Allow community extensions for new database types.
*   [ ] **Data Visualization Suite:** Extended library of auto-generated charts and dashboards.