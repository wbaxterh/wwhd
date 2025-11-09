"""Qdrant vector database retriever"""
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
    SearchParams, SearchRequest
)
from uuid import uuid4
from config import settings
from .embeddings import EmbeddingGenerator
import logging

logger = logging.getLogger(__name__)


class QdrantRetriever:
    """Retriever for Qdrant vector database with namespace support"""

    def __init__(self, namespace: str):
        """
        Initialize retriever for a specific namespace

        Args:
            namespace: Collection name in Qdrant (e.g., 'tcm', 'relationships', 'money', 'feng_shui')
        """
        self.namespace = namespace
        self.collection_name = f"wwhd_{namespace}"
        self.client = self._initialize_client()
        self.embeddings = EmbeddingGenerator()
        self._ensure_collection()

    def _initialize_client(self) -> QdrantClient:
        """Initialize Qdrant client"""
        try:
            client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
                timeout=30
            )
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise

    def _ensure_collection(self):
        """Ensure collection exists with proper configuration"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                # Create collection with vector configuration
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embeddings.get_embedding_dimension(),
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Using existing Qdrant collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Error ensuring collection {self.collection_name}: {e}")
            raise

    async def add_document(
        self,
        document_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Add a document to the vector store

        Args:
            document_id: Unique identifier for the document
            content: Document content to embed and store
            metadata: Additional metadata (title, url, author, etc.)

        Returns:
            Success status
        """
        try:
            # Generate embedding
            embedding = await self.embeddings.embed_query(content)

            # Create point with metadata
            point = PointStruct(
                id=document_id,
                vector=embedding,
                payload={
                    "content": content,
                    "namespace": self.namespace,
                    **metadata
                }
            )

            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )

            logger.info(f"Added document {document_id} to {self.collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error adding document to Qdrant: {e}")
            return False

    async def add_documents_batch(
        self,
        documents: List[Dict[str, Any]]
    ) -> int:
        """
        Add multiple documents in batch

        Args:
            documents: List of documents with 'content' and 'metadata'

        Returns:
            Number of successfully added documents
        """
        try:
            # Prepare contents for embedding
            contents = [doc["content"] for doc in documents]

            # Generate embeddings in batch
            embeddings = await self.embeddings.embed_documents(contents)

            # Create points
            points = []
            for doc, embedding in zip(documents, embeddings):
                point = PointStruct(
                    id=doc.get("id", str(uuid4())),
                    vector=embedding,
                    payload={
                        "content": doc["content"],
                        "namespace": self.namespace,
                        **doc.get("metadata", {})
                    }
                )
                points.append(point)

            # Batch upsert
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            logger.info(f"Added {len(points)} documents to {self.collection_name}")
            return len(points)

        except Exception as e:
            logger.error(f"Error in batch document addition: {e}")
            return 0

    async def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents

        Args:
            query: Search query
            top_k: Number of results to return
            score_threshold: Minimum relevance score
            metadata_filter: Filter by metadata fields

        Returns:
            List of relevant documents with scores
        """
        try:
            # Generate query embedding
            query_embedding = await self.embeddings.embed_query(query)

            # Build filter if provided
            filter_conditions = None
            if metadata_filter:
                conditions = []
                for key, value in metadata_filter.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    filter_conditions = Filter(must=conditions)

            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=filter_conditions,
                score_threshold=score_threshold
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "content": result.payload.get("content", ""),
                    "metadata": {
                        k: v for k, v in result.payload.items()
                        if k not in ["content", "namespace"]
                    }
                })

            return formatted_results

        except Exception as e:
            logger.error(f"Error searching in Qdrant: {e}")
            return []

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[document_id]
            )
            logger.info(f"Deleted document {document_id} from {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "namespace": self.namespace,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "config": info.config
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}