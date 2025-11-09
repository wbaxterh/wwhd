#!/usr/bin/env python3
"""
W.W.H.D. Backend API - Main Application
Multi-agent system with LangChain/LangGraph orchestration
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from datetime import datetime
import logging

# Import configuration
from config import settings

# Import routers
from api import chat_router, health_router, auth_router

# Import database
from models import init_db

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting W.W.H.D. API...")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # Validate configuration
    try:
        settings.validate_api_keys()
        logger.info("API keys validated")
    except ValueError as e:
        logger.warning(f"API key validation warning: {e}")

    yield

    # Shutdown
    logger.info("Shutting down W.W.H.D. API...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="What Would Herman Do? - Multi-agent Shaolin/TCM companion with RAG",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug_mode else None,
    redoc_url="/redoc" if settings.debug_mode else None
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    health_router,
    tags=["health"]
)

app.include_router(
    auth_router,
    prefix=f"{settings.api_v1_prefix}/auth",
    tags=["authentication"]
)

app.include_router(
    chat_router,
    prefix=f"{settings.api_v1_prefix}/chat",
    tags=["chat"]
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "W.W.H.D. API is running",
        "version": settings.app_version,
        "environment": settings.app_env,
        "docs": "/docs" if settings.debug_mode else "Disabled in production"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancer"""
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "region": settings.aws_default_region,
        "deployment_time": datetime.utcnow().isoformat() + "Z",
        "model_chat": settings.model_chat,
        "model_embed": settings.model_embed
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        log_level=settings.log_level.lower(),
        reload=settings.debug_mode
    )