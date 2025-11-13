"""Comprehensive tests for agent engine module."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from quantchain.core.agent_engine import (
    AgentResponse,
    AgentState,
    QuantChainAgent,
)
from quantchain.core.config import QuantChainConfig
from quantchain.core.llm_providers import LLMResponse, LLMProvider
from quantchain.core.reflection import AgentAction


@pytest.mark.unit
class TestAgentResponse:
    """Test AgentResponse dataclass."""

    def test_agent_response_creation(self):
        """Test creating an AgentResponse."""
        response = AgentResponse(
            final_answer="Test answer",
            reasoning_steps=["Step 1", "Step 2"],
            confidence_score=0.85,
            actions_taken=[
                AgentAction(
                    timestamp=datetime.now(),
                    action_type="analyze",
                    parameters={"symbol": "AAPL"},
                    result="success",
                    confidence_score=0.9,
                    success=True,
                    reward=1.0
                )
            ]
        )
        
        assert response.final_answer == "Test answer"
        assert response.reasoning_steps == ["Step 1", "Step 2"]
        assert response.confidence_score == 0.85
        assert len(response.actions_taken) == 1
        assert response.actions_taken[0].action_type == "analyze"

    def test_agent_response_empty_actions(self):
        """Test AgentResponse with empty actions."""
        response = AgentResponse(
            final_answer="Test answer",
            reasoning_steps=[],
            confidence_score=0.5,
            actions_taken=[]
        )
        
        assert response.final_answer == "Test answer"
        assert response.reasoning_steps == []
        assert response.confidence_score == 0.5
        assert response.actions_taken == []


@pytest.mark.unit
class TestAgentState:
    """Test AgentState TypedDict."""

    def test_agent_state_structure(self):
        """Test AgentState has correct structure."""
        state = AgentState(
            messages=[{"role": "user", "content": "test"}],
            current_step=1,
            max_steps=5,
            context={"symbol": "AAPL"},
            final_answer=None,
            reasoning_steps=["Initial analysis"],
            confidence_score=0.0,
            actions=[]
        )
        
        assert state["messages"] == [{"role": "user", "content": "test"}]
        assert state["current_step"] == 1
        assert state["max_steps"] == 5
        assert state["context"] == {"symbol": "AAPL"}
        assert state["final_answer"] is None
        assert state["reasoning_steps"] == ["Initial analysis"]
        assert state["confidence_score"] == 0.0
        assert state["actions"] == []


@pytest.mark.unit
class TestQuantChainAgent:
    """Test QuantChainAgent class."""

    @patch('quantchain.core.agent_engine.create_llm_provider')
    def test_init_with_langgraph_available(self, mock_create_llm):
        """Test agent initialization when LangGraph is available."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_create_llm.return_value = mock_llm
        
        mock_config = MagicMock(spec=QuantChainConfig)
        mock_config.llm_config = {"model": "test-model"}
        
        with patch('quantchain.core.agent_engine.StateGraph') as mock_state_graph:
            mock_sg_instance = MagicMock()
            mock_state_graph.return_value = mock_sg_instance
            
            agent = QuantChainAgent(config=mock_config)
            
            assert agent.config == mock_config
            assert agent.llm_provider == mock_llm
            mock_create_llm.assert_called_once_with(mock_config.llm_config)

    @patch('quantchain.core.agent_engine.create_llm_provider')
    def test_init_with_default_config(self, mock_create_llm):
        """Test agent initialization with default config."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_create_llm.return_value = mock_llm
        
        with patch('quantchain.core.agent_engine.StateGraph'):
            agent = QuantChainAgent()
            assert agent.config is not None
            assert agent.llm_provider == mock_llm

    def test_init_langgraph_not_available(self):
        """Test agent initialization when LangGraph is not available."""
        with patch('quantchain.core.agent_engine.StateGraph', None):
            with pytest.raises(ImportError):
                QuantChainAgent()

    @patch('quantchain.core.agent_engine.create_llm_provider')
    @patch('quantchain.core.agent_engine.StateGraph')
    def test_add_tool(self, mock_state_graph, mock_create_llm):
        """Test adding a tool to the agent."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_create_llm.return_value = mock_llm
        
        mock_sg_instance = MagicMock()
        mock_state_graph.return_value = mock_sg_instance
        
        mock_tool = MagicMock()
        
        agent = QuantChainAgent()
        agent.add_tool(mock_tool)
        
        assert mock_tool in agent.tools

    @patch('quantchain.core.agent_engine.create_llm_provider')
    @patch('quantchain.core.agent_engine.StateGraph')
    def test_add_multiple_tools(self, mock_state_graph, mock_create_llm):
        """Test adding multiple tools to the agent."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_create_llm.return_value = mock_llm
        
        mock_sg_instance = MagicMock()
        mock_state_graph.return_value = mock_sg_instance
        
        agent = QuantChainAgent()
        
        tools = [MagicMock() for _ in range(3)]
        for tool in tools:
            agent.add_tool(tool)
        
        assert len(agent.tools) == 3
        for tool in tools:
            assert tool in agent.tools

    @patch('quantchain.core.agent_engine.create_llm_provider')
    @patch('quantchain.core.agent_engine.StateGraph')
    def test_initialize_graph(self, mock_state_graph, mock_create_llm):
        """Test graph initialization."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_create_llm.return_value = mock_llm
        
        mock_sg_instance = MagicMock()
        mock_state_graph.return_value = mock_sg_instance
        
        agent = QuantChainAgent()
        agent.initialize_graph()
        
        # Should have added nodes and edges
        assert mock_sg_instance.add_node.called
        assert mock_sg_instance.add_edge.called

    @patch('quantchain.core.agent_engine.create_llm_provider')
    @patch('quantchain.core.agent_engine.StateGraph')
    def test_run_simple(self, mock_state_graph, mock_create_llm):
        """Test running the agent with simple query."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate.return_value = LLMResponse(
            text="Test response",
            usage={"tokens": 10}
        )
        mock_create_llm.return_value = mock_llm
        
        mock_sg_instance = MagicMock()
        mock_compiled = MagicMock()
        mock_result = {
            "final_answer": "Test response",
            "reasoning_steps": ["Step 1"],
            "confidence_score": 0.8,
            "actions": []
        }
        mock_compiled.invoke.return_value = mock_result
        mock_sg_instance.compile.return_value = mock_compiled
        mock_state_graph.return_value = mock_sg_instance
        
        agent = QuantChainAgent()
        agent.initialize_graph()
        
        response = agent.run("Test query")
        
        assert isinstance(response, AgentResponse)
        assert response.final_answer == "Test response"
        assert response.reasoning_steps == ["Step 1"]
        assert response.confidence_score == 0.8
        assert response.actions_taken == []

    @patch('quantchain.core.agent_engine.create_llm_provider')
    @patch('quantchain.core.agent_engine.StateGraph')
    def test_run_with_context(self, mock_state_graph, mock_create_llm):
        """Test running the agent with context."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate.return_value = LLMResponse(
            text="Test response with context"
        )
        mock_create_llm.return_value = mock_llm
        
        mock_sg_instance = MagicMock()
        mock_compiled = MagicMock()
        mock_result = {
            "final_answer": "Context-aware response",
            "reasoning_steps": ["Analyzed context"],
            "confidence_score": 0.9,
            "actions": []
        }
        mock_compiled.invoke.return_value = mock_result
        mock_sg_instance.compile.return_value = mock_compiled
        mock_state_graph.return_value = mock_sg_instance
        
        agent = QuantChainAgent()
        agent.initialize_graph()
        
        context = {"symbol": "AAPL", "portfolio": {"cash": 10000}}
        response = agent.run("Analyze AAPL", context=context)
        
        assert response.final_answer == "Context-aware response"

    @patch('quantchain.core.agent_engine.create_llm_provider')
    @patch('quantchain.core.agent_engine.StateGraph')
    def test_run_with_actions(self, mock_state_graph, mock_create_llm):
        """Test running the agent that performs actions."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate.return_value = LLMResponse(
            text="Analysis complete"
        )
        mock_create_llm.return_value = mock_llm
        
        action = AgentAction(
            timestamp=datetime.now(),
            action_type="analyze_market",
            parameters={"symbol": "AAPL"},
            result="Bullish trend detected",
            confidence_score=0.85,
            success=True,
            reward=2.0
        )
        
        mock_sg_instance = MagicMock()
        mock_compiled = MagicMock()
        mock_result = {
            "final_answer": "Market analysis complete",
            "reasoning_steps": ["Analyzed market data"],
            "confidence_score": 0.85,
            "actions": [action]
        }
        mock_compiled.invoke.return_value = mock_result
        mock_sg_instance.compile.return_value = mock_compiled
        mock_state_graph.return_value = mock_sg_instance
        
        agent = QuantChainAgent()
        agent.initialize_graph()
        
        response = agent.run("Analyze AAPL market")
        
        assert len(response.actions_taken) == 1
        assert response.actions_taken[0].action_type == "analyze_market"
        assert response.actions_taken[0].success is True

    @patch('quantchain.core.agent_engine.create_llm_provider')
    @patch('quantchain.core.agent_engine.StateGraph')
    def test_run_with_max_steps(self, mock_state_graph, mock_create_llm):
        """Test running the agent with max steps limit."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate.return_value = LLMResponse(
            text="Response after many steps"
        )
        mock_create_llm.return_value = mock_llm
        
        mock_sg_instance = MagicMock()
        mock_compiled = MagicMock()
        mock_result = {
            "final_answer": "Max steps reached",
            "reasoning_steps": ["Step 1", "Step 2", "Step 3"],
            "confidence_score": 0.6,
            "actions": []
        }
        mock_compiled.invoke.return_value = mock_result
        mock_sg_instance.compile.return_value = mock_compiled
        mock_state_graph.return_value = mock_sg_instance
        
        agent = QuantChainAgent()
        agent.initialize_graph()
        
        response = agent.run("Complex query", max_steps=3)
        
        assert len(response.reasoning_steps) == 3
        assert response.confidence_score == 0.6

    @patch('quantchain.core.agent_engine.create_llm_provider')
    @patch('quantchain.core.agent_engine.StateGraph')
    def test_run_llm_error(self, mock_state_graph, mock_create_llm):
        """Test running the agent when LLM raises an error."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate.side_effect = Exception("LLM error")
        mock_create_llm.return_value = mock_llm
        
        mock_sg_instance = MagicMock()
        mock_compiled = MagicMock()
        mock_compiled.invoke.side_effect = Exception("Graph execution error")
        mock_sg_instance.compile.return_value = mock_compiled
        mock_state_graph.return_value = mock_sg_instance
        
        agent = QuantChainAgent()
        agent.initialize_graph()
        
        with pytest.raises(Exception, match="Graph execution error"):
            agent.run("Test query")

    @patch('quantchain.core.agent_engine.create_llm_provider')
    @patch('quantchain.core.agent_engine.StateGraph')
    def test_run_empty_response(self, mock_state_graph, mock_create_llm):
        """Test running the agent with empty response."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate.return_value = LLMResponse(text="")
        mock_create_llm.return_value = mock_llm
        
        mock_sg_instance = MagicMock()
        mock_compiled = MagicMock()
        mock_result = {
            "final_answer": "",
            "reasoning_steps": [],
            "confidence_score": 0.0,
            "actions": []
        }
        mock_compiled.invoke.return_value = mock_result
        mock_sg_instance.compile.return_value = mock_compiled
        mock_state_graph.return_value = mock_sg_instance
        
        agent = QuantChainAgent()
        agent.initialize_graph()
        
        response = agent.run("Test query")
        
        assert response.final_answer == ""
        assert response.reasoning_steps == []
        assert response.confidence_score == 0.0

    @patch('quantchain.core.agent_engine.create_llm_provider')
    @patch('quantchain.core.agent_engine.StateGraph')
    def test_run_without_initialization(self, mock_state_graph, mock_create_llm):
        """Test running the agent without graph initialization."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_create_llm.return_value = mock_llm
        
        agent = QuantChainAgent()
        
        with pytest.raises(AttributeError):  # Should fail because graph not initialized
            agent.run("Test query")

    @patch('quantchain.core.agent_engine.create_llm_provider')
    @patch('quantchain.core.agent_engine.StateGraph')
    def test_multiple_runs(self, mock_state_graph, mock_create_llm):
        """Test running the agent multiple times."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate.return_value = LLMResponse(text="Response")
        mock_create_llm.return_value = mock_llm
        
        mock_sg_instance = MagicMock()
        mock_compiled = MagicMock()
        
        def mock_invoke(state):
            return {
                "final_answer": f"Response for {state['messages'][0]['content']}",
                "reasoning_steps": ["Step 1"],
                "confidence_score": 0.8,
                "actions": []
            }
        
        mock_compiled.invoke.side_effect = mock_invoke
        mock_sg_instance.compile.return_value = mock_compiled
        mock_state_graph.return_value = mock_sg_instance
        
        agent = QuantChainAgent()
        agent.initialize_graph()
        
        # Run multiple queries
        response1 = agent.run("Query 1")
        response2 = agent.run("Query 2")
        
        assert response1.final_answer == "Response for Query 1"
        assert response2.final_answer == "Response for Query 2"
        assert mock_compiled.invoke.call_count == 2


@pytest.mark.unit
class TestQuantChainAgentEdgeCases:
    """Test edge cases for QuantChainAgent."""

    @patch('quantchain.core.agent_engine.create_llm_provider')
    @patch('quantchain.core.agent_engine.StateGraph')
    def test_run_with_none_context(self, mock_state_graph, mock_create_llm):
        """Test running the agent with None context."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate.return_value = LLMResponse(text="Response")
        mock_create_llm.return_value = mock_llm
        
        mock_sg_instance = MagicMock()
        mock_compiled = MagicMock()
        mock_result = {
            "final_answer": "Response",
            "reasoning_steps": ["Step 1"],
            "confidence_score": 0.8,
            "actions": []
        }
        mock_compiled.invoke.return_value = mock_result
        mock_sg_instance.compile.return_value = mock_compiled
        mock_state_graph.return_value = mock_sg_instance
        
        agent = QuantChainAgent()
        agent.initialize_graph()
        
        response = agent.run("Test query", context=None)
        
        assert response.final_answer == "Response"

    @patch('quantchain.core.agent_engine.create_llm_provider')
    @patch('quantchain.core.agent_engine.StateGraph')
    def test_run_with_empty_context(self, mock_state_graph, mock_create_llm):
        """Test running the agent with empty context."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate.return_value = LLMResponse(text="Response")
        mock_create_llm.return_value = mock_llm
        
        mock_sg_instance = MagicMock()
        mock_compiled = MagicMock()
        mock_result = {
            "final_answer": "Response",
            "reasoning_steps": ["Step 1"],
            "confidence_score": 0.8,
            "actions": []
        }
        mock_compiled.invoke.return_value = mock_result
        mock_sg_instance.compile.return_value = mock_compiled
        mock_state_graph.return_value = mock_sg_instance
        
        agent = QuantChainAgent()
        agent.initialize_graph()
        
        response = agent.run("Test query", context={})
        
        assert response.final_answer == "Response"

    @patch('quantchain.core.agent_engine.create_llm_provider')
    @patch('quantchain.core.agent_engine.StateGraph')
    def test_run_with_zero_max_steps(self, mock_state_graph, mock_create_llm):
        """Test running the agent with zero max steps."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate.return_value = LLMResponse(text="Quick response")
        mock_create_llm.return_value = mock_llm
        
        mock_sg_instance = MagicMock()
        mock_compiled = MagicMock()
        mock_result = {
            "final_answer": "Immediate response",
            "reasoning_steps": [],
            "confidence_score": 0.5,
            "actions": []
        }
        mock_compiled.invoke.return_value = mock_result
        mock_sg_instance.compile.return_value = mock_compiled
        mock_state_graph.return_value = mock_sg_instance
        
        agent = QuantChainAgent()
        agent.initialize_graph()
        
        response = agent.run("Test query", max_steps=0)
        
        assert response.final_answer == "Immediate response"
        assert response.reasoning_steps == []

    @patch('quantchain.core.agent_engine.create_llm_provider')
    @patch('quantchain.core.agent_engine.StateGraph')
    def test_run_with_negative_max_steps(self, mock_state_graph, mock_create_llm):
        """Test running the agent with negative max steps."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate.return_value = LLMResponse(text="Error response")
        mock_create_llm.return_value = mock_llm
        
        mock_sg_instance = MagicMock()
        mock_compiled = MagicMock()
        mock_result = {
            "final_answer": "Error: invalid max_steps",
            "reasoning_steps": [],
            "confidence_score": 0.0,
            "actions": []
        }
        mock_compiled.invoke.return_value = mock_result
        mock_sg_instance.compile.return_value = mock_compiled
        mock_state_graph.return_value = mock_sg_instance
        
        agent = QuantChainAgent()
        agent.initialize_graph()
        
        response = agent.run("Test query", max_steps=-1)
        
        assert "Error" in response.final_answer
        assert response.confidence_score == 0.0
