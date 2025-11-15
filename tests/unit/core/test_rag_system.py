"""Tests for RAG system."""

import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from quantchain.core.rag_system import (
    ChromaVectorStore,
    EmbeddingProvider,
    MarketData,
    MarketDataRAG,
    SentenceTransformerProvider,
    VectorStore,
)


class TestMarketData:
    """Test MarketData dataclass."""



def test_market_data_creation(self) -> None:
        """Test creating MarketData."""
        timestamp = datetime.now()
        data = MarketData(
            symbol="AAPL",
            timestamp=timestamp,
            data_type="price",
            content={"price": 150.0},
            embedding=[0.1, 0.2, 0.3],
        )
        assert data.symbol == "AAPL"
        assert data.timestamp == timestamp
        assert data.data_type == "price"
        assert data.content == {"price": 150.0}
        assert data.embedding == [0.1, 0.2, 0.3]



def test_market_data_defaults(self) -> None:
        """Test MarketData with defaults."""
        timestamp = datetime.now()
        data = MarketData(
            symbol="AAPL",
            timestamp=timestamp,
            data_type="price",
            content={"price": 150.0},
        )
        assert data.embedding is None


class TestChromaVectorStore:
    """Test ChromaDB vector store."""

    @patch("quantchain.core.rag_system.chromadb")


def test_chroma_store_init_success(self, mock_chromadb) -> None:
        """Test successful ChromaVectorStore initialization."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        store = ChromaVectorStore()

        # The constructor converts relative path to absolute path
        expected_path = os.path.abspath("./data/chroma_db")
        mock_chromadb.PersistentClient.assert_called_once_with(path=expected_path)
        mock_client.get_or_create_collection.assert_called_once_with("market_data")
        assert store.collection == mock_collection



def test_chroma_store_init_import_error(self) -> None:
        """Test ChromaVectorStore initialization with import error."""
        with patch("quantchain.core.rag_system.chromadb", None):
            with pytest.raises(ImportError):
                ChromaVectorStore()

    @patch("quantchain.core.rag_system.chromadb")


def test_chroma_store_store(self, mock_chromadb) -> None:
        """Test storing data in ChromaVectorStore."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        store = ChromaVectorStore()
        timestamp = datetime.now()
        data = MarketData(
            symbol="AAPL",
            timestamp=timestamp,
            data_type="price",
            content={"price": 150.0},
        )
        embedding: list = [0.1, 0.2, 0.3]

        data_id = store.store(data, embedding)

        assert data_id.startswith("AAPL_")
        assert timestamp.isoformat() in data_id
        assert "price" in data_id

        # Check that add was called
        mock_collection.add.assert_called_once()
        call_args = mock_collection.add.call_args
        assert "ids" in call_args[1]
        assert "embeddings" in call_args[1]
        assert "metadatas" in call_args[1]

    @patch("quantchain.core.rag_system.chromadb")


def test_chroma_store_search(self, mock_chromadb) -> None:
        """Test searching in ChromaVectorStore."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        # Mock query response
        mock_results = {
            "metadatas": [
                [
                    {
                        "symbol": "AAPL",
                        "timestamp": "2023-01-01T00:00:00",
                        "data_type": "price",
                        "content": '{"price": 150.0}',
                    }
                ]
            ],
            "embeddings": [[[0.1, 0.2, 0.3]]],
        }
        mock_collection.query.return_value = mock_results

        store = ChromaVectorStore()
        results = store.search([0.1, 0.2, 0.3], limit=5)

        assert len(results) == 1
        assert results[0].symbol == "AAPL"
        assert results[0].data_type == "price"
        assert results[0].content == {"price": 150.0}

    @patch("quantchain.core.rag_system.chromadb")


def test_chroma_store_delete(self, mock_chromadb) -> None:
        """Test deleting data from ChromaVectorStore."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        store = ChromaVectorStore()

        # Test successful delete
        mock_collection.delete.return_value = None
        result = store.delete("test_id")
        assert result is True
        mock_collection.delete.assert_called_once_with(ids=["test_id"])

        # Test failed delete
        mock_collection.delete.side_effect = Exception("Delete failed")
        result = store.delete("test_id")
        assert result is False


class TestSentenceTransformerProvider:
    """Test SentenceTransformer embedding provider."""

    @patch("quantchain.core.rag_system.SentenceTransformer")


def test_sentence_transformer_init_success(self, mock_transformer) -> None:
        """Test successful SentenceTransformerProvider initialization."""
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model

        provider = SentenceTransformerProvider()

        mock_transformer.assert_called_once_with("all-MiniLM-L6-v2")
        assert provider.model == mock_model



