"""Core agent engine using LangGraph for QuantChain."""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, TypedDict

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool
    from langgraph.graph import END, StateGraph

try:
    from langchain_core.tools import BaseTool  # noqa: F811
    from langgraph.graph import END, StateGraph  # noqa: F811
except ImportError:
    StateGraph = None  # type: ignore[assignment,misc]
    END = None  # type: ignore[assignment,misc]
    BaseTool = None  # type: ignore[assignment,misc]

from .config import QuantChainConfig
from .llm_providers import LLMProvider, create_llm_provider
from .reflection import AgentAction, ReflectionEngine, ReflectionReport


@dataclass
class AgentResponse:
    """Response from agent execution."""

    final_answer: str
    reasoning_steps: List[str]
    confidence_score: float
    actions_taken: List[AgentAction]


class AgentState(TypedDict):
    """State for the LangGraph agent."""

    messages: List[Dict[str, Any]]
    current_step: int
    max_steps: int
    context: Dict[str, Any]
    final_answer: Optional[str]
    reasoning_steps: List[str]
    confidence_score: float
    actions: List[AgentAction]


class QuantChainAgent:
    """Main agent class using LangGraph framework."""

    def __init__(
        self,
        config: QuantChainConfig,
        tools: Optional[List[BaseTool]] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        if StateGraph is None:
            raise ImportError("langgraph package not installed")

        self.config = config
        self.rag_system = None  # type: ignore[assignment]
        self.tools = tools or []

        # Initialize LLM provider
        if llm_provider is None:
            provider_config = config.get("llm", {})
            provider_type = provider_config.get("provider", "ollama")
            llm_provider = create_llm_provider(
                provider_type,
                model=provider_config.get("model", "llama2:7b"),
                api_key=config.get_api_key(provider_type),
            )
        self.llm_provider = llm_provider

        # Initialize RAG system from config
        rag_config = config.get("rag", {})
        if rag_config.get("enabled", False):
            from .rag_system import (
                ChromaVectorStore,
                MarketDataRAG,
                SentenceTransformerProvider,
            )

            vector_store = ChromaVectorStore(
                persist_directory=rag_config.get(
                    "persist_directory", "./data/chroma_db"
                )
            )
            embedding_provider = SentenceTransformerProvider(
                model_name=rag_config.get("embedding_model", "all-MiniLM-L6-v2")
            )
            self.rag_system = MarketDataRAG(vector_store, embedding_provider)
        else:
            self.rag_system = None

        # Initialize reflection engine
        self.reflection_engine = ReflectionEngine()

        # Build the LangGraph
        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        """Build the LangGraph workflow."""

        def reason_step(state: AgentState) -> AgentState:
            """Reasoning step in the agent loop."""
            messages = state["messages"]
            current_step = state["current_step"]

            # Get augmented prompt if RAG is available
            prompt = messages[-1]["content"]
            if self.rag_system and "market" in prompt.lower():
                prompt = self.rag_system.generate_augmented_prompt(
                    "Analyze the following market query:", prompt
                )

            # Generate reasoning
            response = self.llm_provider.generate(
                f"Reason step {current_step + 1}: {prompt}",
                max_tokens=self.config.get("llm.max_tokens", 500),
            )

            state["reasoning_steps"].append(response.text)
            state["current_step"] = current_step + 1

            return state

        def act_step(state: AgentState) -> AgentState:
            """Action step - decide whether to use tools or finalize."""
            reasoning = state["reasoning_steps"][-1]

            # Simple decision logic - in practice, this would be more sophisticated
            if (
                "final answer" in reasoning.lower()
                or state["current_step"] >= state["max_steps"]
            ):
                # Extract final answer
                state["final_answer"] = self._extract_final_answer(reasoning)
                state["confidence_score"] = self._calculate_confidence(reasoning)
                return state

            # Use tools if available
            # TODO: Production tool selection and execution logic required here.
            # WARNING: Placeholder logic below - replace for production.
            if self.tools and "tool" in reasoning.lower():
                action = self._select_tool(reasoning)
                if action:
                    result = self._execute_tool(action)
                    state["messages"].append({"role": "tool", "content": str(result)})
                    state["actions"].append(action)

            return state

        def should_continue(state: AgentState) -> str:
            """Determine whether to continue reasoning or end."""
            if (
                state["final_answer"] is not None
                or state["current_step"] >= state["max_steps"]
            ):
                return str(END)
            return "reason"

        # Build graph
        graph = StateGraph(AgentState)

        graph.add_node("reason", reason_step)
        graph.add_node("act", act_step)

        graph.set_entry_point("reason")
        graph.add_edge("reason", "act")
        graph.add_conditional_edges(
            "act", should_continue, {"reason": "reason", END: END}
        )

        return graph.compile()

    def run(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Run the agent with given input."""
        initial_state: AgentState = {
            "messages": [{"role": "user", "content": str(input_data)}],
            "current_step": 0,
            "max_steps": self.config.get("agent.max_iterations", 5),
            "context": {},
            "final_answer": None,
            "reasoning_steps": [],
            "confidence_score": 0.0,
            "actions": [],
        }

        final_state = self.graph.invoke(initial_state)

        # Record actions for reflection
        for action in final_state["actions"]:
            self.reflection_engine.record_action(action)

        return AgentResponse(
            final_answer=final_state["final_answer"] or "No final answer reached",
            reasoning_steps=final_state["reasoning_steps"],
            confidence_score=final_state["confidence_score"],
            actions_taken=final_state["actions"],
        )

    def reflect(self) -> ReflectionReport:
        """Generate reflection report."""
        return self.reflection_engine.generate_report()

    def _extract_final_answer(self, reasoning: str) -> str:
        """Extract final answer from reasoning text."""
        # Simple extraction - in practice, use better NLP
        if "final answer:" in reasoning.lower():
            # Find the last occurrence of "final answer:" (case insensitive)
            lower_reasoning = reasoning.lower()
            last_index = lower_reasoning.rfind("final answer:")
            if last_index != -1:
                start = last_index + len("final answer:")
                return reasoning[start:].strip()
            return reasoning.split("final answer:", 1)[1].strip()
        return reasoning.strip()

    def _calculate_confidence(self, reasoning: str) -> float:
        """Calculate confidence score from reasoning."""
        # Simple heuristic - count certainty words
        certainty_words = ["certain", "confident", "sure", "definitely", "clearly"]
        score = sum(word in reasoning.lower() for word in certainty_words)
        return min(score / len(certainty_words), 1.0)

    def _select_tool(self, reasoning: str) -> Optional[AgentAction]:
        """Select appropriate tool based on reasoning."""
        # Placeholder - would need more sophisticated tool selection
        if not self.tools:
            return None

        # For now, return a dummy action
        return AgentAction(
            timestamp=datetime.now(),
            action_type="tool_use",
            parameters={"tool": "placeholder"},
            result=None,
            confidence_score=0.5,
        )

    def _execute_tool(self, action: AgentAction) -> Any:
        """Execute selected tool."""
        # Placeholder implementation
        return {"result": "Tool executed", "action": action.parameters}
