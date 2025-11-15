"""
LibrarianAgent implementation from AGENTS.md specification
Performs hybrid retrieval from Qdrant vector database and manages reranking
"""
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models
import logging

logger = logging.getLogger(__name__)


class LibrarianAgent:
    """
    LibrarianAgent implementation as specified in AGENTS.md
    Handles vector similarity search across selected namespaces
    """

    def __init__(self, qdrant_client: QdrantClient, embedder: OpenAIEmbeddings, reranker=None):
        self.qdrant = qdrant_client
        self.embedder = embedder
        self.reranker = reranker

        # Retrieval parameters from AGENTS.md
        self.search_config = {
            "top_k": 5,
            "score_threshold": 0.3,  # Lowered from 0.7 to allow more results
            "include_metadata": True,
            "use_mmr": False  # Maximal Marginal Relevance - disabled in v0.1
        }

        # Reranking configuration
        self.reranking_config = {
            "enabled": False,  # Enable in v0.2 as per AGENTS.md
            "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "top_k": 3
        }

    async def retrieve(self, state: dict) -> dict:
        """
        Retrieve context from Qdrant as specified in AGENTS.md

        Args:
            state: ConversationState dict containing user_message and selected_namespaces

        Returns:
            Updated state with retrieved_chunks
        """
        try:
            # Embed query
            query_vector = await self.embedder.aembed_query(state["user_message"])

            # Search across namespaces
            all_chunks = []
            for namespace in state["selected_namespaces"]:
                try:
                    results = await self._search_namespace(
                        namespace=namespace,
                        query_vector=query_vector,
                        limit=self.search_config["top_k"]
                    )
                    formatted_chunks = self._format_chunks(results, namespace)
                    all_chunks.extend(formatted_chunks)

                except Exception as e:
                    logger.warning(f"Error searching namespace {namespace}: {e}")
                    continue

            # Optional reranking (disabled in v0.1)
            if self.reranker and self.reranking_config["enabled"] and len(all_chunks) > 5:
                all_chunks = await self.reranker.rerank(
                    query=state["user_message"],
                    documents=all_chunks,
                    top_k=self.reranking_config["top_k"]
                )

            # Take top 5 chunks and sort by score
            all_chunks = sorted(all_chunks, key=lambda x: x["score"], reverse=True)
            state["retrieved_chunks"] = all_chunks[:self.search_config["top_k"]]

            # Extract citations for frontend streaming
            state["citations"] = self._extract_citations(state["retrieved_chunks"])

            state["current_node"] = "librarian"
            state["next_node"] = "interpreter"

            logger.info(f"Retrieved {len(state['retrieved_chunks'])} chunks from {len(state['selected_namespaces'])} namespaces")

        except Exception as e:
            logger.error(f"Error in LibrarianAgent.retrieve: {e}")
            state["retrieved_chunks"] = []
            state["error"] = f"Retrieval failed: {str(e)}"

        return state

    async def _search_namespace(self, namespace: str, query_vector: List[float], limit: int) -> List:
        """Search a specific namespace/collection in Qdrant"""
        try:
            # Check if collection exists (with documents_ prefix)
            collection_name = f"documents_{namespace}"
            collections = self.qdrant.get_collections()
            collection_names = [c.name for c in collections.collections]

            if collection_name not in collection_names:
                logger.warning(f"Collection {collection_name} not found in Qdrant")
                return []

            # Perform vector search
            search_result = self.qdrant.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=self.search_config["score_threshold"],
                with_payload=True,
                with_vectors=False
            )

            return search_result

        except Exception as e:
            logger.error(f"Error searching namespace {namespace}: {e}")
            return []

    def _format_chunks(self, results: List, namespace: str) -> List[Dict]:
        """
        Format Qdrant search results as specified in AGENTS.md

        Returns:
            List of dicts with {text, score, metadata} structure
        """
        formatted = []

        for result in results:
            try:
                chunk = {
                    "text": result.payload.get("content", ""),
                    "score": float(result.score),
                    "metadata": {
                        "namespace": namespace,
                        "source_url": result.payload.get("source_url", ""),
                        "source_title": result.payload.get("source_title", "Unknown Source"),
                        "timestamp": result.payload.get("transcript_timestamp", ""),
                        "tags": result.payload.get("tags", []),
                        "chunk_index": result.payload.get("chunk_index", 0),
                        "checksum": result.payload.get("checksum", "")
                    }
                }

                # Format citation for API response
                chunk["citation"] = self._format_citation(chunk["metadata"])

                # Only include chunks with actual content
                if chunk["text"].strip():
                    formatted.append(chunk)

            except Exception as e:
                logger.warning(f"Error formatting chunk: {e}")
                continue

        return formatted

    def _format_citation(self, metadata: Dict) -> Dict:
        """Format citation according to API spec and PROMPTS.md"""
        return {
            "title": metadata.get("source_title", "Unknown Source"),
            "url": metadata.get("source_url", ""),
            "timestamp": metadata.get("timestamp", "")
        }

    def _extract_citations(self, chunks: List[Dict]) -> List[Dict]:
        """
        Extract unique citations from retrieved chunks for streaming

        Returns:
            List of {title, url, timestamp} dicts
        """
        citations = []

        for chunk in chunks:
            meta = chunk["metadata"]

            # Include citations with source title (URL is optional)
            if meta.get("source_title"):
                citation = {
                    "title": meta["source_title"],
                    "url": meta.get("source_url", ""),
                    "timestamp": meta.get("timestamp", "")
                }

                # Avoid duplicate citations
                if citation not in citations:
                    citations.append(citation)

        return citations

    def get_retrieval_stats(self, chunks: List[Dict]) -> Dict:
        """Get statistics about retrieved chunks"""
        if not chunks:
            return {"total_chunks": 0, "namespaces": [], "avg_score": 0.0}

        namespaces = list(set(chunk["metadata"]["namespace"] for chunk in chunks))
        avg_score = sum(chunk["score"] for chunk in chunks) / len(chunks)

        return {
            "total_chunks": len(chunks),
            "namespaces": namespaces,
            "avg_score": round(avg_score, 3),
            "score_range": {
                "min": min(chunk["score"] for chunk in chunks),
                "max": max(chunk["score"] for chunk in chunks)
            }
        }