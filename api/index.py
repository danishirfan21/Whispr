"""Vercel serverless function handler for FastAPI."""
from app.main import app

# Vercel's Python runtime expects 'app' variable
__all__ = ['app']
