"""Tests for AI model training mode functionality."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from quantchain.core.config import QuantChainConfig
from quantchain.core.reflection import AgentAction
from quantchain.tools.agent_training_mode import (
    AgentTrainingMode,
    ModelOptimizer,
    PerformanceTracker,
    TrainingDecision,
    TrainingSession,
)
from quantchain.tools.trading_execution import (
    OrderResult,
    OrderSide,
    OrderStatus,
    OrderType,
)


class TestTrainingSession:
    """Test training session management."""

    def test_session_initialization(self) -> None:
        """Test training session initialization."""
        session_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        objectives: list[float] = ["Improve decision quality", "Learn market drivers"]
        parameters = {"learning_rate": 0.001, "exploration_rate": 0.1}

        session = TrainingSession(
            session_id=session_id,
            start_time=start_time,
            agent_name="TestAgent",
            objectives=objectives,
            duration_seconds=3600,
            iterations_planned=1000,
            initial_parameters=parameters,
            current_parameters=parameters.copy(),
        )

        assert session.session_id == session_id
        assert session.start_time == start_time
        assert session.agent_name == "TestAgent"
        assert session.objectives == objectives
        assert session.duration_seconds == 3600
        assert session.iterations_planned == 1000
        assert session.iterations_completed == 0
        assert session.is_active is True
        assert session.progress_percentage == 0.0

    def test_session_active_status(self) -> None:
        """Test session active status calculation."""
        past_time = datetime.now(timezone.utc) - timedelta(seconds=7200)  # 2 hours ago
        session = TrainingSession(
            session_id="test",
            start_time=past_time,
            duration_seconds=3600,  # 1 hour
            iterations_planned=100,
        )

        # Should be inactive (duration exceeded)
        assert session.is_active is False

        # Should have correct elapsed time
        assert session.elapsed_time >= 3600

    def test_iteration_progress(self) -> None:
        """Test iteration-based progress calculation."""
        session = TrainingSession(
            session_id="test",
            start_time=datetime.now(timezone.utc),
            duration_seconds=3600,
            iterations_planned=100,
        )

        session.iterations_completed = 50
        assert session.progress_percentage == 50.0

        session.iterations_completed = 100
        assert session.progress_percentage == 100.0

        session.iterations_completed = 150
        assert session.progress_percentage == 100.0  # Capped at 100

    def test_performance_tracking(self) -> None:
        """Test performance history tracking."""
        session = TrainingSession(
            session_id="test",
            start_time=datetime.now(timezone.utc),
            iterations_planned=100,
        )

        # Add performance scores
        for i in range(10):
            session.update_performance(0.5 + i * 0.05)

        assert len(session.performance_history) == 10
        assert session.current_performance == 0.95

        # Test improvement trend
        session.update_performance(0.6)  # Lower score to create trend
        assert session.improvement_trend > 0  # Should be positive trend

    def test_parameter_updates(self) -> None:
        """Test parameter update functionality."""
        session = TrainingSession(
            session_id="test",
            start_time=datetime.now(timezone.utc),
        )

        original_params = {"learning_rate": 0.001, "exploration_rate": 0.1}
        session.current_parameters = original_params.copy()

        new_params = {"learning_rate": 0.002}
        session.update_parameters(new_params)

        assert session.current_parameters["learning_rate"] == 0.002
        assert (
            session.current_parameters["exploration_rate"] == 0.1
        )  # Should remain unchanged

    def test_session_to_dict(self) -> None:
        """Test session dictionary conversion."""
        start_time = datetime.now(timezone.utc)
        session = TrainingSession(
            session_id="test",
            start_time=start_time,
            agent_name="TestAgent",
            objectives=["Learn"],
            iterations_planned=100,
        )

        session_dict = session.to_dict()

        assert session_dict["session_id"] == "test"
        assert session_dict["start_time"] == start_time.isoformat()
        assert session_dict["agent_name"] == "TestAgent"
        assert session_dict["objectives"] == ["Learn"]
        assert session_dict["is_active"] is True
        assert "estimated_completion" in session_dict


class TestTrainingDecision:
    """Test training decision representation."""

    def test_decision_creation(self) -> None:
        """Test training decision creation."""
        decision_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        agent_action = AgentAction(
            timestamp=timestamp,
            action_type="analyze",
            parameters={"symbol": "AAPL"},
            result="test_result",
            confidence_score=0.7,
            success=True,
        )

        order_result = OrderResult(
            order_id="test_order",
            client_order_id=None,
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            filled_quantity=100,
            price=None,
            stop_price=None,
            avg_fill_price=150.0,
            status=OrderStatus.FILLED,
            timestamp=timestamp,
        )

        decision = TrainingDecision(
            decision_id=decision_id,
            timestamp=timestamp,
            session_id="test_session",
            agent_action=agent_action,
            order=order_result,
            market_data={"price": 150.0, "volume": 1000},
            decision_quality=0.8,
            reasoning="Technical analysis indicates bullish trend",
            market_drivers=["RSI oversold", "High volume"],
            performance_impact=0.1,
        )

        assert decision.decision_id == decision_id
        assert decision.agent_action == agent_action
        assert decision.order == order_result
        assert decision.decision_quality == 0.8
        assert "RSI oversold" in decision.market_drivers
        assert decision.performance_impact == 0.1

    def test_decision_to_dict(self) -> None:
        """Test decision dictionary conversion."""
        decision = TrainingDecision(
            decision_id="test",
            timestamp=datetime.now(timezone.utc),
            session_id="test_session",
            agent_action=AgentAction(
                timestamp=datetime.now(timezone.utc),
                action_type="wait",
                parameters={},
                result="waiting",
                confidence_score=0.5,
                success=True,
            ),
            order=None,
            market_data={},
            decision_quality=0.7,
            reasoning="Waiting for better entry",
        )

        decision_dict = decision.to_dict()

        assert decision_dict["decision_id"] == "test"
        assert decision_dict["session_id"] == "test_session"
        assert decision_dict["decision_quality"] == 0.7
        assert decision_dict["order_id"] is None  # No order
        assert "reasoning" in decision_dict


class TestPerformanceTracker:
    """Test performance tracking functionality."""

    def test_tracker_initialization(self) -> None:
        """Test performance tracker initialization."""
        tracker = PerformanceTracker()

        assert "decision_quality" in tracker.performance_history
        assert "profit_loss" in tracker.performance_history
        assert "win_rate" in tracker.performance_history
        assert tracker.decisions == []
        assert tracker.current_session is None

    def test_session_tracking(self) -> None:
        """Test session tracking functionality."""
        tracker = PerformanceTracker()
        session = TrainingSession(
            session_id="test",
            start_time=datetime.now(timezone.utc),
        )

        tracker.start_session(session)
        assert tracker.current_session == session

    def test_decision_recording(self) -> None:
        """Test decision recording and metrics update."""
        tracker = PerformanceTracker()
        session = TrainingSession(
            session_id="test",
            start_time=datetime.now(timezone.utc),
        )
        tracker.start_session(session)

        decision = TrainingDecision(
            decision_id="test",
            timestamp=datetime.now(timezone.utc),
            session_id="test",
            agent_action=AgentAction(
                timestamp=datetime.now(timezone.utc),
                action_type="analyze",
                parameters={},
                result="analysis",
                confidence_score=0.6,
                success=True,
            ),
            order=None,
            market_data={},
            decision_quality=0.8,
            reasoning="Test",
        )

        tracker.record_decision(decision)

        assert len(tracker.decisions) == 1
        assert len(tracker.performance_history["decision_quality"]) == 1
        assert tracker.performance_history["decision_quality"][0] == 0.8
        assert session.current_performance is not None

    def test_improvement_trend_calculation(self) -> None:
        """Test improvement trend calculation."""
        tracker = PerformanceTracker()

        # Create improving performance history
        for i in range(30):
            decision = TrainingDecision(
                decision_id=f"test_{i}",
                timestamp=datetime.now(timezone.utc),
                session_id="test",
                agent_action=AgentAction(
                    timestamp=datetime.now(timezone.utc),
                    action_type="analyze",
                    parameters={},
                    result="analysis",
                    confidence_score=0.6,
                    success=True,
                ),
                order=None,
                market_data={},
                decision_quality=0.5 + (i * 0.01),  # Improving quality
                reasoning="Test",
            )
            tracker.record_decision(decision)

        trend = tracker.get_improvement_trend()
        assert trend > 0  # Should show positive trend

    def test_weakness_identification(self) -> None:
        """Test weakness identification functionality."""
        tracker = PerformanceTracker()

        # Create decisions with poor quality
        for i in range(10):
            decision = TrainingDecision(
                decision_id=f"test_{i}",
                timestamp=datetime.now(timezone.utc),
                session_id="test",
                agent_action=AgentAction(
                    timestamp=datetime.now(timezone.utc),
                    action_type="analyze",
                    parameters={},
                    result="analysis",
                    confidence_score=0.6,
                    success=True,
                ),
                order=None,
                market_data={},
                decision_quality=0.3,  # Low quality
                reasoning="Test",
            )
            tracker.record_decision(decision)

        weaknesses = tracker.identify_weaknesses()
        assert len(weaknesses) > 0
        assert any("Low decision quality" in w for w in weaknesses)

    def test_current_metrics(self) -> None:
        """Test current metrics calculation."""
        tracker = PerformanceTracker()

        # Add some decisions
        for i in range(5):
            decision = TrainingDecision(
                decision_id=f"test_{i}",
                timestamp=datetime.now(timezone.utc),
                session_id="test",
                agent_action=AgentAction(
                    timestamp=datetime.now(timezone.utc),
                    action_type="analyze",
                    parameters={},
                    result="analysis",
                    confidence_score=0.6,
                    success=True,
                ),
                order=None,
                market_data={},
                decision_quality=0.6 + (i * 0.05),
                reasoning="Test",
            )
            tracker.record_decision(decision)

        metrics = tracker.get_current_metrics()
        assert "decision_quality" in metrics
        assert "improvement_trend" in metrics
        assert "total_decisions" in metrics
        assert metrics["total_decisions"] == 5


class TestModelOptimizer:
    """Test model optimization functionality."""

    def test_optimizer_initialization(self) -> None:
        """Test model optimizer initialization."""
        optimizer = ModelOptimizer()

        assert optimizer.optimization_strategy == "bayesian"
        assert optimizer.optimization_history == []
        assert optimizer.best_performance == 0.0
        assert optimizer.best_parameters == {}

    def test_parameter_optimization(self) -> None:
        """Test parameter optimization functionality."""
        optimizer = ModelOptimizer(optimization_strategy="gradient")

        current_params = {"learning_rate": 0.001, "exploration_rate": 0.1}
        feedback = {"overall_score": 0.7, "improvement_trend": 10.0}
        constraints = {"learning_rate": {"min": 0.0001, "max": 0.01}}

        optimized_params = optimizer.optimize_parameters(
            current_params, feedback, constraints
        )

        assert "learning_rate" in optimized_params
        assert "exploration_rate" in optimized_params
        assert (
            constraints["learning_rate"]["min"]
            <= optimized_params["learning_rate"]
            <= constraints["learning_rate"]["max"]
        )

    def test_best_performance_tracking(self) -> None:
        """Test best performance tracking."""
        optimizer = ModelOptimizer()

        params = {"learning_rate": 0.001}
        feedback1 = {"overall_score": 0.6}
        feedback2 = {"overall_score": 0.8}

        # First optimization
        optimizer.optimize_parameters(params, feedback1)
        assert optimizer.best_performance == 0.6

        # Second optimization with better performance
        optimizer.optimize_parameters(params, feedback2)
        assert optimizer.best_performance == 0.8
        assert optimizer.best_parameters == params

    def test_improvement_suggestions(self) -> None:
        """Test improvement suggestion generation."""
        optimizer = ModelOptimizer()

        # Declining performance
        declining_data: list[float] = [0.8, 0.7, 0.6, 0.5, 0.4]
        suggestions = optimizer.suggest_improvements(declining_data)
        assert len(suggestions) > 0
        assert len(suggestions) > 0  # Just check we get some suggestions

        # Good performance
        good_data: list[float] = [0.7, 0.75, 0.8, 0.85, 0.9]
        suggestions = optimizer.suggest_improvements(good_data)
        assert len(suggestions) > 0
        assert any("good performance" in s.lower() for s in suggestions)

    def test_bayesian_optimization(self) -> None:
        """Test Bayesian optimization strategy."""
        optimizer = ModelOptimizer(optimization_strategy="bayesian")

        params = {"learning_rate": 0.001}
        feedback = {"improvement_trend": 5.0}

        optimized = optimizer.optimize_parameters(params, feedback)
        assert optimized != params  # Should be different

    def test_grid_search_optimization(self) -> None:
        """Test grid search optimization strategy."""
        optimizer = ModelOptimizer(optimization_strategy="grid_search")

        params = {"learning_rate": 0.001}
        feedback = {"overall_score": 0.4}

        optimized = optimizer.optimize_parameters(params, feedback)
        assert "learning_rate" in optimized
        # Should decrease learning rate for poor performance
        assert optimized["learning_rate"] < params["learning_rate"]

    def test_optimization_history(self) -> None:
        """Test optimization history tracking."""
        optimizer = ModelOptimizer()

        params = {"learning_rate": 0.001}
        feedback = {"overall_score": 0.7}

        optimizer.optimize_parameters(params, feedback)

        assert len(optimizer.optimization_history) == 1
        history_entry = optimizer.optimization_history[0]
        assert "timestamp" in history_entry
        assert "old_parameters" in history_entry
        assert "new_parameters" in history_entry
        assert "performance_score" in history_entry


class TestAgentTrainingMode:
    """Test AI training mode functionality."""

    @pytest.fixture
    def mock_config(self) -> None:
        """Create mock configuration."""
        config = Mock(spec=QuantChainConfig)
        config.get.return_value = False
        return config

    @pytest.fixture
    def training_executor(self, mock_config):
        """Create training executor for testing."""
        return AgentTrainingMode(
            initial_cash=100000.0,
            config=mock_config,
            learning_objectives=["Improve decision quality", "Learn market drivers"],
            track_performance=True,
            optimize_parameters=True,
        )

    def test_executor_initialization(self, training_executor) -> None:
        """Test training executor initialization."""
        assert training_executor.paper_executor is not None
        assert training_executor.performance_tracker is not None
        assert training_executor.model_optimizer is not None
        assert training_executor.market_driver_analysis is not None
        assert training_executor.learning_objectives == [
            "Improve decision quality",
            "Learn market drivers",
        ]
        assert training_executor.track_performance is True
        assert training_executor.optimize_parameters is True

    def test_start_training_session(self, training_executor) -> None:
        """Test starting a training session."""
        objectives: list[float] = ["Optimize risk management"]
        agent_params = {"learning_rate": 0.001}

        session = training_executor.start_training_session(
            symbols=["AAPL", "MSFT"],
            objectives=objectives,
            duration_seconds=1800,
            iterations=500,
            agent_parameters=agent_params,
        )

        assert session is not None
        assert all(obj in session.objectives for obj in objectives)
        assert session.duration_seconds == 1800
        assert session.iterations_planned == 500
        assert session.initial_parameters == agent_params
        assert session.current_parameters == agent_params
        assert session.is_active is True

        # Check executor state
        assert training_executor.current_session == session
        assert len(training_executor.training_history) == 1

    def test_training_execution(self, training_executor) -> None:
        """Test training execution with iterations."""
        # Start session
        session = training_executor.start_training_session(
            symbols=["AAPL"],
            iterations=20,
        )

        market_data = {"AAPL": {"price": 150.0, "volume": 1000}}

        # Execute training
        results = training_executor.train_agent(
            market_data=market_data,
            iterations=10,
        )

        assert "iterations_completed" in results
        assert results["iterations_completed"] == 10
        assert "performance_improvement" in results
        assert "final_metrics" in results

        # Check session updates
        assert session.iterations_completed == 10

    def test_performance_evaluation(self, training_executor) -> None:
        """Test performance evaluation on scenarios."""
        # Start session and train a bit
        training_executor.start_training_session(["AAPL"])
        training_executor.train_agent(iterations=5)

        test_scenarios: list[float] = ["bull_market", "bear_market", "high_volatility"]
        evaluation_results = training_executor.evaluate_performance(test_scenarios)

        assert len(evaluation_results) == 3
        for scenario in test_scenarios:
            assert scenario in evaluation_results
            assert "score" in evaluation_results[scenario]

    def test_parameter_fine_tuning(self, training_executor) -> None:
        """Test parameter fine-tuning functionality."""
        # Start session
        training_executor.start_training_session(["AAPL"])

        # Mock evaluation results
        evaluation_results = {
            "bull_market": {"score": 0.8},
            "bear_market": {"score": 0.6},
        }

        constraints = {"learning_rate": {"min": 0.0001, "max": 0.01}}

        # Fine-tune parameters
        optimized_params = training_executor.fine_tune_parameters(
            evaluation_results,
            constraints=constraints,
        )

        assert isinstance(optimized_params, dict)
        if "learning_rate" in optimized_params:
            assert (
                constraints["learning_rate"]["min"]
                <= optimized_params["learning_rate"]
                <= constraints["learning_rate"]["max"]
            )

    def test_training_progress(self, training_executor) -> None:
        """Test training progress reporting."""
        # Start session and train
        training_executor.start_training_session(["AAPL"], iterations=50)
        training_executor.train_agent(iterations=20)

        progress = training_executor.get_training_progress()

        assert "session" in progress
        assert "current_metrics" in progress
        assert "suggestions" in progress
        assert "weaknesses" in progress
        assert progress["session"]["iterations_completed"] == 20

    def test_export_improved_agent(self, training_executor) -> None:
        """Test exporting improved agent state."""
        # Start session and train
        training_executor.start_training_session(["AAPL"])
        training_executor.train_agent(iterations=10)

        # Export agent
        export_data = training_executor.export_improved_agent(
            include_training_history=True,
            include_optimized_params=True,
        )

        assert "agent_name" in export_data
        assert "training_session_id" in export_data
        assert "final_performance" in export_data
        assert "improvement_made" in export_data

    def test_end_training_session(self, training_executor) -> None:
        """Test ending a training session."""
        # Start session and train
        training_executor.start_training_session(["AAPL"])
        training_executor.train_agent(iterations=5)

        # End session
        report = training_executor.end_training_session()

        assert "session" in report
        assert "final_performance" in report
        assert "paper_trading_metrics" in report
        assert "training_summary" in report
        assert "ready_for_live" in report

        # Session should be ended
        assert training_executor.current_session is None

    def test_delegate_methods(self, training_executor) -> None:
        """Test delegated methods to paper executor."""
        # Account info
        account = training_executor.get_account()
        assert account.account_id == "PAPER_TRADING"
        assert account.cash == 100000.0

        # Market status
        assert training_executor.is_market_open() is True

        # Performance metrics
        metrics = training_executor.get_performance_metrics()
        assert metrics is not None

    def test_market_price_setting(self, training_executor) -> None:
        """Test market price setting functionality."""
        training_executor.set_market_price("AAPL", 150.0)
        assert training_executor.market_prices["AAPL"] == 150.0

    def test_reset_functionality(self, training_executor) -> None:
        """Test reset functionality."""
        # Start session and train
        training_executor.start_training_session(["AAPL"])
        training_executor.train_agent(iterations=5)
        training_executor.set_market_price("AAPL", 150.0)

        # Verify state exists
        assert training_executor.current_session is not None
        assert len(training_executor.decision_history) > 0

        # Reset
        training_executor.reset()

        # Verify reset
        assert training_executor.current_session is None
        assert len(training_executor.decision_history) == 0
        assert training_executor.get_account().cash == 100000.0

    def test_error_handling(self, training_executor) -> None:
        """Test error handling in training mode."""
        # Test error without session
        with pytest.raises(ValueError, match="No active training session"):
            AgentTrainingMode().get_training_progress()

        with pytest.raises(ValueError, match="No active training session"):
            AgentTrainingMode().end_training_session()

        # Test error when no session to evaluate
        with pytest.raises(ValueError, match="No active training session"):
            AgentTrainingMode().fine_tune_parameters({})


class TestAgentTrainingModeIntegration:
    """Integration tests for AI training mode."""

    @pytest.fixture
    def mock_config(self) -> None:
        """Create mock configuration."""
        config = Mock(spec=QuantChainConfig)
        config.get.return_value = False
        return config

    @pytest.fixture
    def training_executor(self, mock_config):
        """Create training executor for testing."""
        return AgentTrainingMode(
            initial_cash=100000.0,
            config=mock_config,
            learning_objectives=["Improve decision quality", "Learn market drivers"],
            track_performance=True,
            optimize_parameters=True,
        )

    def test_complete_training_workflow(self, training_executor) -> None:
        """Test complete training workflow."""
        # Start training session
        session = training_executor.start_training_session(
            symbols=["AAPL", "MSFT"],
            objectives=["Learn technical analysis"],
            iterations=50,
        )

        # Execute training
        results = training_executor.train_agent(iterations=30)

        # Evaluate performance
        evaluation = training_executor.evaluate_performance(
            [
                "bull_market",
                "bear_market",
            ]
        )

        # Fine-tune parameters
        optimized_params = training_executor.fine_tune_parameters(evaluation)

        # Get progress
        progress = training_executor.get_training_progress()

        # Export improved agent
        export_data = training_executor.export_improved_agent()

        # End session
        report = training_executor.end_training_session()

        # Verify results
        assert session.session_id == progress["session"]["session_id"]
        assert results["iterations_completed"] == 30
        assert len(evaluation) == 2
        assert isinstance(optimized_params, dict)
        assert export_data["training_session_id"] == session.session_id
        assert report["session"]["session_id"] == session.session_id

    def test_multiple_training_sessions(self, training_executor) -> None:
        """Test multiple training sessions."""
        # First session
        session1 = training_executor.start_training_session(["AAPL"], iterations=20)
        training_executor.train_agent(iterations=10)
        report1 = training_executor.end_training_session()

        # Second session
        session2 = training_executor.start_training_session(["MSFT"], iterations=30)
        training_executor.train_agent(iterations=15)
        report2 = training_executor.end_training_session()

        # Verify both sessions are tracked
        assert len(training_executor.training_history) == 2
        assert report1["session"]["session_id"] == session1.session_id
        assert report2["session"]["session_id"] == session2.session_id
        assert session1.session_id != session2.session_id
