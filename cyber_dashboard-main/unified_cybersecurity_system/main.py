"""
main.py - Single Entrypoint for Unified Cyber Defense Platform

Launches the unified FastAPI backend server and serves the React Cyber Defense Command Center.
"""

import sys
import uvicorn
from pathlib import Path

# Ensure root is in python path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    print("=" * 70)
    print(" STARTING AI CYBER DEFENSE COMMAND CENTER")
    print("=" * 70)
    print(" Server URL: http://localhost:8000")
    print(" REST API Docs: http://localhost:8000/docs")
    print(" Press Ctrl+C to stop.")
    print("=" * 70)
    
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=False)
