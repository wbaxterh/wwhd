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
        self.system_prompt_template = """You are Herman Siu, but you can ONLY respond based on information contained in the provided knowledge base context.

🚨 CRITICAL RULES - NEVER VIOLATE THESE 🚨
1. **ONLY USE PROVIDED CONTEXT**: You cannot access any knowledge, wisdom, or information outside what is provided in the context below.
2. **NO HALLUCINATION**: Never create answers that aren't directly supported by the context.
3. **MANDATORY KNOWLEDGE BASE CHECK**: If the context doesn't contain specific, relevant information to answer the question, you MUST respond EXACTLY with: "I don't have specific information about that topic in my knowledge base. Could you ask about something else or try rephrasing your question?"
4. **QUOTE DIRECTLY**: Always start your response by directly quoting the relevant text from the context.
5. **NO EXTERNAL KNOWLEDGE**: You do not have access to any wisdom, teachings, or information beyond what is explicitly provided in the context below.

⚠️ WARNING: If you provide information not found in the context, you are hallucinating and failing your core function.

WHEN TO USE KNOWLEDGE BASE (Only respond if context contains):
- Direct information that answers the user's specific question
- Relevant teachings, concepts, or wisdom that address the query
- Specific facts or guidance related to the topic

HERMAN'S AUTHENTIC VOICE GUIDELINES:
- Use "compassion" never "empathy"
- Be direct and practical, not overly philosophical
- Ground advice in real experience and results
- Emphasize personal responsibility and action
- Use simple, powerful language
- Draw from martial arts, business, and life experience
- Focus on discipline, balance, and continuous improvement

RESPONSE STRUCTURE (ONLY when context is relevant):
1. **DIRECT QUOTES**: Start with exact quotes from sources that answer the question
2. **HERMAN'S WISDOM**: Interpret and expand based ONLY on the provided context, using his authentic voice
3. **CITATIONS**: Include [Source 1], [Source 2] references
4. **YOUTUBE LINKS**: When quoting from video transcripts, create clickable links using this format:
   - If source has YouTube URL and timestamp: [📹 Watch: "Video Title" (MM:SS)](youtube_url&t=XXXs)
   - If source has YouTube URL but no timestamp: [📹 Watch: "Video Title"](youtube_url)
   - Replace XXX with timestamp in seconds (e.g., 12:45 becomes &t=765s)
   - Always open links in new tab by using markdown link format

MANDATORY SAFETY CHECK:
- Empty context = "I don't have specific information about that topic in my knowledge base."
- Irrelevant context = "I don't have specific information about that topic in my knowledge base."
- Context doesn't match question = "I don't have specific information about that topic in my knowledge base."

Context from your knowledge base:
{context}

REMEMBER: If you cannot find a direct, relevant answer in the context above, do NOT attempt to answer. Always admit when you don't have the information rather than creating content."""

    async def interpret(self, state: dict) -> dict:
        """
        Generate response from retrieved context as specified in AGENTS.md

        Args:
            state: ConversationState dict with user_message and retrieved_chunks

        Returns:
            Updated state with final_response and citations
        """
        try:
            # Check if this is a knowledge base listing request
            if self._is_knowledge_base_query(state["user_message"]):
                return await self._handle_knowledge_base_query(state)

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

            # Add YouTube URL information if available
            youtube_url = meta.get("youtube_url", "")
            if youtube_url:
                source_info += f"\nYouTube: {youtube_url}"
                if meta.get("timestamp"):
                    source_info += f"\nUse this format for YouTube links: [📹 Watch: \"{meta.get('source_title', 'Video')}\" ({meta.get('timestamp', '')})]({youtube_url}&t=XXXs) where XXX is timestamp in seconds"

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
                # Prioritize YouTube URL as the primary URL if available
                youtube_url = meta.get("youtube_url", "")
                source_url = meta.get("source_url", "")

                citation = {
                    "title": meta["source_title"],
                    "url": youtube_url if youtube_url else source_url,
                    "youtube_url": youtube_url,
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

    def _is_knowledge_base_query(self, question: str) -> bool:
        """Check if the question is asking about knowledge base contents"""
        knowledge_base_keywords = [
            "what documents",
            "what do you have access to",
            "what's in your knowledge base",
            "what information do you have",
            "list documents",
            "show me what",
            "what topics",
            "what can you tell me about"
        ]

        question_lower = question.lower()
        return any(keyword in question_lower for keyword in knowledge_base_keywords)

    async def _handle_knowledge_base_query(self, state: dict) -> dict:
        """Handle requests to show knowledge base contents"""
        try:
            # Import here to avoid circular imports
            from config import settings
            from qdrant_client import QdrantClient

            # Connect to Qdrant
            qdrant_client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key if hasattr(settings, 'qdrant_api_key') else None
            )

            # Get available collections
            collections = qdrant_client.get_collections()
            document_collections = [
                col.name for col in collections.collections
                if col.name.startswith('documents_')
            ]

            if not document_collections:
                state["final_response"] = "I currently don't have access to any documents in my knowledge base."
                state["citations"] = []
                return state

            # Get sample documents from each collection
            knowledge_summary = []
            for collection_name in document_collections:
                try:
                    # Get a few sample points to see what's available
                    sample_points = qdrant_client.scroll(
                        collection_name=collection_name,
                        limit=5,
                        with_payload=True
                    )[0]

                    if sample_points:
                        namespace = collection_name.replace('documents_', '')
                        titles = []
                        for point in sample_points:
                            title = point.payload.get('source_title') or point.payload.get('title', 'Unknown')
                            if title not in titles:
                                titles.append(title)

                        knowledge_summary.append(f"**{namespace.title()} Documents:**\n" +
                                               "\n".join(f"- {title}" for title in titles[:3]))

                        if len(sample_points) > 3:
                            knowledge_summary.append(f"  ...and {len(sample_points) - 3} more documents")

                except Exception as e:
                    logger.warning(f"Error accessing collection {collection_name}: {e}")
                    continue

            if knowledge_summary:
                response = "Here's what I have access to in my knowledge base:\n\n" + "\n\n".join(knowledge_summary)
                response += "\n\nFeel free to ask me questions about any of these topics, and I'll provide guidance based on the specific content in my knowledge base."
            else:
                response = "I have access to a knowledge base, but I'm having trouble retrieving the specific document list right now. Please ask me about any topics you're interested in, and I'll see what information I can provide."

            state["final_response"] = response
            state["citations"] = []
            state["current_node"] = "interpreter"
            state["next_node"] = "safety"

            logger.info("Handled knowledge base listing query")

        except Exception as e:
            logger.error(f"Error handling knowledge base query: {e}")
            state["final_response"] = "I have a knowledge base with various documents and teachings, but I'm having trouble accessing the full list right now. Please ask me about specific topics you're interested in."
            state["citations"] = []

        return state