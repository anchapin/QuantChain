"""AI Model Training Mode for Agent Performance Improvement."""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from ..core.config import QuantChainConfig
from ..core.reflection import AgentAction, ReflectionEngine
from .paper_trading import PaperTradingExecutor, PerformanceMetrics
from .trading_execution import (
    AccountInfo,
    OrderNotFoundError,
    OrderRequest,
    OrderResult,
    OrderStatus,
    Position,
    TradingExecutionInterface,
)
from .tutorial_mode import ConfidenceMetrics, MarketDriverAnalysis, MistakeTracker

logger = logging.getLogger(__name__)


@dataclass
class TrainingSession:
    """Manages a single AI agent training session."""

    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    agent_name: str = "QuantChainAgent"
    objectives: List[str] = field(default_factory=list)
    duration_seconds: int = 3600
    iterations_planned: int = 1000
    iterations_completed: int = 0
    performance_history: List[float] = field(default_factory=list)
    best_parameters: Dict[str, Any] = field(default_factory=dict)
    initial_parameters: Dict[str, Any] = field(default_factory=dict)
    current_parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        if self.end_time is not None:
            return False

        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        return (
            elapsed < self.duration_seconds
            and self.iterations_completed < self.iterations_planned
        )

    @property
    def elapsed_time(self) -> int:
        """Get elapsed time in seconds."""
        return int((datetime.now(timezone.utc) - self.start_time).total_seconds())

    @property
    def progress_percentage(self) -> float:
        """Get training progress as percentage."""
        if self.iterations_planned > 0:
            return min(
                100.0, (self.iterations_completed / self.iterations_planned) * 100
            )
        return 0.0

    @property
    def time_progress_percentage(self) -> float:
        """Get time-based progress as percentage."""
        elapsed = self.elapsed_time
        return min(100.0, (elapsed / self.duration_seconds) * 100)

    @property
    def current_performance(self) -> Optional[float]:
        """Get current performance score."""
        return self.performance_history[-1] if self.performance_history else None

    @property
    def improvement_trend(self) -> float:
        """Calculate performance improvement trend."""
        if len(self.performance_history) < 10:
            return 0.0

        recent_avg = sum(self.performance_history[-10:]) / 10
        earlier_avg = sum(self.performance_history[:10]) / 10

        if earlier_avg == 0:
            return 0.0

        return ((recent_avg - earlier_avg) / earlier_avg) * 100

    @property
    def estimated_completion(self) -> datetime:
        """Estimate completion time based on current progress."""
        if self.iterations_completed == 0:
            return self.start_time + timedelta(seconds=self.duration_seconds)

        iterations_per_second = self.iterations_completed / max(1, self.elapsed_time)
        remaining_iterations = self.iterations_planned - self.iterations_completed
        remaining_time = remaining_iterations / max(0.001, iterations_per_second)

        return datetime.now(timezone.utc) + timedelta(seconds=remaining_time)

    def add_objective(self, objective: str) -> None:
        """Add a training objective."""
        if objective not in self.objectives:
            self.objectives.append(objective)

    def update_performance(self, performance_score: float) -> None:
        """Update performance history."""
        self.performance_history.append(performance_score)

    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """Update current agent parameters."""
        self.current_parameters.update(parameters)

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "agent_name": self.agent_name,
            "objectives": self.objectives,
            "duration_seconds": self.duration_seconds,
            "iterations_planned": self.iterations_planned,
            "iterations_completed": self.iterations_completed,
            "progress_percentage": self.progress_percentage,
            "time_progress_percentage": self.time_progress_percentage,
            "performance_history": self.performance_history[-50:],  # Keep last 50
            "current_performance": self.current_performance,
            "improvement_trend": self.improvement_trend,
            "best_parameters": self.best_parameters,
            "current_parameters": self.current_parameters,
            "is_active": self.is_active,
            "estimated_completion": self.estimated_completion.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class TrainingDecision:
    """Represents a trading decision made during training."""

    decision_id: str
    timestamp: datetime
    session_id: str
    agent_action: AgentAction
    order: Optional[OrderResult]
    market_data: Dict[str, Any]
    decision_quality: float
    reasoning: str
    market_drivers: List[str] = field(default_factory=list)
    mistakes: List[str] = field(default_factory=list)
    learning_points: List[str] = field(default_factory=list)
    performance_impact: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert decision to dictionary."""
        return {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "agent_action": str(self.agent_action),
            "order_id": self.order.order_id if self.order else None,
            "decision_quality": self.decision_quality,
            "reasoning": self.reasoning,
            "market_drivers": self.market_drivers,
            "mistakes": self.mistakes,
            "learning_points": self.learning_points,
            "performance_impact": self.performance_impact,
        }


class PerformanceTracker:
    """Tracks and analyzes AI agent performance during training."""

    def __init__(self, metrics_to_track: Optional[List[str]] = None):
        """Initialize with specified metrics."""
        self.metrics_to_track = metrics_to_track or [
            "decision_quality",
            "profit_loss",
            "risk_management",
            "consistency",
            "adaptation",
            "win_rate",
        ]
        self.performance_history: Dict[str, List[float]] = {
            metric: [] for metric in self.metrics_to_track
        }
        self.decisions: List[TrainingDecision] = []
        self.current_session: Optional[TrainingSession] = None

    def start_session(self, session: TrainingSession) -> None:
        """Start tracking a new training session."""
        self.current_session = session
        logger.info(f"Started tracking training session: {session.session_id}")

    def record_decision(self, decision: TrainingDecision) -> None:
        """Record and analyze a trading decision."""
        self.decisions.append(decision)

        # Update performance metrics
        self.performance_history["decision_quality"].append(decision.decision_quality)

        # Calculate other metrics
        if decision.order:
            # Calculate P&L impact
            performance_impact = self._calculate_performance_impact(decision)
            self.performance_history["profit_loss"].append(performance_impact)

            # Update win rate
            current_wins = sum(
                1 for p in self.performance_history["profit_loss"][-20:] if p > 0
            )
            win_rate = current_wins / min(
                20, len(self.performance_history["profit_loss"])
            )
            self.performance_history["win_rate"][-20:] = [win_rate] * min(
                20, len(self.performance_history["profit_loss"][-20:])
            )

        # Update session performance
        if self.current_session:
            overall_score = self._calculate_overall_performance()
            self.current_session.update_performance(overall_score)

    def get_improvement_trend(self, window_size: int = 100) -> float:
        """Calculate performance improvement trend."""
        if len(self.performance_history["decision_quality"]) < 2:
            return 0.0

        # Use all available data if less than window_size
        data = self.performance_history["decision_quality"]
        recent_count = min(window_size, len(data) // 2)
        recent = data[-recent_count:]
        earlier = (
            data[-recent_count * 2 : -recent_count]
            if len(data) >= recent_count * 2
            else data[: len(data) - recent_count]
        )

        if not recent or not earlier:
            return 0.0

        recent_avg = sum(recent) / len(recent)
        earlier_avg = sum(earlier) / len(earlier)

        if earlier_avg == 0:
            return 0.0

        return ((recent_avg - earlier_avg) / earlier_avg) * 100

    def identify_weaknesses(self) -> List[str]:
        """Identify areas needing improvement."""
        weaknesses = []

        # Check decision quality
        if self.performance_history["decision_quality"]:
            avg_quality = sum(self.performance_history["decision_quality"][-20:]) / min(
                20, len(self.performance_history["decision_quality"])
            )
            if avg_quality < 0.6:
                weaknesses.append(
                    "Low decision quality - needs market analysis improvement"
                )

        # Check consistency
        if len(self.performance_history["decision_quality"]) >= 10:
            recent_values = self.performance_history["decision_quality"][-10:]
            variance = sum(
                (x - sum(recent_values) / len(recent_values)) ** 2
                for x in recent_values
            ) / len(recent_values)
            if variance > 0.1:
                weaknesses.append(
                    "Inconsistent decision making - needs stability improvement"
                )

        # Check win rate
        if self.performance_history["win_rate"]:
            current_win_rate = self.performance_history["win_rate"][-1]
            if current_win_rate < 0.5:
                weaknesses.append("Low win rate - needs strategy refinement")

        # Check adaptation
        trend = self.get_improvement_trend()
        if trend < -5:
            weaknesses.append("Declining performance - needs adaptation improvement")

        return weaknesses

    def _calculate_performance_impact(self, decision: TrainingDecision) -> float:
        """Calculate performance impact of a decision."""
        # Simplified calculation - in real implementation would consider
        # P&L, risk-adjusted returns, etc.
        if decision.decision_quality > 0.7:
            return decision.decision_quality * 0.1  # Positive impact
        elif decision.decision_quality < 0.3:
            return -0.05  # Negative impact
        return 0.0  # Neutral impact

    def _calculate_overall_performance(self) -> float:
        """Calculate overall performance score."""
        if not self.performance_history["decision_quality"]:
            return 0.5  # Default starting score

        # Weighted average of key metrics
        quality_weight = 0.4
        consistency_weight = 0.3
        win_rate_weight = 0.3

        quality_score = sum(self.performance_history["decision_quality"][-10:]) / min(
            10, len(self.performance_history["decision_quality"])
        )

        # Consistency (inverse of variance)
        if len(self.performance_history["decision_quality"]) >= 5:
            recent_values = self.performance_history["decision_quality"][-5:]
            mean_val = sum(recent_values) / len(recent_values)
            variance = sum((x - mean_val) ** 2 for x in recent_values) / len(
                recent_values
            )
            consistency_score = 1.0 - min(1.0, variance * 10)
        else:
            consistency_score = 0.5

        # Win rate
        win_rate_score = (
            self.performance_history["win_rate"][-1]
            if self.performance_history["win_rate"]
            else 0.5
        )

        overall = (
            quality_score * quality_weight
            + consistency_score * consistency_weight
            + win_rate_score * win_rate_weight
        )

        return min(1.0, max(0.0, overall))

    def get_current_metrics(self) -> Dict[str, float]:
        """Get current performance metrics."""
        metrics = {}

        for metric in self.metrics_to_track:
            if self.performance_history[metric]:
                # Use average of recent values
                recent_count = min(20, len(self.performance_history[metric]))
                recent_avg = (
                    sum(self.performance_history[metric][-recent_count:]) / recent_count
                )
                metrics[metric] = recent_avg
            else:
                metrics[metric] = 0.0

        metrics["improvement_trend"] = self.get_improvement_trend()
        metrics["total_decisions"] = len(self.decisions)

        return metrics


class ModelOptimizer:
    """Optimizes AI model parameters based on performance feedback."""

    def __init__(self, optimization_strategy: str = "bayesian"):
        """Initialize with optimization strategy."""
        self.optimization_strategy = optimization_strategy
        self.optimization_history: List[Dict[str, Any]] = []
        self.best_performance = 0.0
        self.best_parameters: Dict[str, Any] = {}

    def optimize_parameters(
        self,
        current_parameters: Dict[str, Any],
        performance_feedback: Dict[str, float],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Optimize model parameters based on performance feedback."""
        current_score = performance_feedback.get("overall_score", 0.0)

        # Update best performance if improved
        if current_score > self.best_performance:
            self.best_performance = current_score
            self.best_parameters = current_parameters.copy()

        # Apply optimization strategy
        if self.optimization_strategy == "bayesian":
            optimized_params = self._bayesian_optimization(
                current_parameters, performance_feedback, constraints
            )
        elif self.optimization_strategy == "grid_search":
            optimized_params = self._grid_search_optimization(
                current_parameters, performance_feedback, constraints
            )
        else:
            # Default: simple gradient-based adjustment
            optimized_params = self._gradient_adjustment(
                current_parameters, performance_feedback, constraints
            )

        # Record optimization
        self.optimization_history.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "old_parameters": current_parameters,
                "new_parameters": optimized_params,
                "performance_score": current_score,
                "improvement": current_score - self.best_performance,
            }
        )

        return optimized_params

    def suggest_improvements(self, performance_data: List[float]) -> List[str]:
        """Suggest model improvements based on performance data."""
        suggestions: List[str] = []

        if not performance_data:
            return suggestions

        # Analyze performance trend
        if len(performance_data) >= 10:
            recent = performance_data[-10:]
            earlier = (
                performance_data[-20:-10]
                if len(performance_data) >= 20
                else performance_data[:10]
            )

            recent_avg = sum(recent) / len(recent)
            earlier_avg = sum(earlier) / len(earlier)

            if recent_avg < earlier_avg:
                suggestions.append(
                    "Performance declining - consider reducing learning rate"
                )
            elif recent_avg - earlier_avg < 0.05:
                suggestions.append("Slow improvement - consider increasing exploration")

        # Check volatility
        if len(performance_data) >= 5:
            recent = performance_data[-5:]
            variance = sum((x - sum(recent) / len(recent)) ** 2 for x in recent) / len(
                recent
            )
            if variance > 0.1:
                suggestions.append(
                    (
                        "High performance volatility - consider "
                        "more conservative parameters"
                    )
                )

        # Check overall level
        current_score = performance_data[-1]
        if current_score < 0.5:
            suggestions.append("Low performance - consider model architecture review")
        elif current_score > 0.8:
            suggestions.append("Good performance - consider fine-tuning for edge cases")

        return suggestions

    def _bayesian_optimization(
        self,
        current_parameters: Dict[str, Any],
        performance_feedback: Dict[str, float],
        constraints: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Apply Bayesian optimization strategy."""
        # Simplified Bayesian optimization
        # In real implementation would use proper Bayesian optimization library
        optimized = current_parameters.copy()

        # Adjust parameters based on performance
        for param, value in current_parameters.items():
            if isinstance(value, (int, float)):
                # Adjust based on performance gradient
                adjustment = (
                    (performance_feedback.get("improvement_trend", 0) / 100)
                    * value
                    * 0.1
                )

                # Apply constraints
                if constraints and param in constraints:
                    min_val = constraints[param].get("min", 0)
                    max_val = constraints[param].get("max", 1)
                    optimized[param] = max(min_val, min(max_val, value + adjustment))
                else:
                    optimized[param] = value + adjustment

        return optimized

    def _grid_search_optimization(
        self,
        current_parameters: Dict[str, Any],
        performance_feedback: Dict[str, float],
        constraints: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Apply grid search optimization strategy."""
        # Simplified grid search
        # In real implementation would explore parameter grid
        optimized = current_parameters.copy()

        # Example: adjust learning rate based on performance
        if "learning_rate" in optimized:
            current_score = performance_feedback.get("overall_score", 0.0)
            if current_score < 0.5:
                # Decrease learning rate if poor performance
                optimized["learning_rate"] *= 0.9
            elif current_score > 0.8:
                # Increase learning rate if good performance
                optimized["learning_rate"] *= 1.1

        return optimized

    def _gradient_adjustment(
        self,
        current_parameters: Dict[str, Any],
        performance_feedback: Dict[str, float],
        constraints: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Apply gradient-based parameter adjustment."""
        optimized = current_parameters.copy()

        # Simple gradient-based adjustment
        for param, value in current_parameters.items():
            if isinstance(value, (int, float)):
                # Use performance improvement as gradient signal
                gradient = performance_feedback.get("improvement_trend", 0) / 100
                learning_rate = 0.01  # Small adjustment rate

                adjustment = gradient * learning_rate * value
                optimized[param] = value + adjustment

        return optimized


class AgentTrainingMode(TradingExecutionInterface):
    """AI agent training mode for performance improvement."""

    def __init__(
        self,
        agent: Optional[Any] = None,
        initial_cash: float = 100000.0,
        config: Optional[QuantChainConfig] = None,
        learning_objectives: Optional[List[str]] = None,
        track_performance: bool = True,
        optimize_parameters: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize AI training mode."""
        self.agent = agent
        self.config = config
        self.learning_objectives = learning_objectives or [
            "Learn market drivers",
            "Improve decision quality",
            "Optimize risk management",
        ]
        self.track_performance = track_performance
        self.optimize_parameters = optimize_parameters

        # Initialize paper trading backend
        self.paper_executor = PaperTradingExecutor(
            initial_cash=initial_cash,
            commission_per_trade=kwargs.get("commission_per_trade", 0.0),
            commission_per_share=kwargs.get("commission_per_share", 0.0),
        )

        # Initialize training components
        self.reflection_engine = ReflectionEngine() if config else None
        self.market_driver_analysis = MarketDriverAnalysis()
        self.mistake_tracker = MistakeTracker()
        self.confidence_metrics = ConfidenceMetrics()

        # Training-specific components
        self.current_session: Optional[TrainingSession] = None
        self.performance_tracker = PerformanceTracker()
        self.model_optimizer = ModelOptimizer(
            optimization_strategy=kwargs.get("optimization_strategy", "bayesian")
        )

        # Training state
        self.training_history: List[TrainingSession] = []
        self.decision_history: List[TrainingDecision] = []
        self.market_prices: Dict[str, float] = {}

        logger.info(
            f"Initialized AI Training Mode with objectives: {self.learning_objectives}"
        )

    def start_training_session(
        self,
        symbols: Optional[List[str]] = None,
        objectives: Optional[List[str]] = None,
        duration_seconds: int = 3600,
        iterations: int = 1000,
        agent_parameters: Optional[Dict[str, Any]] = None,
    ) -> TrainingSession:
        """Start a new training session."""
        session_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)

        # Combine default and custom objectives
        session_objectives = self.learning_objectives.copy()
        if objectives:
            session_objectives.extend(objectives)

        # Create training session
        session = TrainingSession(
            session_id=session_id,
            start_time=start_time,
            agent_name=(
                getattr(self.agent, "name", "UnknownAgent")
                if self.agent
                else "QuantChainAgent"
            ),
            objectives=session_objectives,
            duration_seconds=duration_seconds,
            iterations_planned=iterations,
            initial_parameters=agent_parameters or {},
            current_parameters=agent_parameters or {},
            metadata={
                "symbols": symbols or [],
                "config": self.config.to_dict() if self.config else {},
                "training_mode": "ai_model_training",
            },
        )

        self.current_session = session
        self.performance_tracker.start_session(session)
        self.training_history.append(session)

        logger.info(
            (
                f"Started AI training session {session_id} for {duration_seconds}s "
                f"with {iterations} iterations"
            )
        )

        return session

    def train_agent(
        self,
        market_data: Optional[Dict[str, Any]] = None,
        iterations: int = 100,
        batch_size: int = 10,
        learning_rate: float = 0.001,
    ) -> Dict[str, Any]:
        """Execute training iterations with market data."""
        if not self.current_session:
            raise ValueError("No active training session. Start a session first.")

        if not market_data:
            market_data = {}

        results = {
            "iterations_completed": 0,
            "performance_improvement": 0.0,
            "best_score": 0.0,
            "final_metrics": {},
        }

        initial_performance = self.current_session.current_performance or 0.5

        # Execute training iterations
        for iteration in range(iterations):
            if not self.current_session.is_active:
                logger.info(
                    (
                        f"Training session ended after "
                        f"{results['iterations_completed']} iterations"
                    )
                )
                break

            # Simulate trading decision
            decision = self._make_training_decision(market_data)

            # Record decision
            self.decision_history.append(decision)
            self.performance_tracker.record_decision(decision)

            # Update session
            self.current_session.iterations_completed += 1

            # Optimize parameters if enabled and batch completed
            if self.optimize_parameters and (iteration + 1) % batch_size == 0:
                current_metrics = self.performance_tracker.get_current_metrics()
                optimized_params = self.model_optimizer.optimize_parameters(
                    self.current_session.current_parameters, current_metrics
                )
                self.current_session.update_parameters(optimized_params)

            # Periodic logging
            if (iteration + 1) % 10 == 0:
                logger.info(
                    f"Completed {iteration + 1}/{iterations} iterations, "
                    f"performance: {self.current_session.current_performance:.3f}"
                )

            results["iterations_completed"] = iteration + 1

        # Calculate results
        final_performance = self.current_session.current_performance or 0.5
        results["performance_improvement"] = final_performance - initial_performance
        results["best_score"] = (
            max(self.current_session.performance_history)
            if self.current_session.performance_history
            else 0.0
        )
        results["final_metrics"] = self.performance_tracker.get_current_metrics()

        logger.info(
            f"Training completed: {results['iterations_completed']} iterations, "
            f"improvement: {results['performance_improvement']:.3f}"
        )

        return results

    def evaluate_performance(
        self, test_scenarios: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """Evaluate agent performance on test scenarios."""
        results = {}

        for scenario in test_scenarios:
            # Simulate scenario evaluation
            scenario_data = self._generate_scenario_data(scenario)

            # Run evaluation
            scenario_results = self._run_scenario_evaluation(scenario_data)
            results[scenario] = scenario_results

            logger.info(
                (
                    f"Scenario '{scenario}' evaluation: "
                    f"score={scenario_results.get('score', 0):.3f}"
                )
            )

        return results

    def fine_tune_parameters(
        self,
        performance_feedback: Dict[str, Dict[str, float]],
        optimization_target: str = "overall_score",
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Fine-tune agent parameters based on performance feedback."""
        if not self.current_session:
            raise ValueError("No active training session")

        # Aggregate feedback across scenarios
        aggregated_feedback = {
            "overall_score": sum(
                feedback.get("score", 0) for feedback in performance_feedback.values()
            )
            / len(performance_feedback),
            "improvement_trend": self.performance_tracker.get_improvement_trend(),
        }

        # Optimize parameters
        optimized_params = self.model_optimizer.optimize_parameters(
            self.current_session.current_parameters, aggregated_feedback, constraints
        )

        # Update session
        self.current_session.update_parameters(optimized_params)

        # Store as best if improved
        current_score = aggregated_feedback["overall_score"]
        if current_score > (self.current_session.best_parameters.get("_score", 0)):
            self.current_session.best_parameters = optimized_params.copy()
            self.current_session.best_parameters["_score"] = current_score

        logger.info(f"Fine-tuned parameters, new score: {current_score:.3f}")

        return optimized_params

    def get_training_progress(self) -> Dict[str, Any]:
        """Get detailed training progress."""
        if not self.current_session:
            raise ValueError("No active training session")

        session_dict = self.current_session.to_dict()
        metrics = self.performance_tracker.get_current_metrics()
        suggestions = self.model_optimizer.suggest_improvements(
            self.current_session.performance_history
        )

        return {
            "session": session_dict,
            "current_metrics": metrics,
            "suggestions": suggestions,
            "weaknesses": self.performance_tracker.identify_weaknesses(),
            "best_performance": self.model_optimizer.best_performance,
            "total_decisions": len(self.decision_history),
        }

    def export_improved_agent(
        self,
        filename: Optional[str] = None,
        include_training_history: bool = True,
        include_optimized_params: bool = True,
    ) -> Dict[str, Any]:
        """Export improved agent state."""
        if not self.current_session:
            raise ValueError("No active training session")

        # Prepare export data
        export_data = {
            "agent_name": self.current_session.agent_name,
            "training_session_id": self.current_session.session_id,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "training_duration": self.current_session.elapsed_time,
            "final_performance": self.current_session.current_performance,
            "improvement_made": self.current_session.improvement_trend,
        }

        if include_training_history:
            export_data["training_history"] = self.current_session.performance_history
            export_data["session_metadata"] = self.current_session.to_dict()

        if include_optimized_params and self.current_session.best_parameters:
            export_data["optimized_parameters"] = self.current_session.best_parameters

        # Save to file if filename provided
        if filename:
            with open(filename, "w") as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"Exported improved agent to {filename}")

        return export_data

    def end_training_session(self) -> Dict[str, Any]:
        """End current training session and generate report."""
        if not self.current_session:
            raise ValueError("No active training session to end")

        # End session
        self.current_session.end_time = datetime.now(timezone.utc)

        # Generate final report
        final_feedback = self.performance_tracker.get_current_metrics()
        paper_trading_metrics = self.paper_executor.get_performance_metrics()

        report = {
            "session": self.current_session.to_dict(),
            "final_performance": final_feedback,
            "paper_trading_metrics": (
                paper_trading_metrics.__dict__ if paper_trading_metrics else {}
            ),
            "training_summary": {
                "total_iterations": self.current_session.iterations_completed,
                "improvement_trend": self.current_session.improvement_trend,
                "best_performance": (
                    max(self.current_session.performance_history)
                    if self.current_session.performance_history
                    else 0.0
                ),
                "weaknesses_identified": self.performance_tracker.identify_weaknesses(),
                "optimization_suggestions": self.model_optimizer.suggest_improvements(
                    self.current_session.performance_history
                ),
            },
            "ready_for_live": self._assess_live_trading_readiness(),
        }

        self.current_session = None

        logger.info("Ended training session, generated final report")

        return report

    def _make_training_decision(self, market_data: Dict[str, Any]) -> TrainingDecision:
        """Make a trading decision during training."""
        decision_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)

        # Simulate agent action (would integrate with actual agent)
        agent_action = self._simulate_agent_action(market_data)

        # Execute order if action requires it
        order_result = None
        if (
            hasattr(agent_action, "action_type")
            and agent_action.action_type == "execute_order"
        ):
            try:
                order_request = self._create_order_from_action(agent_action)
                order_result = self.paper_executor.place_order(order_request)
            except Exception as e:
                logger.warning(f"Failed to execute order: {e}")

        # Analyze decision quality
        decision_quality = self._evaluate_decision_quality(
            agent_action, market_data, order_result
        )

        # Analyze market drivers
        market_drivers = []
        if self.market_driver_analysis and market_data:
            # This would integrate with the market driver analysis
            market_drivers = ["Simulated market driver"]  # Placeholder

        # Generate decision
        decision = TrainingDecision(
            decision_id=decision_id,
            timestamp=timestamp,
            session_id=(
                self.current_session.session_id if self.current_session else "unknown"
            ),
            agent_action=agent_action,
            order=order_result,
            market_data=market_data,
            decision_quality=decision_quality,
            reasoning=self._generate_reasoning(agent_action, market_data),
            market_drivers=market_drivers,
            performance_impact=self._calculate_performance_impact(
                decision_quality, order_result
            ),
        )

        return decision

    def _simulate_agent_action(self, market_data: Dict[str, Any]) -> AgentAction:
        """Simulate agent action for training."""
        # Simplified simulation - would integrate with actual agent
        import random

        action_type = random.choice(["analyze", "execute_order", "wait"])

        if action_type == "execute_order":
            symbol = random.choice(
                list(market_data.keys()) if market_data else ["AAPL"]
            )
            side = random.choice(["buy", "sell"])
            quantity = random.randint(10, 100)

            return AgentAction(
                timestamp=datetime.now(timezone.utc),
                action_type=action_type,
                parameters={
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "order_type": "market",
                },
                result="simulated_order",
                confidence_score=0.7,
                success=True,
                reward=0.1,
            )
        else:
            return AgentAction(
                timestamp=datetime.now(timezone.utc),
                action_type=action_type,
                parameters=market_data,
                result="analysis_complete",
                confidence_score=0.6,
                success=True,
                reward=0.05,
            )

    def _create_order_from_action(self, agent_action: AgentAction) -> OrderRequest:
        """Create order request from agent action."""
        from .trading_execution import OrderRequest, OrderSide, OrderType

        params = agent_action.parameters or {}

        return OrderRequest(
            symbol=params.get("symbol", "AAPL"),
            side=OrderSide.BUY if params.get("side") == "buy" else OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=params.get("quantity", 100),
        )

    def _evaluate_decision_quality(
        self,
        agent_action: AgentAction,
        market_data: Dict[str, Any],
        order_result: Optional[OrderResult],
    ) -> float:
        """Evaluate the quality of a trading decision."""
        # Simplified quality evaluation
        # In real implementation would use sophisticated analysis

        base_quality = 0.5

        # Consider action type
        if agent_action.action_type == "analyze":
            base_quality += 0.2
        elif agent_action.action_type == "execute_order":
            # Check if order was successful
            if order_result and order_result.status == OrderStatus.FILLED:
                base_quality += 0.3

        # Consider market conditions (simplified)
        if market_data.get("volatility", 0) > 0.2:
            base_quality -= 0.1  # Penalize trading in high volatility

        # Add randomness for simulation
        import random

        base_quality += random.uniform(-0.2, 0.2)

        return max(0.0, min(1.0, base_quality))

    def _generate_reasoning(
        self, agent_action: AgentAction, market_data: Dict[str, Any]
    ) -> str:
        """Generate reasoning for a decision."""
        if agent_action.action_type == "analyze":
            return f"Analyzing market conditions: {len(market_data)} data points"
        elif agent_action.action_type == "execute_order":
            params = agent_action.parameters or {}
            return (
                f"Executing {params.get('side', 'unknown')} "
                f"order for {params.get('symbol', 'unknown')}"
            )
        else:
            return "Waiting for better market conditions"

    def _calculate_performance_impact(
        self, decision_quality: float, order_result: Optional[OrderResult]
    ) -> float:
        """Calculate performance impact of a decision."""
        if not order_result or order_result.status != OrderStatus.FILLED:
            return 0.0

        # Simplified impact calculation
        if decision_quality > 0.7:
            return 0.1  # Positive impact
        elif decision_quality < 0.3:
            return -0.05  # Negative impact
        return 0.0  # Neutral impact

    def _generate_scenario_data(self, scenario: str) -> Dict[str, Any]:
        """Generate market data for a test scenario."""
        # Simplified scenario generation
        if "bull" in scenario.lower():
            return {"trend": "up", "volatility": 0.15, "volume": 1.2}
        elif "bear" in scenario.lower():
            return {"trend": "down", "volatility": 0.25, "volume": 1.5}
        elif "volatile" in scenario.lower():
            return {"trend": "sideways", "volatility": 0.4, "volume": 2.0}
        else:
            return {"trend": "sideways", "volatility": 0.2, "volume": 1.0}

    def _run_scenario_evaluation(
        self, scenario_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Run evaluation on a single scenario."""
        # Simulate scenario evaluation
        # In real implementation would run actual agent against scenario

        base_score = 0.5

        # Adjust based on scenario
        if scenario_data["trend"] == "up":
            base_score += 0.1
        elif scenario_data["trend"] == "down":
            base_score -= 0.1

        if scenario_data["volatility"] > 0.3:
            base_score -= 0.05  # Penalty for high volatility

        return {
            "score": max(0.0, min(1.0, base_score)),
            "risk_adjusted_score": base_score * 0.9,
            "consistency": 0.7 + (scenario_data["volatility"] * -0.5),
        }

    def _assess_live_trading_readiness(self) -> Dict[str, Any]:
        """Assess if the agent is ready for live trading."""
        if not self.current_session:
            return {"ready": False, "reason": "No training session"}

        # Check various readiness criteria
        criteria = {
            "sufficient_iterations": self.current_session.iterations_completed >= 100,
            "good_performance": (self.current_session.current_performance or 0) >= 0.7,
            "consistent_performance": abs(self.current_session.improvement_trend) < 50,
            "improving_trend": self.current_session.improvement_trend > 0,
        }

        all_passed = all(criteria.values())

        readiness_assessment = {
            "ready": all_passed,
            "criteria": criteria,
            "confidence": self.current_session.current_performance or 0.0,
            "recommendations": (
                []
                if all_passed
                else [
                    (
                        "Increase training iterations"
                        if not criteria["sufficient_iterations"]
                        else None
                    ),
                    (
                        "Improve decision quality"
                        if not criteria["good_performance"]
                        else None
                    ),
                    (
                        "Work on consistency"
                        if not criteria["consistent_performance"]
                        else None
                    ),
                    "Focus on improvement" if not criteria["improving_trend"] else None,
                ]
            ),
        }

        # Filter out None recommendations
        recommendations = readiness_assessment.get("recommendations", [])
        if isinstance(recommendations, list):
            readiness_assessment["recommendations"] = [r for r in recommendations if r]

        return readiness_assessment

    # Delegate methods to paper executor
    def place_order(self, order: OrderRequest) -> OrderResult:
        """Place an order through the paper trading executor."""
        return self.paper_executor.place_order(order)

    def cancel_order(self, order_id: str) -> OrderResult:
        """Cancel an order."""
        return self.paper_executor.cancel_order(order_id)

    def get_account(self) -> AccountInfo:
        """Get account information."""
        return self.paper_executor.get_account()

    def get_positions(self) -> List[Position]:
        """Get current positions."""
        return self.paper_executor.get_positions()

    def get_orders(self) -> List[OrderResult]:
        """Get order history."""
        orders: List[OrderResult] = getattr(
            self.paper_executor, "get_orders", lambda: []
        )()
        return orders if isinstance(orders, list) else []

    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get performance metrics from paper trading."""
        return self.paper_executor.get_performance_metrics()

    def is_market_open(self, symbol: Optional[str] = None) -> bool:
        """Check if market is open."""
        return self.paper_executor.is_market_open(symbol)

    def set_market_price(self, symbol: str, price: float) -> None:
        """Set market price for simulation."""
        self.market_prices[symbol] = price
        if hasattr(self.paper_executor, "set_market_price"):
            self.paper_executor.set_market_price(symbol, price)

    def reset(self) -> None:
        """Reset training state."""
        self.current_session = None
        self.decision_history.clear()
        self.market_prices.clear()
        self.paper_executor.reset()
        self.performance_tracker = PerformanceTracker()
        logger.info("Reset AI training mode")

    def get_order(self, order_id: str) -> OrderResult:
        """Get a specific order by ID."""
        try:
            result = getattr(self.paper_executor, "get_order", None)
            if result:
                order = result(order_id)
                if isinstance(order, OrderResult):
                    return order
        except (AttributeError, TypeError):
            pass

        # Fallback - search in order history
        for order in self.get_orders():
            if order.order_id == order_id:
                return order  # type: ignore

        raise OrderNotFoundError(f"Order {order_id} not found")

    def get_order_history(
        self,
        symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[OrderResult]:
        """Get order history with optional filtering."""
        orders = self.get_orders()

        # Apply filters
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        if status:
            orders = [o for o in orders if o.status == status]
        if start_date:
            orders = [
                o
                for o in orders
                if hasattr(o, "created_at")
                and o.created_at
                and o.created_at >= start_date
            ]
        if end_date:
            orders = [
                o
                for o in orders
                if hasattr(o, "created_at")
                and o.created_at
                and o.created_at <= end_date
            ]
        if limit:
            orders = orders[:limit]

        return orders
