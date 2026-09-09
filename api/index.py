import sys
from pathlib import Path

# Add backend/src to path for Vercel Serverless Function execution
backend_src = str(Path(__file__).resolve().parents[1] / "backend" / "src")
if backend_src not in sys.path:
    sys.path.insert(0, backend_src)

from app.main import app
