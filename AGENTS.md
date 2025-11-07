# Agents

## LangGraph Agent Architecture

### Overview

The W.W.H.D. system uses LangGraph to orchestrate a multi-agent workflow where specialized agents handle different aspects of processing user queries. Each agent is a node in the state machine with defined responsibilities and transitions.

## Agent Definitions

### 1. RouterAgent

**Purpose**: Classifies user intent and selects appropriate namespaces and downstream agents.

**Capabilities**:
- Intent classification using few-shot examples
- Namespace mapping based on keywords and context
- Confidence scoring for routing decisions
- Fallback to general namespace when uncertain

**Implementation**:

```python
from langchain.schema import BaseMessage
from typing import List, Dict, Any

class RouterAgent:
    def __init__(self, llm):
        self.llm = llm
        self.namespace_map = {
            "relationships": ["dating", "marriage", "family", "friendship", "love"],
            "money": ["investing", "savings", "wealth", "finance", "budget"],
            "business": ["entrepreneurship", "startup", "management", "leadership"],
            "feng_shui": ["energy", "space", "harmony", "arrangement", "chi"],
            "diet_food": ["nutrition", "eating", "health", "cooking", "meal"],
            "exercise_martial_arts": ["training", "fitness", "shaolin", "kungfu", "workout"],
            "meditation": ["mindfulness", "breathing", "zen", "peace", "calm"],
            "general": []  # Fallback
        }

    async def route(self, state: ConversationState) -> ConversationState:
        prompt = self._build_routing_prompt(state.user_message)
        response = await self.llm.ainvoke(prompt)

        # Parse intent and confidence
        intent, confidence = self._parse_response(response)

        # Map to namespaces
        namespaces = self._select_namespaces(intent, confidence)

        state.intent = intent
        state.confidence = confidence
        state.selected_namespaces = namespaces
        state.next_node = "librarian" if namespaces else "interpreter"

        return state

    def _build_routing_prompt(self, message: str) -> str:
        return f"""
        Classify the following user message into one or more categories:
        - relationships, money, business, feng_shui, diet_food, exercise_martial_arts, meditation, general

        Message: {message}

        Return format:
        Intent: <primary_intent>
        Confidence: <0.0-1.0>
        Categories: <comma_separated_list>
        """
```

**Routing Logic**:

```python
routing_rules = {
    "confidence_threshold": 0.7,
    "max_namespaces": 3,
    "fallback": "general",
    "multi_namespace_keywords": ["balance", "holistic", "life", "wellness"],
}
```

### 2. LibrarianAgent

**Purpose**: Performs hybrid retrieval from Qdrant vector database and manages reranking.

**Capabilities**:
- Vector similarity search across selected namespaces
- Optional keyword filtering
- Result reranking based on relevance
- Metadata extraction and formatting

**Implementation**:

```python
class LibrarianAgent:
    def __init__(self, qdrant_client, embedder, reranker=None):
        self.qdrant = qdrant_client
        self.embedder = embedder
        self.reranker = reranker

    async def retrieve(self, state: ConversationState) -> ConversationState:
        # Embed query
        query_vector = await self.embedder.aembed_query(state.user_message)

        # Search across namespaces
        all_chunks = []
        for namespace in state.selected_namespaces:
            results = await self.qdrant.search(
                collection_name=namespace,
                query_vector=query_vector,
                limit=5,
                score_threshold=0.7
            )
            all_chunks.extend(self._format_chunks(results))

        # Optional reranking
        if self.reranker and len(all_chunks) > 5:
            all_chunks = await self.reranker.rerank(
                query=state.user_message,
                documents=all_chunks,
                top_k=5
            )

        state.retrieved_chunks = all_chunks[:5]  # Top 5 final chunks
        state.next_node = "interpreter"

        return state

    def _format_chunks(self, results) -> List[Dict]:
        return [{
            "text": r.payload.get("content"),
            "score": r.score,
            "metadata": {
                "source_url": r.payload.get("source_url"),
                "source_title": r.payload.get("source_title"),
                "timestamp": r.payload.get("transcript_timestamp"),
                "tags": r.payload.get("tags", [])
            }
        } for r in results]
```

**Retrieval Parameters**:

```yaml
search:
  top_k: 5
  score_threshold: 0.7
  include_metadata: true
  use_mmr: false  # Maximal Marginal Relevance

reranking:
  enabled: false  # Enable in v0.2
  model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
  top_k: 3
```

### 3. InterpreterAgent

**Purpose**: Synthesizes retrieved context into a coherent answer in Herman's voice.

**Capabilities**:
- Context integration from multiple sources
- Citation formatting with timestamps
- Response generation in characteristic style
- Token streaming for real-time display

**Implementation**:

