"""
Orchestrator Agent using LangGraph
Routes queries to appropriate specialist agents
"""
from typing import List, Dict, Any, Optional, TypedDict
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain.prompts import ChatPromptTemplate
from config import settings
import logging
import json

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the agent graph"""
    messages: List[BaseMessage]
    query: str
    selected_agents: List[str]
    agent_responses: Dict[str, Any]
    final_response: str
    sources: List[Dict[str, Any]]


class OrchestratorAgent:
    """
    Main orchestrator that routes queries to specialist agents
    Uses LangGraph for stateful workflow management
    """

    def __init__(self):
        self.llm = self._initialize_llm()
        self.graph = self._build_graph()
        self.available_agents = self._register_agents()

        # System prompt for routing decisions
        self.routing_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Herman Siu's wisdom orchestrator. Your role is to analyze user queries and determine which specialist agents should handle them.

Available specialist agents:
1. TCM Specialist - Traditional Chinese Medicine, herbs, meridians, health conditions
2. Relationship Specialist - Interpersonal relationships, communication, family dynamics
3. Money Specialist - Financial wisdom, prosperity mindset, practical budgeting
4. Feng Shui Specialist - Spatial harmony, energy flow, environmental optimization

Analyze the user's query and respond with a JSON object containing:
{{
    "agents": ["agent_name1", "agent_name2"],  // List of agents to consult (can be empty if you can answer directly)
    "reasoning": "Brief explanation of why these agents were chosen",
    "direct_answer": "Your direct response if no agents are needed (null otherwise)"
}}

Guidelines:
- Select 0-2 agents based on query relevance
- If the query is general or doesn't match any specialist, provide a direct answer
- For health queries, always include TCM Specialist
- For home/space queries, include Feng Shui Specialist
- Combine agents when query spans multiple domains
"""),
            ("human", "{query}")
        ])

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

    def _register_agents(self) -> Dict[str, Any]:
        """Register available specialist agents"""
        # Import specialist agents (to be implemented)
        agents = {}

        try:
            from .tcm_specialist import TCMSpecialist
            agents["TCM Specialist"] = TCMSpecialist()
        except ImportError:
            logger.warning("TCM Specialist not available")

        try:
            from .relationship_specialist import RelationshipSpecialist
            agents["Relationship Specialist"] = RelationshipSpecialist()
        except ImportError:
            logger.warning("Relationship Specialist not available")

        try:
            from .money_specialist import MoneySpecialist
            agents["Money Specialist"] = MoneySpecialist()
        except ImportError:
            logger.warning("Money Specialist not available")

        try:
            from .feng_shui_specialist import FengShuiSpecialist
            agents["Feng Shui Specialist"] = FengShuiSpecialist()
        except ImportError:
            logger.warning("Feng Shui Specialist not available")

        return agents

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("route", self._route_query)
        workflow.add_node("consult_agents", self._consult_agents)
        workflow.add_node("synthesize", self._synthesize_response)

        # Define edges
        workflow.set_entry_point("route")

        # Conditional routing based on whether agents are needed
        workflow.add_conditional_edges(
            "route",
            self._should_consult_agents,
            {
                True: "consult_agents",
                False: "synthesize"
            }
        )

        workflow.add_edge("consult_agents", "synthesize")
        workflow.add_edge("synthesize", END)

        return workflow.compile()

    async def _route_query(self, state: AgentState) -> AgentState:
        """Analyze query and determine routing"""
        query = state["query"]

        try:
            # Get routing decision from LLM
            routing_messages = self.routing_prompt.format_messages(query=query)
            response = await self.llm.ainvoke(routing_messages)

            # Parse JSON response
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]

            routing_decision = json.loads(content)

            state["selected_agents"] = routing_decision.get("agents", [])

            # If direct answer provided, use it
            if routing_decision.get("direct_answer"):
                state["final_response"] = routing_decision["direct_answer"]

            logger.info(f"Routing decision: {routing_decision}")

        except Exception as e:
            logger.error(f"Error in routing: {e}")
            state["selected_agents"] = []
            state["final_response"] = "I'll do my best to help you with that."

        return state

    def _should_consult_agents(self, state: AgentState) -> bool:
        """Determine if we need to consult specialist agents"""
        return len(state.get("selected_agents", [])) > 0

    async def _consult_agents(self, state: AgentState) -> AgentState:
        """Consult selected specialist agents"""
        agent_responses = {}

        for agent_name in state["selected_agents"]:
            if agent_name in self.available_agents:
                try:
                    agent = self.available_agents[agent_name]
                    response = await agent.process(
                        query=state["query"],
                        chat_history=state["messages"],
                        context={"orchestrator": True}
                    )
                    agent_responses[agent_name] = response

                    # Collect sources
                    if response.get("sources"):
                        state["sources"].extend(response["sources"])

                except Exception as e:
                    logger.error(f"Error consulting {agent_name}: {e}")
                    agent_responses[agent_name] = {
                        "content": f"Error consulting {agent_name}",
                        "error": str(e)
                    }

        state["agent_responses"] = agent_responses
        return state

    async def _synthesize_response(self, state: AgentState) -> AgentState:
        """Synthesize final response from agent consultations"""

        # If we already have a direct answer, use it
        if state.get("final_response"):
            return state

        # If we have agent responses, synthesize them
        if state.get("agent_responses"):
            synthesis_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are Herman Siu synthesizing wisdom from various specialists.
Combine the insights from the specialist agents into a cohesive, helpful response.
Maintain Herman's warm, wise, and practical voice.
Include specific recommendations and actionable advice."""),
                ("human", f"""Query: {state['query']}

Agent Responses:
{json.dumps(state['agent_responses'], indent=2)}

Please provide a unified response that combines these insights.""")
            ])

            messages = synthesis_prompt.format_messages()
            response = await self.llm.ainvoke(messages)
            state["final_response"] = response.content

        else:
            # Fallback response
            state["final_response"] = "I understand your question. Let me share some wisdom on this."

        return state

    async def process(
        self,
        query: str,
        chat_history: Optional[List[BaseMessage]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing queries

        Args:
            query: User's query
            chat_history: Previous conversation messages

        Returns:
            Dictionary with response and metadata
        """
        # Initialize state
        initial_state = {
            "query": query,
            "messages": chat_history or [],
            "selected_agents": [],
            "agent_responses": {},
            "final_response": "",
            "sources": []
        }

        # Run the graph
        try:
            final_state = await self.graph.ainvoke(initial_state)

            return {
                "content": final_state["final_response"],
                "agents_used": final_state["selected_agents"],
                "sources": final_state["sources"],
                "metadata": {
                    "agent_responses": final_state.get("agent_responses", {})
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