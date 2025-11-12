"""Document model for knowledge base"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class Document(Base):
    """Document model for storing knowledge base entries"""
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    namespace = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    filename = Column(String)
    file_type = Column(String)
    file_size = Column(Float)
    chunk_count = Column(Float, default=0)
    youtube_url = Column(String)
    youtube_metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign key to users table
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationship (optional, for easier navigation)
    creator = relationship("User", back_populates="documents")