def test_sentence_transformer_init_import_error(self) -> None:
        """Test SentenceTransformerProvider initialization with import error."""
        with patch("quantchain.core.rag_system.SentenceTransformer", None):
            with pytest.raises(ImportError):
                SentenceTransformerProvider()

    @patch("quantchain.core.rag_system.SentenceTransformer")


def test_sentence_transformer_encode(self, mock_transformer) -> None:
        """Test encoding text with SentenceTransformerProvider."""
        mock_model = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value: list = [0.1, 0.2, 0.3]
        mock_model.encode.return_value = mock_embedding
        mock_transformer.return_value = mock_model

        provider = SentenceTransformerProvider()
        result = provider.encode("test text")

        assert result == [0.1, 0.2, 0.3]
        mock_model.encode.assert_called_once_with("test text")


class TestMarketDataRAG:
    """Test MarketDataRAG system."""

    @pytest.fixture


def mock_vector_store(self) -> None:
        """Mock vector store."""
        return MagicMock(spec=VectorStore)

    @pytest.fixture


def mock_embedding_provider(self) -> None:
        """Mock embedding provider."""
        provider = MagicMock(spec=EmbeddingProvider)
        provider.encode.return_value: list = [0.1, 0.2, 0.3]
        return provider



def test_rag_init(self, mock_vector_store, mock_embedding_provider) -> None:
        """Test MarketDataRAG initialization."""
        rag = MarketDataRAG(mock_vector_store, mock_embedding_provider)

        assert rag.vector_store == mock_vector_store
        assert rag.embedding_provider == mock_embedding_provider



def test_store_market_data(
        self, mock_vector_store, mock_embedding_provider
    ) -> None:
        """Test storing market data."""
        rag = MarketDataRAG(mock_vector_store, mock_embedding_provider)

        timestamp = datetime.now()
        data = MarketData(
            symbol="AAPL",
            timestamp=timestamp,
            data_type="price",
            content={"price": 150.0},
        )

        mock_vector_store.store.return_value = "test_id"

        data_id = rag.store_market_data(data)

        assert data_id == "test_id"
        assert data.embedding == [0.1, 0.2, 0.3]
        mock_embedding_provider.encode.assert_called_once()
        mock_vector_store.store.assert_called_once_with(data, [0.1, 0.2, 0.3])



def test_retrieve_relevant_data(
        self, mock_vector_store, mock_embedding_provider
    ) -> None:
        """Test retrieving relevant data."""
        rag = MarketDataRAG(mock_vector_store, mock_embedding_provider)

        mock_data = MagicMock(spec=MarketData)
        mock_vector_store.search.return_value: list = [mock_data]

        results = rag.retrieve_relevant_data("test query")

        assert results == [mock_data]
        mock_embedding_provider.encode.assert_called_once_with("test query")
        mock_vector_store.search.assert_called_once_with([0.1, 0.2, 0.3], 5)



def test_generate_augmented_prompt(
        self, mock_vector_store, mock_embedding_provider
    ) -> None:
        """Test generating augmented prompt."""
        rag = MarketDataRAG(mock_vector_store, mock_embedding_provider)

        mock_data = MagicMock(spec=MarketData)
        mock_data.symbol = "AAPL"
        mock_data.data_type = "price"
        mock_data.timestamp = datetime.now()
        mock_data.content = {"price": 150.0}

        mock_vector_store.search.return_value: list = [mock_data]

        prompt = rag.generate_augmented_prompt("Analyze market", "AAPL price")

        assert "Analyze market" in prompt
        assert "Relevant Market Data:" in prompt
        assert "AAPL" in prompt
        assert "price" in prompt



def test_generate_augmented_prompt_no_data(
        self, mock_vector_store, mock_embedding_provider
    ) -> None:
        """Test generating augmented prompt with no relevant data."""
        rag = MarketDataRAG(mock_vector_store, mock_embedding_provider)

        mock_vector_store.search.return_value: list = []

        prompt = rag.generate_augmented_prompt("Analyze market", "AAPL price")

        assert prompt == "Analyze market"



def test_market_data_to_text(
        self, mock_vector_store, mock_embedding_provider
    ) -> None:
        """Test converting market data to text."""
        rag = MarketDataRAG(mock_vector_store, mock_embedding_provider)

        timestamp = datetime.now()
        data = MarketData(
            symbol="AAPL",
            timestamp=timestamp,
            data_type="price",
            content={"price": 150.0},
        )

        text = rag._market_data_to_text(data)

        assert "AAPL" in text
        assert "price" in text
        assert '{"price": 150.0}' in text
        assert timestamp.isoformat() in text
