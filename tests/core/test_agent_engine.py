"""Tests for the core agent engine."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from quantchain.core.agent_engine import QuantChainAgent, AgentResponse
from quantchain.core.config import QuantChainConfig
from quantchain.core.llm_providers import LLMProvider, LLMResponse
from quantchain.core.reflection import AgentAction


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, responses=None) -> None:
        self.responses = responses or ["Final answer: test response"]
        self.call_count = 0

    def generate(self, prompt, **kwargs) -> None:
        response = self.responses[min(self.call_count, len(self.responses) - 1)]
        self.call_count += 1
        return LLMResponse(text=response, usage={"tokens": 10})

    def get_model_name(self) -> None:
        return "mock-model"


@pytest.fixture
def mock_config() -> None:
    """Mock configuration for testing."""
    config = MagicMock(spec=QuantChainConfig)

    def config_get(key, default=None) -> None:
        """Return appropriate mock values based on key."""
        mock_values = {
            "max_iterations": 5,
            "llm": {"provider": "mock", "model": "mock-model"},
            "rag": {"enabled": False},  # Return dict for rag config
        }
        return mock_values.get(key, default)

    config.get.side_effect = config_get
    config.get_api_key.return_value = None
    return config


@pytest.fixture
def mock_llm_provider() -> None:
    """Mock LLM provider."""
    return MockLLMProvider()


@pytest.mark.unit
class TestQuantChainAgentEngine:

    def test_agent_initialization_with_mock(
        self, mock_config, mock_llm_provider
    ) -> None:
        """Test agent initialization."""

    # Mock graph compilation
    mock_graph.compile.return_value = final_state
    mock_graph = MagicMock()
    # Mock graph compilation
    mock_graph.compile.return_value = final_state

    agent = QuantChainAgent(mock_config, llm_provider=mock_llm_provider)

    assert agent.config == mock_config
    assert agent.llm_provider == mock_llm_provider
    assert agent.graph == mock_graph


@patch("quantchain.core.agent_engine.StateGraph")
def test_agent_run(mock_state_graph, mock_config, mock_llm_provider) -> None:
    """Test agent execution."""
    # Setup mock graph
    mock_graph = MagicMock()
    final_state = {
        "final_answer": "Test final answer",
        "reasoning_steps": ["Step 1", "Step 2"],
        "confidence_score": 0.8,
        "actions": [
            AgentAction(
                timestamp=datetime.now(),
                action_type="test_action",
                parameters={},
                result="success",
                confidence_score=0.8,
                success=True,
            )
        ],
    }
    mock_graph.invoke.return_value = final_state
    # Mock graph compilation
    mock_graph.compile.return_value = final_state

    agent = QuantChainAgent(mock_config, llm_provider=mock_llm_provider)

    input_data = {"query": "test query"}
    response = agent.run(input_data)

    assert isinstance(response, AgentResponse)
    assert response.final_answer == "Test final answer"
    assert len(response.reasoning_steps) == 2
    assert response.confidence_score == 0.8
    assert len(response.actions_taken) == 1


@patch("quantchain.core.agent_engine.StateGraph")
def test_agent_reflection(mock_state_graph, mock_config, mock_llm_provider) -> None:
    """Test agent reflection capability."""
    mock_graph = MagicMock()
    # Mock graph compilation
    mock_graph.compile.return_value = final_state

    agent = QuantChainAgent(mock_config, llm_provider=mock_llm_provider)

    # Add some actions to reflection engine
    action = AgentAction(
        timestamp=datetime.now(),
        action_type="test",
        parameters={},
        result="success",
        confidence_score=0.9,
        success=True,
        reward=10.0,
    )
    agent.reflection_engine.record_action(action)

    report = agent.reflect()

    assert report is not None
    assert report.metrics.total_actions == 1
    assert report.metrics.successful_actions == 1
    assert len(report.insights) > 0


@patch("quantchain.core.agent_engine.StateGraph")
def test_extract_final_answer(mock_state_graph, mock_config) -> None:
    """Test final answer extraction."""
    mock_graph = MagicMock()
    # Mock graph compilation
    mock_graph.compile.return_value = final_state
    agent = QuantChainAgent(mock_config, llm_provider=MockLLMProvider())

    reasoning = "After analysis, the final answer: buy AAPL"
    answer = agent._extract_final_answer(reasoning)
    assert answer == "buy AAPL"

    reasoning_no_final = "This is just reasoning without final answer"
    answer = agent._extract_final_answer(reasoning_no_final)
    assert answer == reasoning_no_final.strip()

    # Test with multiple 'final answer:' instances
    reasoning_multiple = (
        "Step 1: Consider options. Final answer: hold TSLA. "
        "Step 2: Re-evaluate. Final answer: sell TSLA"
    )
    answer = agent._extract_final_answer(reasoning_multiple)
    # Assuming extraction gets the last 'final answer:' value
    assert answer == "sell TSLA"

    # Test with atypical formatting (extra spaces, case differences)
    reasoning_atypical = "Analysis complete. FINAL ANSWER:   buy GOOG  "
    answer = agent._extract_final_answer(reasoning_atypical)
    # Depending on implementation, may be case-insensitive and strip spaces
    assert answer.strip().lower() == "buy goog"


def test_calculate_confidence() -> None:
    """Test confidence calculation."""
    # Create a config with RAG disabled to avoid SentenceTransformer issues
    mock_config = QuantChainConfig()
    mock_config._config["rag"] = {"enabled": False}

    agent = QuantChainAgent(mock_config, llm_provider=MockLLMProvider())

    high_confidence = "I am certain this is definitely the right approach"
    score = agent._calculate_confidence(high_confidence)
    assert score > 0

    low_confidence = "Maybe this could work"
    score = agent._calculate_confidence(low_confidence)
    assert score >= 0

    # Test with all certainty words present
    all_certainty = (
        "I am certain, confident, sure, definitely, and clearly the right approach"
    )
    score = agent._calculate_confidence(all_certainty)
    assert score == 1.0  # Should not exceed 1.0
