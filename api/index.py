"""
Entrypoint serverless Vercel untuk SAVEURMONEY FastAPI.
"""
import sys
from pathlib import Path

direktoriRoot = Path(__file__).resolve().parent.parent
if str(direktoriRoot) not in sys.path:
    sys.path.insert(0, str(direktoriRoot))

from backend.main import app
