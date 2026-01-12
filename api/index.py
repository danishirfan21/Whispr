"""Vercel serverless function handler."""
from app.main import app

# Vercel expects the ASGI app to be named 'app' or available via this module
__all__ = ['app']
