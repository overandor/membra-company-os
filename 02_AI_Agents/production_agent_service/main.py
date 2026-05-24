#!/usr/bin/env python3
"""
Production Agent Service — Entry Point
Run: python main.py
Or: uvicorn main:app --host 0.0.0.0 --port 8000
"""

import os
from api import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)
