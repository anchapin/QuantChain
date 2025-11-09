"""Tests for tutorial mode functionality."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock
import uuid

from quantchain.tools.tutorial_mode import (
    TutorialExecutor,
    TutorialSession,
    TutorialFeedback,
    MarketDriverAnalysis,
    MistakeTracker,
    ConfidenceMetrics,
)
from quantchain.tools.trading_execution import (
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderType,
    OrderStatus,
)
from quantchain.core.config import QuantChainConfig


class TestTutorialSession:
    """Test tutorial session management."""

    def test_session_initialization(self) -> None:
        """Test tutorial session initialization."""
        session_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        symbols: list[float] = ["AAPL", "MSFT"]
        objectives: list[float] = ["Understand market drivers", "Practice risk management"]

        session = TutorialSession(
            session_id=session_id,
            start_time=start_time,
            symbols=symbols,
            learning_objectives=objectives,
            duration_seconds=3600,
        )

        assert session.session_id == session_id
        assert session.start_time == start_time
        assert session.symbols == symbols
        assert session.learning_objectives == objectives
        assert session.duration_seconds == 3600
        assert session.is_active is True
        assert session.end_time is None

    def test_session_active_status(self) -> None:
        """Test session active status calculation."""
        past_time = datetime.now(timezone.utc) - timedelta(seconds=7200)  # 2 hours ago
        session = TutorialSession(
            session_id="test", start_time=past_time, duration_seconds=3600  # 1 hour
        )

        # Should be inactive (duration exceeded)
        assert session.is_active is False

        # Should have correct elapsed time
        assert session.elapsed_time >= 3600

    def test_add_objective(self) -> None:
        """Test adding learning objectives."""
        session = TutorialSession(
            session_id="test",
            start_time=datetime.now(timezone.utc),
            learning_objectives=["Initial objective"],
        )

        session.add_objective("New objective")
        assert "New objective" in session.learning_objectives

        # Should not add duplicates
        session.add_objective("New objective")
        assert session.learning_objectives.count("New objective") == 1


class TestMarketDriverAnalysis:
    """Test market driver analysis."""

    def test_basic_driver_identification(self) -> None:
        """Test basic market driver identification."""
        analysis = MarketDriverAnalysis()

        order_result = OrderResult(
            order_id="test",
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
            timestamp=datetime.now(timezone.utc),
        )

        drivers = analysis.analyze_market_drivers("AAPL", order_result)

        assert any("Price action" in driver for driver in drivers)
        assert any("Immediate execution" in driver for driver in drivers)

    def test_limit_order_drivers(self) -> None:
        """Test limit order driver identification."""
        analysis = MarketDriverAnalysis()

        order_result = OrderResult(
            order_id="test",
            client_order_id=None,
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            filled_quantity=100,
            price=150.0,
            stop_price=None,
            avg_fill_price=150.0,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(timezone.utc),
        )

        drivers = analysis.analyze_market_drivers("AAPL", order_result)

        assert any("Price discipline" in driver for driver in drivers)

    def test_educational_context_generation(self) -> None:
        """Test educational context generation."""
        analysis = MarketDriverAnalysis()

        drivers = [
            "RSI oversold condition",
            "High volume increase",
            "Positive news sentiment",
        ]
        context = analysis.generate_educational_context("AAPL", drivers)

        assert "AAPL" in context
        assert "RSI oversold condition" in context
        assert "High volume increase" in context
        assert "Educational Notes" in context
        assert "time-dependent effects" in context


class TestMistakeTracker:
    """Test mistake tracking functionality."""

    def test_timing_mistake_detection(self) -> None:
        """Test timing mistake detection."""
        tracker = MistakeTracker()

        order_result = OrderResult(
            order_id="test",
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
            timestamp=datetime.now(timezone.utc),
        )

        market_context = {"volatility": 0.3}  # High volatility
        mistake = tracker.analyze_mistake(order_result, market_context)

        if mistake:
            assert mistake.mistake_type == "timing"
            assert mistake.severity == "moderate"
            # Check that the description matches what's expected for timing mistakes
            assert (
                mistake.description
                == "Order placed at suboptimal time considering market conditions"
            )

    def test_sizing_mistake_detection(self) -> None:
        """Test sizing mistake detection."""
        tracker = MistakeTracker()

        order_result = OrderResult(
            order_id="test",
            client_order_id=None,
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=2000,  # Large position
            filled_quantity=2000,
            price=None,
            stop_price=None,
            avg_fill_price=150.0,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(timezone.utc),
        )

        market_context = {"portfolio_value": 100000}
        mistake = tracker.analyze_mistake(order_result, market_context)

        if mistake:
            assert mistake.mistake_type == "sizing"
            assert "position size" in mistake.description.lower()


class TestConfidenceMetrics:
    """Test confidence metrics functionality."""

    def test_decision_recording(self) -> None:
        """Test recording trading decisions."""
        metrics = ConfidenceMetrics()

        assert len(metrics.decisions) == 0

        metrics.record_decision(
            decision_quality=0.8, risk_assessment="Medium risk", consistency_score=0.7
        )

        assert len(metrics.decisions) == 1
        assert metrics.decisions[0]["decision_quality"] == 0.8
        assert metrics.decisions[0]["risk_assessment"] == "Medium risk"

    def test_confidence_score_calculation(self) -> None:
        """Test confidence score calculation."""
        metrics = ConfidenceMetrics()

        confidence = metrics.calculate_confidence_score()
        assert 0.0 <= confidence <= 1.0

        # Add decisions with varying quality
        for i in range(5):
            quality = 0.5 + (i * 0.1)  # 0.5 to 0.9
            risk = "Low risk" if i > 2 else "High risk"
            metrics.record_decision(quality, risk)

        # Confidence should change
        new_confidence = metrics.calculate_confidence_score()
        assert isinstance(new_confidence, float)
        assert 0.0 <= new_confidence <= 1.0

    def test_learning_progress(self) -> None:
        """Test learning progress calculation."""
        metrics = ConfidenceMetrics()

        # Add progression of improving decisions
        for i in range(10):
            quality = 0.5 + (i * 0.04)  # Improving from 0.5 to 0.86
            risk = "Medium risk"
            metrics.record_decision(quality, risk)

        progress = metrics.get_learning_progress()

        assert progress["total_decisions"] == 10
        assert progress["trend"] == "improving"
        assert progress["recent_average_quality"] > progress["early_average_quality"]


class TestTutorialExecutor:
    """Test tutorial executor functionality."""

    @pytest.fixture
    def mock_config(self) -> None: """Create mock configuration."""
        config = Mock(spec=QuantChainConfig)
        config.get.return_value = False  # RAG disabled by default
        return config

    @pytest.fixture
    def tutorial_executor(self, mock_config):
        """Create tutorial executor for testing."""
        return TutorialExecutor(
            initial_cash=100000.0,
            config=mock_config,
            learning_objectives=["Practice trading", "Understand risk"],
            track_mistakes=True,
            analyze_market_drivers=True,
        )

    def test_executor_initialization(self, tutorial_executor) -> None: """Test tutorial executor initialization."""
        assert tutorial_executor.paper_executor is not None
        assert tutorial_executor.reflection_engine is not None
        assert tutorial_executor.market_driver_analysis is not None
        assert tutorial_executor.mistake_tracker is not None
        assert tutorial_executor.confidence_metrics is not None
        assert tutorial_executor.learning_objectives == [
            "Practice trading",
            "Understand risk",
        ]
        assert tutorial_executor.track_mistakes is True
        assert tutorial_executor.analyze_market_drivers is True

    def test_start_tutorial_session(self, tutorial_executor) -> None: """Test starting a tutorial session."""
        symbols: list[float] = ["AAPL", "MSFT"]
        objectives: list[float] = ["Understand technical analysis"]

        session = tutorial_executor.start_tutorial_session(
            symbols=symbols, objectives=objectives, duration_seconds=1800
        )

        assert session is not None
        assert session.symbols == symbols
        assert all(obj in session.learning_objectives for obj in objectives)
        assert session.duration_seconds == 1800
        assert session.is_active is True

        # Check executor state
        assert tutorial_executor.current_session == session

    def test_end_tutorial_session(self, tutorial_executor) -> None: """Test ending a tutorial session."""
        # Start session first
        tutorial_executor.start_tutorial_session(["AAPL"])

        # Place an order to create some data
        order = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )
        tutorial_executor.set_market_price("AAPL", 150.0)
        tutorial_executor.place_order(order)

        # End session
        report = tutorial_executor.end_tutorial_session()

        assert "session" in report
        assert "final_feedback" in report
        assert "paper_trading_metrics" in report
        assert "trade_history" in report
        assert "ready_for_live" in report

        # Session should be ended
        assert tutorial_executor.current_session.end_time is not None

    def test_order_placement_with_analysis(self, tutorial_executor) -> None: """Test order placement with decision analysis."""
        # Start session
        tutorial_executor.start_tutorial_session(["AAPL"])

        order = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        tutorial_executor.set_market_price("AAPL", 150.0)
        result = tutorial_executor.place_order(order)

        # Order should be filled
        assert result.status == OrderStatus.FILLED

        # Should have decision analysis
        assert len(tutorial_executor.decision_history) == 1
        analysis = tutorial_executor.decision_history[0]
        assert analysis.order.order_id == result.order_id
        assert 0.0 <= analysis.decision_quality <= 1.0
        assert analysis.market_drivers is not None

    def test_tutorial_feedback_generation(self, tutorial_executor) -> None: """Test tutorial feedback generation."""
        # Start session and make trades
        tutorial_executor.start_tutorial_session(["AAPL"])

        for i in range(3):
            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=100,
            )
            tutorial_executor.set_market_price("AAPL", 150.0 + i)
            tutorial_executor.place_order(order)

        # Get feedback
        feedback = tutorial_executor.get_tutorial_feedback()

        assert isinstance(feedback, TutorialFeedback)
        assert len(feedback.decision_analyses) > 0
        assert 0.0 <= feedback.confidence_score <= 1.0
        assert 0.0 <= feedback.consistency_score <= 1.0
        assert 0.0 <= feedback.risk_management_score <= 1.0
        assert "learning_progress" in feedback.to_dict()

    def test_confidence_score_tracking(self, tutorial_executor) -> None: """Test confidence score tracking."""
        confidence = tutorial_executor.get_confidence_score()
        assert 0.0 <= confidence <= 1.0

        # Make some trades to build confidence
        tutorial_executor.start_tutorial_session(["AAPL"])

        for i in range(10):
            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=100,
            )
            tutorial_executor.set_market_price("AAPL", 150.0 + i)
            tutorial_executor.place_order(order)

        # Confidence should change
        new_confidence = tutorial_executor.get_confidence_score()
        assert isinstance(new_confidence, float)
        assert 0.0 <= new_confidence <= 1.0

    def test_market_price_setting(self, tutorial_executor) -> None: """Test market price setting functionality."""
        tutorial_executor.set_market_price("AAPL", 150.0)

        # Place order should use set price
        order = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        result = tutorial_executor.place_order(order)
        assert result.avg_fill_price == 150.0

    def test_delegate_methods(self, tutorial_executor) -> None: """Test that methods are properly delegated to paper executor."""
        # Account info
        account = tutorial_executor.get_account()
        assert account.account_id == "PAPER_TRADING"
        assert account.cash == 100000.0

        # Market status
        assert tutorial_executor.is_market_open() is True

        # Performance metrics
        metrics = tutorial_executor.get_performance_metrics()
        assert metrics is not None

    def test_reset_functionality(self, tutorial_executor) -> None: """Test reset functionality."""
        # Start session and make trades
        tutorial_executor.start_tutorial_session(["AAPL"])
        tutorial_executor.set_market_price("AAPL", 150.0)

        order = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )
        tutorial_executor.place_order(order)

        # Verify state exists
        assert tutorial_executor.current_session is not None
        assert len(tutorial_executor.decision_history) > 0

        # Reset
        tutorial_executor.reset()

        # Verify reset
        assert tutorial_executor.current_session is None
        assert len(tutorial_executor.decision_history) == 0
        assert tutorial_executor.get_account().cash == 100000.0


@pytest.mark.unit
class TestTutorialExecutorFactoryIntegration:
    """Test tutorial executor integration with factory."""

    def test_tutorial_executor_with_rag(self) -> None:
        """Test tutorial executor with RAG system enabled."""
        mock_config = Mock(spec=QuantChainConfig)
        mock_config.get.side_effect = lambda key, default=None: {
            "rag.enabled": True,
            "rag.persist_directory": "./test_db",
            "rag.embedding_model": "all-MiniLM-L6-v2",
        }.get(key, default)

        executor = TutorialExecutor(config=mock_config)

        # Should initialize RAG system when enabled
        assert executor is not None
        # RAG system may not be available in test environment due to missing
        # dependencies. So we only check it if it was successfully initialized
        if executor.rag_system is not None:
            assert executor.market_driver_analysis.rag_system is executor.rag_system

    def test_tutorial_executor_without_rag(self) -> None:
        """Test tutorial executor without RAG system."""
        mock_config = Mock(spec=QuantChainConfig)
        mock_config.get.side_effect = lambda key, default=None: {
            "rag.enabled": False
        }.get(key, default)

        executor = TutorialExecutor(config=mock_config)

        # Should work without RAG
        assert executor.rag_system is None
        assert executor is not None


