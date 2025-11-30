"""Chat-related Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class Source(BaseModel):
    """Citation source from RAG"""
    title: str
    url: Optional[str] = None
    youtube_url: Optional[str] = None
    timestamp: Optional[str] = None


class MessageCreate(BaseModel):
    """Request to create a new message"""
    content: str = Field(..., min_length=1, max_length=10000)
    chat_id: Optional[int] = None  # If None, create new chat
    stream: bool = False  # Whether to stream the response


class MessageResponse(BaseModel):
    """Response for a message"""
    id: int
    role: str
    content: str
    agent_used: Optional[str] = None
    routing_reason: Optional[str] = None
    sources: Optional[List[Source]] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    response_time_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatCreate(BaseModel):
    """Request to create a new chat"""
    title: Optional[str] = None
    first_message: Optional[str] = None


class ChatResponse(BaseModel):
    """Response for a chat session"""
    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    total_tokens_used: int = 0
    total_cost: float = 0.0
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ChatListResponse(BaseModel):
    """Response for listing chats"""
    chats: List[ChatResponse]
    total: int
    page: int
    per_page: int


class CompletionRequest(BaseModel):
    """Request for chat completion"""
    messages: List[Dict[str, str]]  # OpenAI format messages
    model: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, le=4000)
    stream: bool = False
    use_rag: bool = True
    namespace: Optional[str] = None  # Force specific agent namespace