```python
class InterpreterAgent:
    def __init__(self, llm, streaming=True):
        self.llm = llm
        self.streaming = streaming

    async def interpret(self, state: ConversationState) -> ConversationState:
        # Build context from chunks
        context = self._build_context(state.retrieved_chunks)

        # Generate response
        prompt = self._build_interpretation_prompt(
            question=state.user_message,
            context=context
        )

        if self.streaming:
            response_tokens = []
            async for token in self.llm.astream(prompt):
                response_tokens.append(token)
                # Stream to client via callback
                await state.stream_callback(token)

            state.response_tokens = response_tokens
            state.final_response = "".join(response_tokens)
        else:
            response = await self.llm.ainvoke(prompt)
            state.final_response = response.content

        # Extract citations
        state.citations = self._extract_citations(state.retrieved_chunks)
        state.next_node = "safety"

        return state

    def _build_context(self, chunks: List[Dict]) -> str:
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            meta = chunk["metadata"]
            context_parts.append(
                f"[{i}] {chunk['text']}\n"
                f"Source: {meta['source_title']} "
                f"({meta.get('timestamp', 'N/A')})"
            )
        return "\n\n".join(context_parts)

    def _extract_citations(self, chunks: List[Dict]) -> List[Dict]:
        return [{
            "title": c["metadata"]["source_title"],
            "url": c["metadata"]["source_url"],
            "timestamp": c["metadata"].get("timestamp")
        } for c in chunks if c["metadata"].get("source_url")]
```

### 4. SafetyAgent

**Purpose**: Applies safety guardrails and ensures appropriate responses.

**Capabilities**:
- Content moderation
- Medical disclaimer injection
- Tone adjustment
- Response blocking for harmful content

**Implementation**:

```python
class SafetyAgent:
    def __init__(self, llm):
        self.llm = llm
        self.safety_rules = {
            "block_medical_diagnosis": True,
            "block_harmful_content": True,
            "add_disclaimers": True,
            "enforce_respectful_tone": True
        }

    async def check_safety(self, state: ConversationState) -> ConversationState:
        # Check for safety violations
        violations = await self._detect_violations(state.final_response)

        if violations.get("block_response"):
            state.final_response = self._get_safe_fallback(violations)
            state.safety_flags = ["blocked", violations.get("reason")]

        elif violations.get("needs_disclaimer"):
            disclaimer = self._get_disclaimer(violations.get("type"))
            state.final_response += f"\n\n{disclaimer}"
            state.safety_flags = ["disclaimer_added"]

        elif violations.get("tone_adjustment"):
            state.final_response = await self._adjust_tone(state.final_response)
            state.safety_flags = ["tone_adjusted"]

        state.next_node = None  # Terminal node
        state.status = "complete"

        return state

    def _get_disclaimer(self, violation_type: str) -> str:
        disclaimers = {
            "medical": "Note: This is not medical advice. Please consult healthcare professionals for medical concerns.",
            "financial": "Note: This is educational content only, not financial advice. Consult qualified advisors for financial decisions.",
            "legal": "Note: This is general information, not legal advice. Consult an attorney for legal matters."
        }
        return disclaimers.get(violation_type, "")
```

### 5. AdminAgent (Offline)

**Purpose**: Validates and processes documents for ingestion into Qdrant.

**Capabilities**:
- Document validation
- Metadata extraction and validation
- Chunking policy enforcement
- Quality checks

**Implementation**:

```python
class AdminAgent:
    def __init__(self, parser, chunker, embedder, qdrant_client):
        self.parser = parser
        self.chunker = chunker
        self.embedder = embedder
        self.qdrant = qdrant_client

    async def process_document(self, file_path: str, namespace: str) -> Dict:
        # Validate file
        validation = await self._validate_document(file_path)
        if not validation["valid"]:
            return {"error": validation["reason"]}

        # Parse document
        content = await self.parser.parse(file_path)

        # Extract/validate metadata
        metadata = await self._extract_metadata(content, file_path)

        # Chunk content
        chunks = await self.chunker.chunk(
            content,
            chunk_size=1500,
            overlap=200
        )

        # Generate embeddings
        embeddings = await self.embedder.aembed_documents(
            [c["text"] for c in chunks]
        )

        # Prepare for Qdrant
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            points.append({
                "id": str(uuid4()),
                "vector": embedding,
                "payload": {
                    **metadata,
                    "content": chunk["text"],
                    "chunk_index": chunk["index"],
                    "checksum": hashlib.md5(chunk["text"].encode()).hexdigest()
                }
            })

        # Upsert to Qdrant
        await self.qdrant.upsert(
            collection_name=namespace,
            points=points
        )

        return {
            "success": True,
            "chunks_created": len(points),
            "namespace": namespace
        }
```

## LangGraph State Machine Definition

```python
from langgraph.graph import StateGraph, END

def build_conversation_graph():
    # Initialize graph
    graph = StateGraph(ConversationState)

    # Add nodes
    graph.add_node("router", router_agent.route)
    graph.add_node("librarian", librarian_agent.retrieve)
    graph.add_node("interpreter", interpreter_agent.interpret)
    graph.add_node("safety", safety_agent.check_safety)

    # Add edges
    graph.add_edge("router", "librarian")
    graph.add_edge("router", "interpreter")  # Direct route if no RAG needed
    graph.add_edge("librarian", "interpreter")
    graph.add_edge("interpreter", "safety")
    graph.add_edge("safety", END)

    # Set entry point
    graph.set_entry_point("router")

    # Compile
    return graph.compile()
```

