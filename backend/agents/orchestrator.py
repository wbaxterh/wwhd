"""
Orchestrator Agent using LangGraph
Routes queries to appropriate specialist agents
"""
from typing import List, Dict, Any, Optional, TypedDict, Literal
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import StateGraph, END
from langchain.prompts import ChatPromptTemplate
from config import settings
import logging
import json
import re
from datetime import datetime
from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)


class ConversationState(TypedDict):
    """State for the LangGraph conversation flow as defined in AGENTS.md"""
    # Message context
    user_id: str
    session_id: str
    message_id: str
    user_message: str
    timestamp: datetime

    # Routing
    intent: Optional[str]
    confidence: float
    selected_namespaces: List[str]
    selected_agents: List[str]

    # RAG context
    retrieved_chunks: List[dict]  # {text, metadata, score}
    reranked_chunks: Optional[List[dict]]

    # Generation
    system_prompt: str
    safety_flags: List[str]
    response_tokens: List[str]
    final_response: str
    citations: List[dict]  # {source_title, url, timestamp}

    # Accounting
    prompt_tokens: int
    completion_tokens: int
    embedding_tokens: int
    total_cost: float

    # Control flow
    current_node: str
    next_node: Optional[str]
    error: Optional[str]
    status: Literal["processing", "streaming", "complete", "error"]


class RouterAgent:
    """
    RouterAgent implementation from AGENTS.md specification
    Classifies user intent and selects appropriate namespaces
    """

    def __init__(self, llm):
        self.llm = llm
        # Namespace mapping as defined in AGENTS.md
        self.namespace_map = {
            "relationships": ["dating", "marriage", "family", "friendship", "love", "communication", "interpersonal"],
            "money": ["investing", "savings", "wealth", "finance", "budget", "financial", "prosperity"],
            "business": ["entrepreneurship", "startup", "management", "leadership", "career", "work"],
            "feng_shui": ["energy", "space", "harmony", "arrangement", "chi", "home", "environment"],
            "diet_food": ["nutrition", "eating", "health", "cooking", "meal", "diet", "food"],
            "exercise_martial_arts": ["training", "fitness", "shaolin", "kungfu", "workout", "martial", "exercise"],
            "meditation": ["mindfulness", "breathing", "zen", "peace", "calm", "spiritual", "meditation"],
            "general": []  # Fallback
        }

        # Routing configuration
        self.routing_rules = {
            "confidence_threshold": 0.7,
            "max_namespaces": 3,
            "fallback": "general",
            "multi_namespace_keywords": ["balance", "holistic", "life", "wellness"],
        }

    async def route(self, state: ConversationState) -> ConversationState:
        """Route user message to appropriate namespaces"""
        prompt = self._build_routing_prompt(state["user_message"])
        response = await self.llm.ainvoke(prompt)

        # Parse intent and confidence
        intent, confidence = self._parse_response(response.content)

        # Map to namespaces
        namespaces = self._select_namespaces(intent, confidence, state["user_message"])

        state["intent"] = intent
        state["confidence"] = confidence
        state["selected_namespaces"] = namespaces
        state["current_node"] = "router"
        state["next_node"] = "librarian" if namespaces and "general" not in namespaces else "interpreter"

        return state

    def _build_routing_prompt(self, message: str) -> List[BaseMessage]:
        """Build routing prompt as specified in AGENTS.md"""
        prompt = f"""
Classify the following user message into one or more categories:
- relationships: dating, marriage, family, friendship, love, interpersonal issues
- money: investing, savings, wealth, finance, budget, financial advice
- business: entrepreneurship, startup, management, leadership, career
- feng_shui: energy, space, harmony, arrangement, chi, home environment
- diet_food: nutrition, eating, health, cooking, meal planning
- exercise_martial_arts: training, fitness, shaolin, kungfu, workout, martial arts
- meditation: mindfulness, breathing, zen, peace, calm, spiritual practices
- general: anything else that doesn't clearly fit the above categories

Message: {message}

Return format:
Intent: <primary_intent>
Confidence: <0.0-1.0>
Categories: <comma_separated_list>
"""
        return [HumanMessage(content=prompt)]

    def _parse_response(self, response_content: str) -> tuple[str, float]:
        """Parse LLM response to extract intent and confidence"""
        try:
            intent_match = re.search(r"Intent: (.+)", response_content)
            confidence_match = re.search(r"Confidence: ([0-9.]+)", response_content)

            intent = intent_match.group(1).strip() if intent_match else "general"
            confidence = float(confidence_match.group(1)) if confidence_match else 0.5

            return intent, confidence
        except Exception as e:
            logger.warning(f"Error parsing routing response: {e}")
            return "general", 0.5

    def _select_namespaces(self, intent: str, confidence: float, message: str) -> List[str]:
        """Map intent to namespaces based on keywords and confidence"""
        selected = []
        message_lower = message.lower()

        # Check for multi-namespace keywords
        for keyword in self.routing_rules["multi_namespace_keywords"]:
            if keyword in message_lower:
                # Return multiple relevant namespaces for holistic queries
                return ["meditation", "relationships", "general"]

        # Map intent to namespace if confidence is high enough
        if confidence >= self.routing_rules["confidence_threshold"]:
            for namespace, keywords in self.namespace_map.items():
                if namespace == "general":
                    continue
                if intent.lower() in keywords or any(kw in message_lower for kw in keywords):
                    selected.append(namespace)

        # Fallback to general if no matches or low confidence
        if not selected:
            selected = [self.routing_rules["fallback"]]

        # Limit max namespaces
        return selected[:self.routing_rules["max_namespaces"]]

    def _initialize_llm(self):
        """Initialize the LLM based on configuration"""
        if settings.enable_openai:
            return ChatOpenAI(
                model=settings.orchestrator_model,
                temperature=0.3,
                openai_api_key=settings.openai_api_key,
                streaming=settings.enable_streaming
            )
        else:
            # Add OpenRouter support here if needed
            raise NotImplementedError("OpenRouter support not yet implemented")

