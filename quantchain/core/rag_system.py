"""RAG system for market data caching and retrieval."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass
import json
import os
from datetime import datetime
import numpy as np

if TYPE_CHECKING:
    import chromadb

try:
    import chromadb  # noqa: F811
except ImportError:
    chromadb = None  # type: ignore[assignment,misc]

try:
    from sentence_transformers import SentenceTransformer  # noqa: F811
except (ImportError, RuntimeError):
    # Handle RuntimeError from torch conflicts
    SentenceTransformer = None  # type: ignore[assignment,misc]


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
        # Convert relative path to absolute path to avoid Windows path issues
        if not os.path.isabs(persist_directory):
            persist_directory = os.path.abspath(persist_directory)
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection("market_data")

    def store(self, data: MarketData, embedding: List[float]) -> str:
        import hashlib

        content_str = json.dumps(data.content, sort_keys=True)
        hash_input = (
            f"{data.symbol}_{data.timestamp.isoformat()}_{data.data_type}_{content_str}"
        )
        unique_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:16]
        data_id = (
            f"{data.symbol}_{data.timestamp.isoformat()}_{data.data_type}_{unique_hash}"
        )
        metadata = {
            "symbol": data.symbol,
            "timestamp": data.timestamp.isoformat(),
            "data_type": data.data_type,
            "content": content_str,
        }
        self.collection.add(  # noqa: E501
            ids=[data_id], embeddings=[np.array(embedding)], metadatas=[metadata]
        )
        return data_id

    def search(self, query_embedding: List[float], limit: int = 10) -> List[MarketData]:
        from typing import cast

        results = self.collection.query(  # noqa: E501
            query_embeddings=[np.array(query_embedding)], n_results=limit
        )

        market_data: List[MarketData] = []
        if (
            not results.get("metadatas")
            or not results["metadatas"]
            or not results["metadatas"][0]
        ):
            return market_data

        metadatas = results["metadatas"][0]
        embeddings_result = results.get("embeddings")
        embedding_list = (
            embeddings_result[0] if embeddings_result and embeddings_result[0] else []
        )

        for i, metadata in enumerate(metadatas):
            content_str = cast(str, metadata.get("content", "{}"))
            content = json.loads(content_str)
            embedding = None
            if i < len(embedding_list) and embedding_list[i] is not None:
                embedding = list(embedding_list[i])
            market_data.append(
                MarketData(
                    symbol=cast(str, metadata.get("symbol", "")),
                    timestamp=datetime.fromisoformat(
                        cast(str, metadata.get("timestamp", ""))
                    ),
                    data_type=cast(str, metadata.get("data_type", "")),
                    content=content,
                    embedding=embedding,
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
        return list(self.model.encode(text).tolist())


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
            context_parts.extend(
                [
                    f"Symbol: {data.symbol}",
                    f"Type: {data.data_type}",
                    f"Time: {data.timestamp.isoformat()}",
                    f"Data: {json.dumps(data.content, indent=2)}",
                    "---",
                ]
            )

        context = "\n".join(context_parts)
        return f"{base_prompt}\n\nRelevant Market Data:\n{context}\n\nQuery: {query}"

    def _market_data_to_text(self, data: MarketData) -> str:
        """Convert market data to text for embedding."""
        content_str = json.dumps(data.content)
        timestamp_str = data.timestamp.isoformat()
        return f"{data.symbol} {data.data_type} {content_str} {timestamp_str}"
