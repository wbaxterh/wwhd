#!/usr/bin/env python3
"""
W.W.H.D. Backend API - Minimal Health Check
This is a placeholder until we build the full LangGraph application
"""

from fastapi import FastAPI
import uvicorn
import os
from datetime import datetime

app = FastAPI(
    title="W.W.H.D. API",
    description="What Would Herman Do? - Multi-agent Shaolin/TCM companion",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {
        "message": "W.W.H.D. API is running",
        "version": "0.1.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": os.getenv("APP_ENV", "unknown"),
        "region": os.getenv("AWS_DEFAULT_REGION", "unknown"),
        "deployment_time": datetime.utcnow().isoformat() + "Z"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )