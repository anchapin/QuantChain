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

    def __init__(self, responses=None):
        self.responses = responses or ["Final answer: test response"]
        self.call_count = 0

    def generate(self, prompt, **kwargs):
        response = self.responses[min(self.call_count, len(self.responses) - 1)]
        self.call_count += 1
        return LLMResponse(text=response, usage={"tokens": 10})

    def get_model_name(self):
        return "mock-model"


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = MagicMock(spec=QuantChainConfig)
    config.get.return_value = 5  # max_iterations
    config.get_api_key.return_value = None
    return config


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider."""
    return MockLLMProvider()


@patch("quantchain.core.agent_engine.StateGraph")
def test_agent_initialization(mock_state_graph, mock_config, mock_llm_provider):
    """Test agent initialization."""
    # Mock the graph compilation
    mock_graph = MagicMock()
    mock_state_graph.return_value.compile.return_value = mock_graph

    agent = QuantChainAgent(mock_config, llm_provider=mock_llm_provider)

    assert agent.config == mock_config
    assert agent.llm_provider == mock_llm_provider
    assert agent.graph == mock_graph


@patch("quantchain.core.agent_engine.StateGraph")
def test_agent_run(mock_state_graph, mock_config, mock_llm_provider):
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
    mock_state_graph.return_value.compile.return_value = mock_graph

    agent = QuantChainAgent(mock_config, llm_provider=mock_llm_provider)

    input_data = {"query": "test query"}
    response = agent.run(input_data)

    assert isinstance(response, AgentResponse)
    assert response.final_answer == "Test final answer"
    assert len(response.reasoning_steps) == 2
    assert response.confidence_score == 0.8
    assert len(response.actions_taken) == 1


@patch("quantchain.core.agent_engine.StateGraph")
def test_agent_reflection(mock_state_graph, mock_config, mock_llm_provider):
    """Test agent reflection capability."""
    mock_graph = MagicMock()
    mock_state_graph.return_value.compile.return_value = mock_graph

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


def test_extract_final_answer():
    """Test final answer extraction."""
    agent = QuantChainAgent(MagicMock(), llm_provider=MockLLMProvider())

    reasoning = "After analysis, the final answer: buy AAPL"
    answer = agent._extract_final_answer(reasoning)
    assert answer == "buy AAPL"

    reasoning_no_final = "This is just reasoning without final answer"
    answer = agent._extract_final_answer(reasoning_no_final)
    assert answer == reasoning_no_final.strip()


def test_calculate_confidence():
    """Test confidence calculation."""
    agent = QuantChainAgent(MagicMock(), llm_provider=MockLLMProvider())

    high_confidence = "I am certain this is definitely the right approach"
    score = agent._calculate_confidence(high_confidence)
    assert score > 0

    low_confidence = "Maybe this could work"
    score = agent._calculate_confidence(low_confidence)
    assert score >= 0
