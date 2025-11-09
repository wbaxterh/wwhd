"""Embedding generation for documents"""
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from config import settings
import logging

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for text using configured model"""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.model_embed
        self._initialize_embeddings()

    def _initialize_embeddings(self):
        """Initialize the embeddings model"""
        if settings.enable_openai:
            self.embeddings = OpenAIEmbeddings(
                model=self.model_name,
                openai_api_key=settings.openai_api_key
            )
        else:
            # Add OpenRouter or other providers here
            raise NotImplementedError("Only OpenAI embeddings supported currently")

    async def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query

        Args:
            text: Query text to embed

        Returns:
            List of floats representing the embedding
        """
        try:
            embedding = await self.embeddings.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents

        Args:
            texts: List of document texts to embed

        Returns:
            List of embeddings
        """
        try:
            embeddings = await self.embeddings.aembed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating document embeddings: {e}")
            raise

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding model"""
        # OpenAI embedding dimensions
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        return model_dimensions.get(self.model_name, 1536)