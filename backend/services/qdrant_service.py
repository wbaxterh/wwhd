"""Qdrant vector database service for document storage and retrieval"""
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
import openai
from config import settings
import logging
import uuid

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for managing documents in Qdrant vector database"""

    def __init__(self):
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=60
        )
        self.openai_client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key
        )

    async def ensure_collection_exists(self, namespace: str) -> None:
        """Ensure a collection exists for the given namespace"""
        collection_name = f"documents_{namespace}"

        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            existing_names = [col.name for col in collections]

            if collection_name not in existing_names:
                # Create collection with OpenAI embedding dimensions
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI text-embedding-3-small dimensions
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {collection_name}")

        except Exception as e:
            logger.error(f"Failed to ensure collection {collection_name}: {e}")
            raise

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for text using OpenAI"""
        try:
            response = await self.openai_client.embeddings.create(
                input=texts,
                model=settings.model_embed
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            logger.error(f"Failed to get embeddings: {e}")
            raise

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        if not text:
            return []

        words = text.split()
        if len(words) <= chunk_size:
            return [text]

        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            chunks.append(chunk_text)

            if i + chunk_size >= len(words):
                break

        return chunks

    async def add_document(
        self,
        namespace: str,
        document_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Add a document to the vector database"""

        try:
            await self.ensure_collection_exists(namespace)
            collection_name = f"documents_{namespace}"

            # Chunk the content
            chunks = self.chunk_text(
                content,
                chunk_size=settings.chunk_size,
                overlap=settings.chunk_overlap
            )

            if not chunks:
                raise ValueError("No content to process")

            # Get embeddings for chunks
            embeddings = await self.get_embeddings(chunks)

            # Prepare points for Qdrant
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Use safe point ID format
                safe_document_id = str(document_id).replace('-', '')
                point_id = f"{safe_document_id}_{i:04d}"

                # Ensure all payload values are JSON serializable
                safe_metadata = {}
                for key, value in metadata.items():
                    try:
                        import json
                        # Test serialization and ensure compatible types
                        json.dumps(value)
                        # Ensure value is a basic JSON type
                        if isinstance(value, (str, int, float, bool)) or value is None:
                            safe_metadata[str(key)] = value
                        elif isinstance(value, (list, dict)):
                            # Convert complex types to string for safety
                            safe_metadata[str(key)] = str(value)
                        else:
                            safe_metadata[str(key)] = str(value)
                    except (TypeError, ValueError):
                        safe_metadata[str(key)] = str(value)  # Convert to string if not serializable

                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            **safe_metadata,
                            "document_id": str(document_id),
                            "chunk_index": int(i),
                            "chunk_text": str(chunk),
                            "total_chunks": int(len(chunks))
                        }
                    )
                )

            # Upload to Qdrant
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )

            logger.info(f"Added document {document_id} with {len(chunks)} chunks to {collection_name}")

        except Exception as e:
            logger.error(f"Failed to add document {document_id}: {e}")
            raise

    async def update_document(
        self,
        namespace: str,
        document_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Update a document in the vector database"""

        try:
            # Delete existing document
            await self.delete_document(namespace, document_id)

            # Add updated document
            await self.add_document(namespace, document_id, content, metadata)

            logger.info(f"Updated document {document_id} in namespace {namespace}")

        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {e}")
            raise

    async def delete_document(self, namespace: str, document_id: str) -> None:
        """Delete a document from the vector database"""

        try:
            collection_name = f"documents_{namespace}"

            # Get all points for this document
            scroll_result = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id)
                        )
                    ]
                ),
                limit=1000  # Assume max 1000 chunks per document
            )

            if scroll_result[0]:  # If points exist
                point_ids = [point.id for point in scroll_result[0]]

                # Delete all chunks for this document
                self.client.delete(
                    collection_name=collection_name,
                    points_selector=models.PointIdsList(
                        points=point_ids
                    )
                )

                logger.info(f"Deleted document {document_id} ({len(point_ids)} chunks) from {collection_name}")

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise

    async def search_documents(
        self,
        query: str,
        namespace: Optional[str] = None,
        limit: int = 10,
        score_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Search for relevant documents"""

        try:
            # Get query embedding
            query_embedding = (await self.get_embeddings([query]))[0]

            results = []

            # Determine which collections to search
            if namespace:
                collections = [f"documents_{namespace}"]
            else:
                # Search all collections
                all_collections = self.client.get_collections().collections
                collections = [
                    col.name for col in all_collections
                    if col.name.startswith("documents_")
                ]

            for collection_name in collections:
                try:
                    search_result = self.client.search(
                        collection_name=collection_name,
                        query_vector=query_embedding,
                        limit=limit * 2,  # Get more results for deduplication
                        score_threshold=score_threshold
                    )

                    for hit in search_result:
                        results.append({
                            "document_id": hit.payload.get("document_id"),
                            "namespace": collection_name.replace("documents_", ""),
                            "score": hit.score,
                            "chunk_text": hit.payload.get("chunk_text", ""),
                            "metadata": {
                                k: v for k, v in hit.payload.items()
                                if k not in ["document_id", "chunk_text", "chunk_index", "total_chunks"]
                            }
                        })

                except Exception as e:
                    logger.warning(f"Failed to search collection {collection_name}: {e}")
                    continue

            # Sort by score and deduplicate by document_id
            results.sort(key=lambda x: x["score"], reverse=True)

            # Deduplicate by document_id while preserving highest scoring chunk
            seen_docs = set()
            unique_results = []

            for result in results:
                doc_id = result["document_id"]
                if doc_id not in seen_docs:
                    seen_docs.add(doc_id)
                    unique_results.append(result)

                if len(unique_results) >= limit:
                    break

            return unique_results

        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            raise

    async def get_collection_info(self, namespace: str) -> Dict[str, Any]:
        """Get information about a collection"""

        try:
            collection_name = f"documents_{namespace}"
            info = self.client.get_collection(collection_name)

            return {
                "name": namespace,
                "collection_name": collection_name,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "config": {
                    "distance": info.config.params.vectors.distance,
                    "size": info.config.params.vectors.size
                }
            }

        except Exception as e:
            logger.error(f"Failed to get collection info for {namespace}: {e}")
            raise