"""Health check endpoints"""
from fastapi import APIRouter
from datetime import datetime
from config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.app_version,
        "environment": settings.app_env
    }


@router.get("/readiness")
async def readiness_check():
    """Readiness probe for Kubernetes/ECS"""
    # Check if all required services are available
    checks = {
        "api_keys": False,
        "database": True,  # SQLite is always ready
        "qdrant": False
    }

    # Check API keys
    try:
        settings.validate_api_keys()
        checks["api_keys"] = True
    except:
        pass

    # Check Qdrant connection
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url=settings.qdrant_url)
        client.get_collections()
        checks["qdrant"] = True
    except:
        pass

    all_ready = all(checks.values())

    return {
        "ready": all_ready,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/liveness")
async def liveness_check():
    """Liveness probe - simple check that the service is running"""
    return {"alive": True}