"""RAG system for market data caching and retrieval."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
from datetime import datetime

try:
    import chromadb
except ImportError:
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


@dataclass
class MarketData:
    """Market data entry for RAG."""

    symbol: str
    timestamp: datetime
    data_type: str  # 'price', 'news', 'technical'
    content: Dict[str, Any]
    embedding: Optional[List[float]] = None


class VectorStore(ABC):
    """Abstract vector store interface."""

    @abstractmethod
    def store(self, data: MarketData, embedding: List[float]) -> str:
        """Store data with embedding, return ID."""
        pass

    @abstractmethod
    def search(self, query_embedding: List[float], limit: int = 10) -> List[MarketData]:
        """Search for similar data."""
        pass

    @abstractmethod
    def delete(self, data_id: str) -> bool:
        """Delete data by ID."""
        pass


class ChromaVectorStore(VectorStore):
    """ChromaDB implementation of vector store."""

    def __init__(self, persist_directory: str = "./data/chroma_db"):
        if chromadb is None:
            raise ImportError("chromadb package not installed")
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection("market_data")

    def store(self, data: MarketData, embedding: List[float]) -> str:
        data_id = f"{data.symbol}_{data.timestamp.isoformat()}_{data.data_type}"
        metadata = {
            "symbol": data.symbol,
            "timestamp": data.timestamp.isoformat(),
            "data_type": data.data_type,
            "content": json.dumps(data.content),
        }
        self.collection.add(ids=[data_id], embeddings=[embedding], metadatas=[metadata])
        return data_id

    def search(self, query_embedding: List[float], limit: int = 10) -> List[MarketData]:
        results = self.collection.query(
            query_embeddings=[query_embedding], n_results=limit
        )

        market_data = []
        for i, metadata in enumerate(results["metadatas"][0]):
            content = json.loads(metadata["content"])
            market_data.append(
                MarketData(
                    symbol=metadata["symbol"],
                    timestamp=datetime.fromisoformat(metadata["timestamp"]),
                    data_type=metadata["data_type"],
                    content=content,
                    embedding=(
                        results["embeddings"][0][i] if results["embeddings"] else None
                    ),
                )
            )
        return market_data

    def delete(self, data_id: str) -> bool:
        try:
            self.collection.delete(ids=[data_id])
            return True
        except Exception:
            return False


class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    @abstractmethod
    def encode(self, text: str) -> List[float]:
        """Generate embedding for text."""
        pass


class SentenceTransformerProvider(EmbeddingProvider):
    """SentenceTransformer embedding provider."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers package not installed")
        self.model = SentenceTransformer(model_name)

    def encode(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()


class MarketDataRAG:
    """RAG system for market data."""

    def __init__(
        self, vector_store: VectorStore, embedding_provider: EmbeddingProvider
    ):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider

    def store_market_data(self, data: MarketData) -> str:
        """Store market data with generated embedding."""
        # Create text representation for embedding
        text_content = self._market_data_to_text(data)
        embedding = self.embedding_provider.encode(text_content)
        data.embedding = embedding
        return self.vector_store.store(data, embedding)

    def retrieve_relevant_data(self, query: str, limit: int = 5) -> List[MarketData]:
        """Retrieve relevant market data for a query."""
        query_embedding = self.embedding_provider.encode(query)
        return self.vector_store.search(query_embedding, limit)

    def generate_augmented_prompt(self, base_prompt: str, query: str) -> str:
        """Generate RAG-augmented prompt."""
        relevant_data = self.retrieve_relevant_data(query)

        if not relevant_data:
            return base_prompt

        context_parts = []
        for data in relevant_data:
            context_parts.append(f"Symbol: {data.symbol}")
            context_parts.append(f"Type: {data.data_type}")
            context_parts.append(f"Time: {data.timestamp.isoformat()}")
            context_parts.append(f"Data: {json.dumps(data.content, indent=2)}")
            context_parts.append("---")

        context = "\n".join(context_parts)
        return f"{base_prompt}\n\nRelevant Market Data:\n{context}\n\nQuery: {query}"

    def _market_data_to_text(self, data: MarketData) -> str:
        """Convert market data to text for embedding."""
        content_str = json.dumps(data.content)
        timestamp_str = data.timestamp.isoformat()
        return f"{data.symbol} {data.data_type} {content_str} {timestamp_str}"
