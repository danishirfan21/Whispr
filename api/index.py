"""Vercel serverless function handler for FastAPI."""
import sys
from pathlib import Path

# Add parent directory to path so we can import from 'app' package
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

# Vercel's Python runtime expects 'app' variable
__all__ = ['app']
