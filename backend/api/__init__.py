"""API routers for the W.W.H.D. backend"""
from .chat import router as chat_router
from .health import router as health_router
from .auth import router as auth_router

__all__ = ["chat_router", "health_router", "auth_router"]