"""
Backward-compatible entrypoint.

Use:
    uvicorn api:app

This now proxies to the modular FastAPI app in app.main.
"""

from app.main import app