## Error Handling

### Agent-Level Error Handling

```python
class AgentError(Exception):
    """Base exception for agent errors"""
    pass

class RoutingError(AgentError):
    """Failed to route message"""
    pass

class RetrievalError(AgentError):
    """Failed to retrieve context"""
    pass

class GenerationError(AgentError):
    """Failed to generate response"""
    pass

async def handle_agent_error(state: ConversationState, error: Exception):
    if isinstance(error, RoutingError):
        # Fallback to general namespace
        state.selected_namespaces = ["general"]
        state.error = f"Routing failed, using general knowledge"

    elif isinstance(error, RetrievalError):
        # Continue without context
        state.retrieved_chunks = []
        state.error = f"Context retrieval failed, answering without sources"

    elif isinstance(error, GenerationError):
        # Return safe error message
        state.final_response = "I apologize, but I'm having trouble generating a response. Please try again."
        state.status = "error"

    return state
```

### Circuit Breaker Pattern

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure = None
        self.state = "closed"  # closed, open, half-open

    async def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure > self.timeout:
                self.state = "half-open"
            else:
                raise CircuitBreakerOpen()

        try:
            result = await func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failures = 0
            return result

        except Exception as e:
            self.failures += 1
            self.last_failure = time.time()

            if self.failures >= self.failure_threshold:
                self.state = "open"

            raise e
```

## Agent Communication Protocol

### Message Format

```python
from pydantic import BaseModel
from typing import Any, Optional

class AgentMessage(BaseModel):
    agent_id: str
    timestamp: datetime
    message_type: Literal["request", "response", "error", "status"]
    payload: Dict[str, Any]
    correlation_id: str
    metadata: Optional[Dict[str, Any]] = {}
```

### Inter-Agent Communication

```python
class AgentBus:
    def __init__(self):
        self.subscribers = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable):
        self.subscribers[event_type].append(handler)

    async def publish(self, event_type: str, message: AgentMessage):
        for handler in self.subscribers[event_type]:
            await handler(message)

    async def request_response(
        self,
        target_agent: str,
        payload: Dict,
        timeout: float = 30
    ) -> AgentMessage:
        correlation_id = str(uuid4())
        request = AgentMessage(
            agent_id="caller",
            timestamp=datetime.now(),
            message_type="request",
            payload=payload,
            correlation_id=correlation_id
        )

        # Send request and wait for response
        future = asyncio.Future()
        self.subscribe(f"response:{correlation_id}", future.set_result)

        await self.publish(f"request:{target_agent}", request)

        return await asyncio.wait_for(future, timeout=timeout)
```

## Testing Strategies

### Unit Tests

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_router_agent_classification():
    # Mock LLM
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value.content = """
    Intent: financial_advice
    Confidence: 0.85
    Categories: money, business
    """

    # Initialize agent
    router = RouterAgent(mock_llm)

    # Test state
    state = ConversationState(
        user_message="How should I invest my savings?"
    )

    # Execute
    result = await router.route(state)

    # Assert
    assert result.intent == "financial_advice"
    assert result.confidence == 0.85
    assert "money" in result.selected_namespaces
    assert "business" in result.selected_namespaces
```

### Integration Tests

```python
@pytest.mark.integration
async def test_full_conversation_flow():
    # Build graph
    graph = build_conversation_graph()

    # Input state
    initial_state = ConversationState(
        user_id="test_user",
        session_id="test_session",
        user_message="What does Herman say about meditation?",
        timestamp=datetime.now()
    )

    # Execute graph
    final_state = await graph.ainvoke(initial_state)

    # Assertions
    assert final_state.status == "complete"
    assert final_state.final_response is not None
    assert len(final_state.citations) >= 2  # At least 2 sources
    assert final_state.selected_namespaces == ["meditation"]
```

## Performance Benchmarks

### Agent Latency Targets

| Agent | p50 | p95 | p99 |
|-------|-----|-----|-----|
| RouterAgent | 200ms | 500ms | 1s |
| LibrarianAgent | 500ms | 1s | 2s |
| InterpreterAgent | 2s | 5s | 8s |
| SafetyAgent | 100ms | 200ms | 500ms |

### Optimization Strategies

1. **Parallel Processing**: Run independent agents concurrently
2. **Caching**: Cache routing decisions and frequent retrievals
3. **Batching**: Batch embedding requests
4. **Model Selection**: Use smaller models for classification
5. **Streaming**: Stream tokens as generated

## Acceptance Criteria

- ✅ Router correctly classifies 80%+ of test queries
- ✅ Librarian retrieves relevant chunks with score > 0.7
- ✅ Interpreter includes citations in response
- ✅ Safety agent blocks harmful content
- ✅ End-to-end latency < 5s (p50)
- ✅ All agents handle errors gracefully
- ✅ State transitions logged for debugging