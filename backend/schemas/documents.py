"""Document schemas for knowledge base management"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DocumentBase(BaseModel):
    """Base document fields"""
    namespace: str = Field(..., description="Agent namespace for the document")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content/text")
    source_url: Optional[str] = Field(None, description="Original source URL")
    youtube_url: Optional[str] = Field(None, description="YouTube video URL if this is a transcript")


class DocumentCreate(DocumentBase):
    """Schema for creating a new document"""
    pass


class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    title: Optional[str] = None
    content: Optional[str] = None
    source_url: Optional[str] = None
    youtube_url: Optional[str] = None


class DocumentUpload(BaseModel):
    """Schema for uploading a PDF document"""
    namespace: str = Field(default="general", description="Agent namespace")
    title: Optional[str] = Field(None, description="Document title (defaults to filename)")
    youtube_url: Optional[str] = Field(None, description="YouTube video URL if this is a transcript")


class DocumentResponse(BaseModel):
    """Schema for document responses"""
    id: int
    namespace: str
    title: str
    content: str
    source_url: Optional[str]
    vector_id: Optional[str]
    embedding_model: Optional[str]
    author: Optional[str]
    published_date: Optional[datetime]
    tags: Optional[List[str]]
    metadata_json: Optional[Dict[str, Any]]
    uploaded_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    retrieval_count: int
    avg_relevance_score: Optional[float]

    # Computed properties
    @property
    def youtube_url(self) -> Optional[str]:
        """Get YouTube URL from metadata"""
        if self.metadata_json:
            return self.metadata_json.get("youtube_url")
        return None

    @property
    def is_transcript(self) -> bool:
        """Check if this document is a transcript"""
        if self.metadata_json:
            return self.metadata_json.get("is_transcript", False)
        return False

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class NamespaceResponse(BaseModel):
    """Schema for namespace information"""
    name: str
    document_count: int


class DocumentSearchRequest(BaseModel):
    """Schema for searching documents"""
    query: str = Field(..., description="Search query")
    namespace: Optional[str] = Field(None, description="Limit search to specific namespace")
    limit: int = Field(default=10, le=50, description="Maximum number of results")
    min_score: float = Field(default=0.5, le=1.0, description="Minimum relevance score")


class DocumentSearchResult(BaseModel):
    """Schema for search results"""
    document: DocumentResponse
    score: float
    snippet: str  # Relevant text excerpt