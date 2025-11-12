"""Knowledge base document management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from typing import List, Optional
import uuid
from datetime import datetime

from models import get_db, Document, User
from schemas.documents import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
    NamespaceResponse,
    DocumentUpload
)
from api.auth import get_current_user
from services.qdrant_service import QdrantService
from services.pdf_processor import process_pdf
from config import settings

router = APIRouter()

@router.get("/namespaces", response_model=List[NamespaceResponse])
async def list_namespaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all available namespaces with document counts"""
    result = await db.execute(
        select(
            Document.namespace,
            func.count(Document.id).label('document_count')
        ).group_by(Document.namespace)
    )

    namespaces = []
    for row in result:
        namespaces.append(NamespaceResponse(
            name=row.namespace,
            document_count=row.document_count
        ))

    return namespaces

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    namespace: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List documents, optionally filtered by namespace"""
    query = select(Document)

    if namespace:
        query = query.where(Document.namespace == namespace)

    query = query.offset(skip).limit(limit).order_by(Document.created_at.desc())

    result = await db.execute(query)
    documents = result.scalars().all()

    return [DocumentResponse.from_orm(doc) for doc in documents]

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific document by ID"""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return DocumentResponse.from_orm(document)

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    namespace: str = "general",
    title: Optional[str] = None,
    youtube_url: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload and process a PDF document"""

    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )

    try:
        # Process PDF
        content = await file.read()
        extracted_text = process_pdf(content)

        if not extracted_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract text from PDF"
            )

        # Create document record
        document_title = title or file.filename
        vector_id = str(uuid.uuid4())

        # Prepare metadata
        metadata = {}
        if youtube_url:
            metadata["youtube_url"] = youtube_url
            metadata["is_transcript"] = True

        new_document = Document(
            namespace=namespace,
            title=document_title,
            content=extracted_text,
            vector_id=vector_id,
            embedding_model=settings.model_embed,
            uploaded_by=current_user.id,
            metadata_json=metadata if metadata else None
        )

        db.add(new_document)
        await db.flush()  # Get the ID

        # Store in vector database
        qdrant_service = QdrantService()
        await qdrant_service.add_document(
            namespace=namespace,
            document_id=vector_id,
            content=extracted_text,
            metadata={
                "document_id": new_document.id,
                "title": document_title,
                "namespace": namespace,
                **metadata
            }
        )

        await db.commit()
        await db.refresh(new_document)

        return DocumentResponse.from_orm(new_document)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )

@router.post("/", response_model=DocumentResponse)
async def create_document(
    document_data: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a document directly with text content"""

    try:
        vector_id = str(uuid.uuid4())

        # Prepare metadata
        metadata = {}
        if document_data.youtube_url:
            metadata["youtube_url"] = document_data.youtube_url
            metadata["is_transcript"] = True

        new_document = Document(
            namespace=document_data.namespace,
            title=document_data.title,
            content=document_data.content,
            vector_id=vector_id,
            embedding_model=settings.model_embed,
            uploaded_by=current_user.id,
            metadata_json=metadata if metadata else None,
            source_url=document_data.source_url
        )

        db.add(new_document)
        await db.flush()

        # Store in vector database
        qdrant_service = QdrantService()
        await qdrant_service.add_document(
            namespace=document_data.namespace,
            document_id=vector_id,
            content=document_data.content,
            metadata={
                "document_id": new_document.id,
                "title": document_data.title,
                "namespace": document_data.namespace,
                **metadata
            }
        )

        await db.commit()
        await db.refresh(new_document)

        return DocumentResponse.from_orm(new_document)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}"
        )

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_data: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing document"""

    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    try:
        # Update document fields
        update_data = document_data.dict(exclude_unset=True)

        # Handle metadata updates
        if document_data.youtube_url is not None:
            current_metadata = document.metadata_json or {}
            if document_data.youtube_url:
                current_metadata["youtube_url"] = document_data.youtube_url
                current_metadata["is_transcript"] = True
            else:
                current_metadata.pop("youtube_url", None)
                current_metadata.pop("is_transcript", None)
            update_data["metadata_json"] = current_metadata

        for field, value in update_data.items():
            if hasattr(document, field):
                setattr(document, field, value)

        # If content changed, update vector database
        if document_data.content is not None and document.vector_id:
            qdrant_service = QdrantService()
            await qdrant_service.update_document(
                namespace=document.namespace,
                document_id=document.vector_id,
                content=document_data.content,
                metadata={
                    "document_id": document.id,
                    "title": document.title,
                    "namespace": document.namespace,
                    **(document.metadata_json or {})
                }
            )

        await db.commit()
        await db.refresh(document)

        return DocumentResponse.from_orm(document)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}"
        )

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document"""

    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    try:
        # Delete from vector database
        if document.vector_id:
            qdrant_service = QdrantService()
            await qdrant_service.delete_document(
                namespace=document.namespace,
                document_id=document.vector_id
            )

        # Delete from SQL database
        await db.execute(delete(Document).where(Document.id == document_id))
        await db.commit()

        return {"message": "Document deleted successfully"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )