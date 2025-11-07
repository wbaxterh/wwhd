# RAG (Retrieval-Augmented Generation)

## Qdrant Configuration

### Collections Structure

Each namespace maps to a Qdrant collection with consistent schema:

```yaml
collections:
  - name: general
  - name: relationships
  - name: money
  - name: business
  - name: feng_shui
  - name: diet_food
  - name: exercise_martial_arts
  - name: meditation

config:
  vector_size: 1536  # OpenAI text-embedding-3-small
  distance: cosine
  on_disk_payload: false
  quantization:
    scalar:
      type: int8
      quantile: 0.99
      always_ram: true
```

### Alternative Embedding Configurations

```yaml
openai_large:
  model: text-embedding-3-large
  dimensions: 3072
  cost: $0.13/1M tokens

openai_small:
  model: text-embedding-3-small
  dimensions: 1536
  cost: $0.02/1M tokens

openrouter:
  model: voyage/voyage-lite-02-instruct
  dimensions: 1024
  cost: $0.002/1M tokens
```

## Document Schema

### Payload Structure

```json
{
  "content": "The actual text content of the chunk",
  "chunk_index": 0,
  "total_chunks": 5,
  "source_url": "https://youtube.com/watch?v=...",
  "source_title": "Herman Siu on Building Wealth",
  "source_platform": "youtube",
  "source_author": "Herman Siu",
  "source_published_at": "2024-01-15T10:30:00Z",
  "transcript_timestamp": "00:12:45",
  "tags": ["investing", "real-estate", "passive-income"],
  "checksum": "md5_hash_of_content",
  "ingestion_time": "2024-01-20T15:30:00Z",
  "license_notes": "CC BY 4.0",
  "chunk_metadata": {
    "char_start": 1000,
    "char_end": 2500,
    "token_count": 350,
    "overlap_prev": 200,
    "overlap_next": 200
  }
}
```

## Chunking Policy

### Parameters

```python
CHUNKING_CONFIG = {
    "method": "recursive_character",
    "chunk_size": 1500,  # characters
    "chunk_overlap": 200,
    "separators": ["\n\n", "\n", ". ", " "],
    "keep_separator": True,
    "strip_whitespace": True,
    "min_chunk_size": 100,
    "max_chunk_size": 2000
}
```

### Chunking Strategy by Content Type

| Content Type | Strategy | Chunk Size | Overlap |
|-------------|----------|------------|----------|
| Transcript | Timestamp-aware | 1500 chars | 200 chars |
| Article | Paragraph-based | 1500 chars | 200 chars |
| PDF | Page-aware | 1500 chars | 200 chars |
| Social Media | Post-based | Full post | None |
| Q&A | Question-Answer pairs | Full pair | None |

### Implementation

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict
import re

class ContentChunker:
    def __init__(self, config: Dict = CHUNKING_CONFIG):
        self.config = config
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config["chunk_size"],
            chunk_overlap=config["chunk_overlap"],
            separators=config["separators"],
            keep_separator=config["keep_separator"]
        )

    def chunk_transcript(self, content: str, timestamps: List[str]) -> List[Dict]:
        """Special handling for timestamped content"""
        chunks = []
        current_chunk = ""
        current_timestamp = "00:00:00"

        for line in content.split('\n'):
            # Extract timestamp if present
            timestamp_match = re.match(r'^(\d{2}:\d{2}:\d{2})', line)
            if timestamp_match:
                current_timestamp = timestamp_match.group(1)
                line = line[len(current_timestamp):].strip()

            if len(current_chunk) + len(line) > self.config["chunk_size"]:
                chunks.append({
                    "text": current_chunk.strip(),
                    "timestamp": current_timestamp,
                    "index": len(chunks)
                })
                # Keep overlap
                overlap_text = current_chunk[-self.config["chunk_overlap"]:]
                current_chunk = overlap_text + " " + line
            else:
                current_chunk += " " + line

        # Add remaining chunk
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "timestamp": current_timestamp,
                "index": len(chunks)
            })

        return chunks

    def chunk_document(self, content: str) -> List[Dict]:
        """Standard document chunking"""
        text_chunks = self.splitter.split_text(content)
        return [
            {
                "text": chunk,
                "index": i,
                "char_start": sum(len(c) for c in text_chunks[:i]),
                "char_end": sum(len(c) for c in text_chunks[:i+1])
            }
            for i, chunk in enumerate(text_chunks)
        ]
```

## Retrieval Configuration

### Search Parameters

```yaml
default:
  limit: 10  # Retrieve more, then rerank
  score_threshold: 0.7
  with_payload: true
  with_vectors: false

advanced:
  use_mmr: false  # Maximal Marginal Relevance
  mmr_lambda: 0.5
  filter_duplicates: true
  duplicate_threshold: 0.95
```

### Hybrid Search Configuration

```python
HYBRID_SEARCH_CONFIG = {
    "alpha": 0.7,  # 0.7 vector, 0.3 keyword
    "keyword_boost": {
        "title_match": 2.0,
        "tag_match": 1.5,
        "exact_phrase": 3.0
    }
}
```

## Reranking Strategy

### Cross-Encoder Reranking

```python
from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
        # Prepare pairs
        pairs = [(query, doc["text"]) for doc in documents]

        # Get scores
        scores = self.model.predict(pairs)

        # Sort by score
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Return top-k with scores
        return [
            {**doc, "rerank_score": float(score)}
            for doc, score in scored_docs[:top_k]
        ]
```

## Citation Format

### Response Template

```markdown
[Main response content here...]

**Sources:**
1. [Title](URL) - Platform (timestamp if available)
2. [Title](URL) - Platform (timestamp if available)
```

### Citation Extraction

```python
def format_citations(chunks: List[Dict]) -> str:
    citations = []
    seen_urls = set()

    for chunk in chunks:
        url = chunk["metadata"].get("source_url")
        if url and url not in seen_urls:
            seen_urls.add(url)

            title = chunk["metadata"].get("source_title", "Untitled")
            platform = chunk["metadata"].get("source_platform", "")
            timestamp = chunk["metadata"].get("transcript_timestamp", "")

            if timestamp:
                citation = f"[{title}]({url}) - {platform} (@{timestamp})"
            else:
                citation = f"[{title}]({url}) - {platform}"

            citations.append(citation)

    if not citations:
        return ""

    return "\n\n**Sources:**\n" + "\n".join(
        f"{i+1}. {cite}" for i, cite in enumerate(citations[:5])
    )
```

## Quality Metrics

### Retrieval Quality

```python
class RetrievalMetrics:
    @staticmethod
    def precision_at_k(relevant: List[str], retrieved: List[str], k: int) -> float:
        """Fraction of retrieved docs that are relevant"""
        retrieved_k = retrieved[:k]
        relevant_retrieved = len(set(retrieved_k) & set(relevant))
        return relevant_retrieved / k if k > 0 else 0

    @staticmethod
    def recall_at_k(relevant: List[str], retrieved: List[str], k: int) -> float:
        """Fraction of relevant docs that are retrieved"""
        retrieved_k = retrieved[:k]
        relevant_retrieved = len(set(retrieved_k) & set(relevant))
        return relevant_retrieved / len(relevant) if relevant else 0

    @staticmethod
    def mrr(relevant: List[str], retrieved: List[str]) -> float:
        """Mean Reciprocal Rank"""
        for i, doc_id in enumerate(retrieved):
            if doc_id in relevant:
                return 1.0 / (i + 1)
        return 0.0
```

## Index Management

### Collection Operations

```python
class QdrantManager:
    def __init__(self, client: QdrantClient):
        self.client = client

    async def create_collection(self, name: str, vector_size: int = 1536):
        await self.client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )

    async def create_indexes(self, collection: str):
        # Create payload indexes for filtering
        await self.client.create_payload_index(
            collection_name=collection,
            field_name="source_platform",
            field_type="keyword"
        )

        await self.client.create_payload_index(
            collection_name=collection,
            field_name="tags",
            field_type="keyword[]"
        )

    async def optimize_collection(self, collection: str):
        await self.client.update_collection(
            collection_name=collection,
            optimizer_config=OptimizersConfigDiff(
                indexing_threshold=20000,
                memmap_threshold=50000
            )
        )
```

## Namespace Routing Rules

```yaml
routing_keywords:
  relationships:
    primary: [dating, marriage, divorce, family, friendship]
    secondary: [love, trust, communication, conflict, boundaries]

  money:
    primary: [investing, savings, wealth, finance, budget]
    secondary: [stocks, real estate, passive income, retirement]

  business:
    primary: [entrepreneurship, startup, management, leadership]
    secondary: [strategy, marketing, sales, operations, scaling]

  feng_shui:
    primary: [energy, chi, bagua, elements, harmony]
    secondary: [placement, colors, directions, balance, flow]

  diet_food:
    primary: [nutrition, diet, recipes, health, wellness]
    secondary: [organic, supplements, meal prep, fasting]

  exercise_martial_arts:
    primary: [training, shaolin, kungfu, fitness, workout]
    secondary: [forms, meditation, discipline, strength, flexibility]

  meditation:
    primary: [mindfulness, breathing, zen, consciousness]
    secondary: [relaxation, focus, awareness, peace, calm]
```

## Acceptance Criteria

- ✅ Chunks maintain context with 200-char overlap
- ✅ Vector search returns results with score > 0.7
- ✅ Citations include source URL and timestamp when available
- ✅ Retrieval latency < 500ms for 5 chunks
- ✅ Deduplication prevents showing same source twice
- ✅ Minimum 2 sources cited by default
- ✅ Metadata properly indexed for filtering
- ✅ Checksums prevent duplicate content ingestion