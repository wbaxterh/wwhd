"""
InterpreterAgent implementation from AGENTS.md specification
Synthesizes retrieved context into a coherent answer in Herman's voice
"""
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import logging

logger = logging.getLogger(__name__)


class InterpreterAgent:
    """
    InterpreterAgent implementation as specified in AGENTS.md
    Synthesizes retrieved context into coherent responses with citations
    """

    def __init__(self, llm: ChatOpenAI, streaming: bool = True):
        self.llm = llm
        self.streaming = streaming

        # Herman's characteristic voice and style
        self.system_prompt_template = """You are Herman Siu, sharing wisdom in your characteristic warm, thoughtful, and practical voice.

Your responses should:
- Be grounded in the provided context from your knowledge base
- Include specific, actionable advice
- Reference sources naturally within your response
- Maintain a conversational, approachable tone
- Draw connections between concepts when relevant
- Include relevant traditional wisdom (TCM, feng shui, etc.) when appropriate

When using context from sources, weave the information naturally into your response rather than simply listing facts. Your goal is to provide wisdom that helps the person live better.

Context from your knowledge base:
{context}

Guidelines:
- Cite sources using [Source X] format where X matches the source number in the context
- Provide practical, actionable advice
- Be authentic to your voice and philosophy
- If you're uncertain about something, acknowledge it
- Focus on holistic well-being when appropriate"""

    async def interpret(self, state: dict) -> dict:
        """
        Generate response from retrieved context as specified in AGENTS.md

        Args:
            state: ConversationState dict with user_message and retrieved_chunks

        Returns:
            Updated state with final_response and citations
        """
        try:
            # Build context from chunks
            context = self._build_context(state["retrieved_chunks"])

            # Debug: Log the actual context being passed to LLM
            logger.info(f"InterpreterAgent context for question '{state['user_message'][:50]}...': {len(state['retrieved_chunks'])} chunks")
            logger.info(f"Built context: {context[:500]}...")  # First 500 chars of context

            # Generate response
            prompt = self._build_interpretation_prompt(
                question=state["user_message"],
                context=context
            )

            if self.streaming:
                # Handle streaming (placeholder for now)
                response_tokens = []
                response = await self.llm.ainvoke(prompt)
                state["response_tokens"] = [response.content]
                state["final_response"] = response.content
            else:
                response = await self.llm.ainvoke(prompt)
                state["final_response"] = response.content

            # Extract citations
            state["citations"] = self._extract_citations(state["retrieved_chunks"])
            state["current_node"] = "interpreter"
            state["next_node"] = "safety"

            logger.info(f"Generated response with {len(state['citations'])} citations")

        except Exception as e:
            logger.error(f"Error in InterpreterAgent.interpret: {e}")
            state["final_response"] = "I apologize, but I'm having trouble generating a response right now. Please try rephrasing your question."
            state["citations"] = []
            state["error"] = f"Interpretation failed: {str(e)}"

        return state

    def _build_context(self, chunks: List[Dict]) -> str:
        """
        Build context string from retrieved chunks as specified in AGENTS.md

        Format: [1] chunk_text\nSource: source_title (timestamp)
        """
        if not chunks:
            return "No relevant context found in the knowledge base."

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            meta = chunk["metadata"]
            source_info = f"{meta.get('source_title', 'Unknown Source')}"

            # Add timestamp if available
            if meta.get("timestamp"):
                source_info += f" ({meta['timestamp']})"

            context_part = f"[{i}] {chunk['text']}\nSource: {source_info}"
            context_parts.append(context_part)

        return "\n\n".join(context_parts)

    def _build_interpretation_prompt(self, question: str, context: str) -> List[BaseMessage]:
        """Build the interpretation prompt with Herman's voice"""
        system_content = self.system_prompt_template.format(context=context)

        human_content = f"""Question: {question}

Please provide your wisdom and guidance on this question, drawing from the context provided above. Remember to cite sources using [Source X] format and maintain your authentic voice."""

        return [
            SystemMessage(content=system_content),
            HumanMessage(content=human_content)
        ]

    def _extract_citations(self, chunks: List[Dict]) -> List[Dict]:
        """
        Extract citations from chunks as specified in AGENTS.md

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

    def _get_response_quality_score(self, response: str, chunks: List[Dict]) -> float:
        """
        Calculate a quality score for the response based on:
        - Length and completeness
        - Use of context
        - Citation integration
        """
        if not response or len(response) < 50:
            return 0.1

        score = 0.5  # Base score

        # Bonus for length (comprehensive responses)
        if len(response) > 200:
            score += 0.1
        if len(response) > 500:
            score += 0.1

        # Bonus for citing sources
        source_mentions = response.count("[Source")
        if source_mentions > 0:
            score += min(0.2, source_mentions * 0.05)

        # Bonus for using retrieved context
        if chunks:
            context_usage = 0
            for chunk in chunks:
                # Simple check if chunk content appears in response
                chunk_words = chunk["text"].lower().split()[:5]  # First 5 words
                if any(word in response.lower() for word in chunk_words if len(word) > 4):
                    context_usage += 1

            if context_usage > 0:
                score += min(0.2, context_usage * 0.1)

        return min(1.0, score)