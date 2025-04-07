#!/bin/bash
cd "$(dirname "$0")/backend"

# Activate virtual env
source venv/bin/activate

# Start FastAPI server (runs forever)
uvicorn main:app --host 0.0.0.0 --port 8000
