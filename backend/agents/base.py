"""Base agent class for all specialist agents"""
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool
from rag.retriever import QdrantRetriever
from config import settings
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents"""

    def __init__(
        self,
        name: str,
        description: str,
        namespace: str,
        system_prompt: str,
        tools: Optional[List[BaseTool]] = None,
        model_name: Optional[str] = None
    ):
        self.name = name
        self.description = description
        self.namespace = namespace  # Qdrant namespace for this agent
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.model_name = model_name or settings.specialist_model
        self.retriever = QdrantRetriever(namespace=namespace)

    @abstractmethod
    async def process(
        self,
        query: str,
        chat_history: List[BaseMessage],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a query and return a response

        Args:
            query: User's input query
            chat_history: Previous messages in the conversation
            context: Additional context from orchestrator

        Returns:
            Dictionary containing:
            - content: The response text
            - sources: List of sources used
            - metadata: Any additional metadata
        """
        pass

    async def retrieve_context(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context from vector database

        Args:
            query: Query to search for
            top_k: Number of results to return

        Returns:
            List of relevant documents with scores
        """
        top_k = top_k or settings.top_k_retrieval

        try:
            results = await self.retriever.search(
                query=query,
                top_k=top_k,
                score_threshold=settings.min_relevance_score
            )
            return results
        except Exception as e:
            logger.error(f"Error retrieving context for {self.name}: {e}")
            return []

    def format_sources(self, sources: List[Dict[str, Any]]) -> str:
        """Format sources for citation in response"""
        if not sources:
            return ""

        formatted = "\n\n**Sources:**\n"
        for i, source in enumerate(sources, 1):
            title = source.get("metadata", {}).get("title", "Unknown")
            url = source.get("metadata", {}).get("url", "")
            score = source.get("score", 0)

            formatted += f"{i}. {title}"
            if url:
                formatted += f" ({url})"
            formatted += f" - Relevance: {score:.2f}\n"

        return formatted

    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities for orchestrator"""
        return {
            "name": self.name,
            "description": self.description,
            "namespace": self.namespace,
            "tools": [tool.name for tool in self.tools],
            "model": self.model_name
        }