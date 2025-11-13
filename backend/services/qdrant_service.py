"""Qdrant vector database service for document storage and retrieval"""
from typing import List, Dict, Any, Optional
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document as LangChainDocument
from qdrant_client import QdrantClient
from config import settings
import logging

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for managing documents in Qdrant vector database"""

    def __init__(self):
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=60
        )
        self.embeddings = OpenAIEmbeddings(
            model=settings.model_embed,
            openai_api_key=settings.openai_api_key
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
        )

    def _get_vector_store(self, namespace: str) -> QdrantVectorStore:
        """Get or create a QdrantVectorStore for the given namespace"""
        collection_name = f"documents_{namespace}"

        return QdrantVectorStore(
            client=self.client,
            collection_name=collection_name,
            embeddings=self.embeddings,
        )

    async def add_document(
        self,
        namespace: str,
        document_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Add a document to the vector database"""

        try:
            # Get the vector store for this namespace
            vector_store = self._get_vector_store(namespace)

            # Split the content into chunks
            chunks = self.text_splitter.split_text(content)

            if not chunks:
                raise ValueError("No content to process")

            # Prepare document metadata for all chunks
            doc_metadata = {
                "document_id": str(document_id),
                "namespace": str(namespace),
                **{str(k): str(v) for k, v in metadata.items()}  # Ensure all values are strings
            }

            # Create LangChain documents
            documents = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    **doc_metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }

                documents.append(LangChainDocument(
                    page_content=chunk,
                    metadata=chunk_metadata
                ))

            # Add documents to vector store
            await vector_store.aadd_documents(documents)

            logger.info(f"Added document {document_id} with {len(chunks)} chunks to namespace {namespace}")

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
            from qdrant_client.http import models

            collection_name = f"documents_{namespace}"

            # Get all points for this document
            scroll_result = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=str(document_id))
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
                    points_selector=models.PointIdsList(points=point_ids),
                    wait=True
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
            results = []

            # Determine which namespaces to search
            if namespace:
                namespaces = [namespace]
            else:
                # Get all collections to determine available namespaces
                all_collections = self.client.get_collections().collections
                namespaces = [
                    col.name.replace("documents_", "")
                    for col in all_collections
                    if col.name.startswith("documents_")
                ]

            for ns in namespaces:
                try:
                    vector_store = self._get_vector_store(ns)

                    # Use similarity search with score threshold
                    search_results = await vector_store.asimilarity_search_with_score(
                        query=query,
                        k=limit * 2  # Get more results for deduplication
                    )

                    for doc, score in search_results:
                        if score >= score_threshold:
                            # Extract metadata
                            metadata = doc.metadata.copy()
                            document_id = metadata.pop("document_id", "")
                            chunk_index = metadata.pop("chunk_index", 0)
                            total_chunks = metadata.pop("total_chunks", 1)

                            results.append({
                                "document_id": document_id,
                                "namespace": ns,
                                "score": score,
                                "chunk_text": doc.page_content,
                                "metadata": metadata
                            })

                except Exception as e:
                    logger.warning(f"Failed to search namespace {ns}: {e}")
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
                "vectors_count": info.vectors_count if hasattr(info, 'vectors_count') else 0,
                "indexed_vectors_count": info.indexed_vectors_count if hasattr(info, 'indexed_vectors_count') else 0,
                "points_count": info.points_count if hasattr(info, 'points_count') else 0,
                "segments_count": info.segments_count if hasattr(info, 'segments_count') else 0,
                "config": {
                    "distance": info.config.params.vectors.distance if hasattr(info.config.params.vectors, 'distance') else 'cosine',
                    "size": info.config.params.vectors.size if hasattr(info.config.params.vectors, 'size') else 1536
                }
            }

        except Exception as e:
            logger.error(f"Failed to get collection info for {namespace}: {e}")
            raise