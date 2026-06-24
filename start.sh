#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Clear screen and show a banner
clear
echo "===================================================="
echo "      🚀 Starting MCP No-Code DB Tool...             "
echo "===================================================="

# Keep track of background process PIDs to kill them cleanly
BACKEND_PID=""
FRONTEND_PID=""

# Cleanup function to run when the script exits or receives SIGINT/SIGTERM
cleanup() {
    echo ""
    echo "Stopping servers..."
    if [ -n "$BACKEND_PID" ]; then
        echo "Shutting down FastAPI backend (PID: $BACKEND_PID)..."
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        echo "Shutting down React frontend (PID: $FRONTEND_PID)..."
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    echo "Bye!"
    exit 0
}

# Trap INT and TERM signals to trigger cleanup
trap cleanup INT TERM EXIT

# 1. Start Backend
echo "📡 Starting Backend FastAPI server..."
cd backend

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -d "env" ]; then
    echo "Activating virtual environment (env)..."
    source env/bin/activate
else
    echo "⚠️ Warning: No python virtual environment found in backend/.venv or backend/env"
fi

# Run uvicorn in the background
uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 2. Start Frontend
echo "💻 Starting Frontend React app..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "⚠️ node_modules not found. Installing frontend dependencies first..."
    npm install
fi

# Run Vite in background
npm run dev &
FRONTEND_PID=$!
cd ..

echo "===================================================="
echo "✅ Both servers are starting up!"
echo "Backend API:     http://localhost:8000"
echo "Backend Docs:    http://localhost:8000/docs"
echo "Frontend:        http://localhost:5173"
echo "Press Ctrl+C to stop both servers."
echo "===================================================="

# Wait for background jobs to complete (runs indefinitely until interrupted)
wait