class OrchestratorAgent:
    """
    Main orchestrator implementing the LangGraph state machine from AGENTS.md
    """

    def __init__(self):
        self.llm = self._initialize_llm()
        self.router_agent = RouterAgent(self.llm)

        # Initialize other agents
        self.embedder = self._initialize_embedder()
        self.qdrant_client = self._initialize_qdrant()

        # Import and initialize agent components
        self.librarian_agent = self._initialize_librarian()
        self.interpreter_agent = self._initialize_interpreter()
        self.safety_agent = self._initialize_safety()

        self.graph = self._build_graph()

    def _initialize_embedder(self):
        """Initialize OpenAI embeddings"""
        return OpenAIEmbeddings(
            model=settings.model_embed,
            openai_api_key=settings.openai_api_key
        )

    def _initialize_qdrant(self):
        """Initialize Qdrant client"""
        return QdrantClient(url=settings.qdrant_url)

    def _initialize_librarian(self):
        """Initialize LibrarianAgent"""
        try:
            from .librarian import LibrarianAgent
            return LibrarianAgent(
                qdrant_client=self.qdrant_client,
                embedder=self.embedder
            )
        except ImportError as e:
            logger.error(f"Failed to import LibrarianAgent: {e}")
            return None

    def _initialize_interpreter(self):
        """Initialize InterpreterAgent"""
        try:
            from .interpreter import InterpreterAgent
            return InterpreterAgent(
                llm=self.llm,
                streaming=settings.enable_streaming
            )
        except ImportError as e:
            logger.error(f"Failed to import InterpreterAgent: {e}")
            return None

    def _initialize_safety(self):
        """Initialize SafetyAgent"""
        try:
            from .safety import SafetyAgent
            return SafetyAgent(llm=self.llm)
        except ImportError as e:
            logger.error(f"Failed to import SafetyAgent: {e}")
            return None

    def _build_conversation_graph(self):
        """Build conversation graph as specified in AGENTS.md"""
        # Initialize graph
        graph = StateGraph(ConversationState)

        # Add nodes with actual agent implementations
        graph.add_node("router", self.router_agent.route)
        graph.add_node("librarian", self._librarian_node)
        graph.add_node("interpreter", self._interpreter_node)
        graph.add_node("safety", self._safety_node)

        # Add edges as specified in AGENTS.md
        graph.add_conditional_edges(
            "router",
            lambda state: state["next_node"],
            {
                "librarian": "librarian",
                "interpreter": "interpreter"
            }
        )
        graph.add_edge("librarian", "interpreter")
        graph.add_edge("interpreter", "safety")
        graph.add_edge("safety", END)

        # Set entry point
        graph.set_entry_point("router")

        return graph.compile()

    async def _librarian_node(self, state: ConversationState) -> ConversationState:
        """LibrarianAgent node in the graph"""
        if self.librarian_agent:
            return await self.librarian_agent.retrieve(state)
        else:
            # Fallback if LibrarianAgent not available
            logger.warning("LibrarianAgent not available, skipping retrieval")
            state["retrieved_chunks"] = []
            state["current_node"] = "librarian"
            state["next_node"] = "interpreter"
            return state

    async def _interpreter_node(self, state: ConversationState) -> ConversationState:
        """InterpreterAgent node in the graph"""
        if self.interpreter_agent:
            return await self.interpreter_agent.interpret(state)
        else:
            # Fallback if InterpreterAgent not available
            logger.warning("InterpreterAgent not available, using simple response")
            prompt = f"Please provide wisdom about: {state['user_message']}"
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])

            state["final_response"] = response.content
            state["citations"] = []
            state["current_node"] = "interpreter"
            state["next_node"] = "safety"
            return state

    async def _safety_node(self, state: ConversationState) -> ConversationState:
        """SafetyAgent node in the graph"""
        if self.safety_agent:
            return await self.safety_agent.check_safety(state)
        else:
            # Fallback if SafetyAgent not available
            logger.warning("SafetyAgent not available, skipping safety checks")
            state["safety_flags"] = ["safety_agent_unavailable"]
            state["current_node"] = "safety"
            state["next_node"] = None
            state["status"] = "complete"
            return state

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow using the conversation graph"""
        return self._build_conversation_graph()


    async def process(
        self,
        query: str,
        chat_history: Optional[List[BaseMessage]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing queries using the ConversationState
        """
        # Initialize state following AGENTS.md specification
        initial_state = {
            "user_id": "system",
            "session_id": "system",
            "message_id": "system",
            "user_message": query,
            "timestamp": datetime.now(),

            # Routing
            "intent": None,
            "confidence": 0.0,
            "selected_namespaces": [],
            "selected_agents": [],

            # RAG context
            "retrieved_chunks": [],
            "reranked_chunks": None,

            # Generation
            "system_prompt": "",
            "safety_flags": [],
            "response_tokens": [],
            "final_response": "",
            "citations": [],

            # Accounting
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "embedding_tokens": 0,
            "total_cost": 0.0,

            # Control flow
            "current_node": "",
            "next_node": None,
            "error": None,
            "status": "processing"
        }

        try:
            final_state = await self.graph.ainvoke(initial_state)

            return {
                "content": final_state["final_response"],
                "agents_used": final_state["selected_namespaces"],  # Return namespaces instead of agents
                "sources": final_state["citations"],
                "metadata": {
                    "intent": final_state["intent"],
                    "confidence": final_state["confidence"],
                    "namespaces": final_state["selected_namespaces"],
                    "safety_flags": final_state["safety_flags"]
                }
            }

        except Exception as e:
            logger.error(f"Error in orchestrator processing: {e}")
            return {
                "content": "I apologize, but I encountered an error processing your request. Please try again.",
                "error": str(e),
                "agents_used": [],
                "sources": []
            }