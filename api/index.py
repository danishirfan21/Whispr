"""Vercel serverless function handler for FastAPI."""
from mangum import Mangum
from app.main import app

# Mangum adapter converts FastAPI to ASGI handler for Vercel
handler = Mangum(app, lifespan="off")
