"""Chat and message models for storing conversation history"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """User model for authentication and tracking"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="creator", cascade="all, delete-orphan")


class Chat(Base):
    """Chat session model"""
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Token tracking
    total_tokens_used = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)

    # Metadata
    metadata_json = Column(JSON, nullable=True)  # Store additional chat metadata

    # Relationships
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    """Individual message in a chat"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Message content
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # Agent routing information
    agent_used = Column(String(100), nullable=True)  # Which specialist agent was used
    routing_reason = Column(Text, nullable=True)  # Why this agent was chosen

    # RAG information
    sources_json = Column(JSON, nullable=True)  # Retrieved sources with citations
    retrieval_score = Column(Float, nullable=True)  # Relevance score from RAG

    # Token tracking
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(Float, default=0.0)

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    response_time_ms = Column(Integer, nullable=True)  # Response generation time

    # Metadata
    metadata_json = Column(JSON, nullable=True)  # Additional message metadata

    # Relationships
    chat = relationship("Chat", back_populates="messages")
    user = relationship("User", back_populates="messages")


