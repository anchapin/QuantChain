"""Tests for tutorial mode functionality."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
import uuid

from quantchain.tools.tutorial_mode import (
    TutorialExecutor,
    TrainingSession,
    TradingMistake,
    DecisionAnalysis,
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
    Position,
)
from quantchain.core.config import QuantChainConfig


class TestTrainingSession:
    """Test training session management."""
    
    def test_session_initialization(self):
        """Test training session initialization."""
        session_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        symbols = ["AAPL", "MSFT"]
        objectives = ["Understand market drivers", "Practice risk management"]
        
        session = TrainingSession(
            session_id=session_id,
            start_time=start_time,
            symbols=symbols,
            learning_objectives=objectives,
            duration_seconds=3600
        )
        
        assert session.session_id == session_id
        assert session.start_time == start_time
        assert session.symbols == symbols
        assert session.learning_objectives == objectives
        assert session.duration_seconds == 3600
        assert session.is_active is True
        assert session.end_time is None
    
    def test_session_active_status(self):
        """Test session active status calculation."""
        past_time = datetime.now(timezone.utc) - timedelta(seconds=7200)  # 2 hours ago
        session = TrainingSession(
            session_id="test",
            start_time=past_time,
            duration_seconds=3600  # 1 hour
        )
        
        # Should be inactive (duration exceeded)
        assert session.is_active is False
        
        # Should have correct elapsed time
        assert session.elapsed_time >= 3600
    
    def test_add_objective(self):
        """Test adding learning objectives."""
        session = TrainingSession(
            session_id="test",
            start_time=datetime.now(timezone.utc),
            learning_objectives=["Initial objective"]
        )
        
        session.add_objective("New objective")
        assert "New objective" in session.learning_objectives
        
        # Should not add duplicates
        session.add_objective("New objective")
        assert session.learning_objectives.count("New objective") == 1
    
    def test_session_to_dict(self):
        """Test session dictionary conversion."""
        start_time = datetime.now(timezone.utc)
        session = TrainingSession(
            session_id="test",
            start_time=start_time,
            symbols=["AAPL"],
            learning_objectives=["Learn"]
        )
        
        session_dict = session.to_dict()
        
        assert session_dict["session_id"] == "test"
        assert session_dict["start_time"] == start_time.isoformat()
        assert session_dict["symbols"] == ["AAPL"]
        assert session_dict["learning_objectives"] == ["Learn"]
        assert session_dict["is_active"] is True
    
    def test_end_session(self):
        """Test ending a session."""
        session = TrainingSession(
            session_id="test",
            start_time=datetime.now(timezone.utc)
        )
        
        end_time = datetime.now(timezone.utc)
        session.end_time = end_time
        
        assert session.is_active is False
        assert session.end_time == end_time


class TestMarketDriverAnalysis:
    """Test market driver analysis."""
    
    def test_basic_driver_identification(self):
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
            timestamp=datetime.now(timezone.utc)
        )
        
        drivers = analysis.analyze_market_drivers("AAPL", order_result)
        
        assert any("Price action" in driver for driver in drivers)
        assert any("Immediate execution" in driver for driver in drivers)
    
    def test_limit_order_drivers(self):
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
            timestamp=datetime.now(timezone.utc)
        )
        
        drivers = analysis.analyze_market_drivers("AAPL", order_result)
        
        assert any("Price discipline" in driver for driver in drivers)
    
    def test_position_sizing_drivers(self):
        """Test position sizing driver identification."""
        analysis = MarketDriverAnalysis()
        
        # Large position
        large_order = OrderResult(
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
            timestamp=datetime.now(timezone.utc)
        )
        
        drivers = analysis.analyze_market_drivers("AAPL", large_order)
        assert any("large position" in driver.lower() for driver in drivers)
        
        # Small position
        small_order = OrderResult(
            order_id="test2",
            client_order_id=None,
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=50,  # Small position
            filled_quantity=50,
            price=None,
            stop_price=None,
            avg_fill_price=150.0,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(timezone.utc)
        )
        
        drivers = analysis.analyze_market_drivers("AAPL", small_order)
        assert any("conservative position" in driver.lower() for driver in drivers)
    
    def test_educational_context_generation(self):
        """Test educational context generation."""
        analysis = MarketDriverAnalysis()
        
        drivers = ["RSI oversold condition", "High volume increase", "Positive news sentiment"]
        context = analysis.generate_educational_context("AAPL", drivers)
        
        assert "AAPL" in context
        assert "RSI oversold condition" in context
        assert "High volume increase" in context
        assert "Educational Notes" in context
        assert "time-dependent effects" in context
    
    def test_rag_integration(self):
        """Test RAG system integration."""
        mock_rag = Mock()
        mock_rag.retrieve_relevant_data.return_value = [
            Mock(
                data_type="technical",
                symbol="AAPL",
                content={
                    "indicators": {
                        "rsi": 25,  # Oversold
                        "macd_signal": True,
                        "volume_change": 0.3
                    }
                }
            )
        ]
        
        analysis = MarketDriverAnalysis(mock_rag)
        
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
            timestamp=datetime.now(timezone.utc)
        )
        
        drivers = analysis.analyze_market_drivers("AAPL", order_result)
        
        mock_rag.retrieve_relevant_data.assert_called_once()
        assert any("Oversold RSI" in driver for driver in drivers)
        assert any("MACD signal" in driver for driver in drivers)


class TestMistakeTracker:
    """Test mistake tracking functionality."""
    
    def test_timing_mistake_detection(self):
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
            timestamp=datetime.now(timezone.utc)
        )
        
        market_context = {"volatility": 0.3}  # High volatility
        mistake = tracker.analyze_mistake(order_result, market_context)
        
        if mistake:
            assert mistake.mistake_type == "timing"
            assert mistake.severity == "moderate"
            assert "timing" in mistake.description.lower()
    
    def test_sizing_mistake_detection(self):
        """Test sizing mistake detection."""
        tracker = MistakeTracker()
        
        order_result = OrderResult(
            order_id="test",
            client_order_id=None,
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=500,  # Large position
            filled_quantity=500,
            price=None,
            stop_price=None,
            avg_fill_price=150.0,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(timezone.utc)
        )
        
        market_context = {"portfolio_value": 100000}
        mistake = tracker.analyze_mistake(order_result, market_context)
        
        if mistake:
            assert mistake.mistake_type == "sizing"
            assert "position size" in mistake.description.lower()
    
    def test_risk_mistake_detection(self):
        """Test risk management mistake detection."""
        tracker = MistakeTracker()
        
        order_result = OrderResult(
            order_id="test",
            client_order_id=None,
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1000,  # Very large position
            filled_quantity=1000,
            price=None,
            stop_price=None,
            avg_fill_price=150.0,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(timezone.utc)
        )
        
        market_context = {"portfolio_value": 100000, "volatility": 0.4}
        mistake = tracker.analyze_mistake(order_result, market_context)
        
        if mistake:
            assert mistake.mistake_type == "risk_management"
            assert mistake.severity == "critical"
    
    def test_mistake_pattern_tracking(self):
        """Test mistake pattern tracking."""
        tracker = MistakeTracker()
        
        # Create multiple mistakes of same type
        for i in range(3):
            order_result = OrderResult(
                order_id=f"test_{i}",
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
                timestamp=datetime.now(timezone.utc)
            )
            
            market_context = {"volatility": 0.3}  # High volatility
            tracker.analyze_mistake(order_result, market_context)
        
        patterns = tracker.get_mistake_patterns()
        recommendations = tracker.get_learning_recommendations()
        
        assert patterns  # Should have detected patterns
        assert recommendations  # Should have recommendations
    
    def test_learning_recommendations(self):
        """Test learning recommendations generation."""
        tracker = MistakeTracker()
        
        # Create timing mistakes
        for i in range(3):
            order_result = OrderResult(
                order_id=f"test_{i}",
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
                timestamp=datetime.now(timezone.utc)
            )
            
            market_context = {"volatility": 0.3}
            mistake = tracker.analyze_mistake(order_result, market_context)
            if mistake:
                mistake.mistake_type = "timing"
        
        recommendations = tracker.get_learning_recommendations()
        
        assert any("timing" in rec.lower() for rec in recommendations)


class TestConfidenceMetrics:
    """Test confidence metrics functionality."""
    
    def test_decision_recording(self):
        """Test recording trading decisions."""
        metrics = ConfidenceMetrics()
        
        assert len(metrics.decisions) == 0
        
        metrics.record_decision(
            decision_quality=0.8,
            risk_assessment="Medium risk",
            consistency_score=0.7
        )
        
        assert len(metrics.decisions) == 1
        assert metrics.decisions[0]["decision_quality"] == 0.8
        assert metrics.decisions[0]["risk_assessment"] == "Medium risk"
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation."""
        metrics = ConfidenceMetrics()
        
        # No decisions should return 0
        assert metrics.calculate_confidence_score() == 0.0
        
        # Add decisions with varying quality
        for i in range(5):
            quality = 0.5 + (i * 0.1)  # 0.5 to 0.9
            risk = "Low risk" if i > 2 else "High risk"
            metrics.record_decision(quality, risk)
        
        confidence = metrics.calculate_confidence_score()
        assert 0.0 <= confidence <= 1.0
    
    def test_consistency_score_calculation(self):
        """Test consistency score calculation."""
        metrics = ConfidenceMetrics()
        
        # Insufficient data should return 0.5
        assert metrics.calculate_consistency_score() == 0.5
        
        # Add consistent decisions
        for i in range(5):
            metrics.record_decision(0.75, "Medium risk", 0.8)
        
        consistency = metrics.calculate_consistency_score()
        assert consistency > 0.7  # Should be high consistency
    
    def test_risk_management_score(self):
        """Test risk management score calculation."""
        metrics = ConfidenceMetrics()
        
        # Add decisions with different risk levels
        risk_levels = ["low risk", "low risk", "medium risk", "high risk"]
        for risk in risk_levels:
            metrics.record_decision(0.7, risk)
        
        risk_score = metrics.calculate_risk_management_score()
        assert 0.0 <= risk_score <= 1.0
        assert risk_score > 0.5  # Should be moderate risk score
    
    def test_learning_progress(self):
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
    
    def test_live_trading_readiness(self):
        """Test live trading readiness assessment."""
        metrics = ConfidenceMetrics()
        
        # Not ready with insufficient decisions
        assert metrics.is_ready_for_live_trading() is False
        
        # Add good decisions
        for i in range(15):
            metrics.record_decision(
                decision_quality=0.8,
                risk_assessment="Low risk",
                consistency_score=0.7
            )
        
        assert metrics.is_ready_for_live_trading() is True
        
        # Test with threshold
        assert metrics.is_ready_for_live_trading(threshold=0.9) is False


class TestTrainingExecutor:
    """Test training executor functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock(spec=QuantChainConfig)
        config.get.return_value = False  # RAG disabled by default
        return config
    
    @pytest.fixture
    def training_executor(self, mock_config):
        """Create training executor for testing."""
        return TrainingExecutor(
            initial_cash=100000.0,
            config=mock_config,
            learning_objectives=["Learn market drivers", "Practice risk management"],
            track_mistakes=True,
            analyze_market_drivers=True
        )
    
    def test_executor_initialization(self, training_executor):
        """Test training executor initialization."""
        assert training_executor.paper_executor is not None
        assert training_executor.reflection_engine is not None
        assert training_executor.market_driver_analysis is not None
        assert training_executor.mistake_tracker is not None
        assert training_executor.confidence_metrics is not None
        assert training_executor.learning_objectives == ["Learn market drivers", "Practice risk management"]
        assert training_executor.track_mistakes is True
        assert training_executor.analyze_market_drivers is True
    
    def test_start_training_session(self, training_executor):
        """Test starting a training session."""
        symbols = ["AAPL", "MSFT"]
        objectives = ["Understand technical analysis"]
        
        session = training_executor.start_training_session(
            symbols=symbols,
            objectives=objectives,
            duration_seconds=1800
        )
        
        assert session is not None
        assert session.symbols == symbols
        assert objectives in session.learning_objectives
        assert session.duration_seconds == 1800
        assert session.is_active is True
        
        # Check executor state
        assert training_executor.current_session == session
    
    def test_end_training_session(self, training_executor):
        """Test ending a training session."""
        # Start session first
        training_executor.start_training_session(["AAPL"])
        
        # Place an order to create some data
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100
        )
        training_executor.set_market_price("AAPL", 150.0)
        training_executor.place_order(order)
        
        # End session
        report = training_executor.end_training_session()
        
        assert "session" in report
        assert "final_feedback" in report
        assert "paper_trading_metrics" in report
        assert "trade_history" in report
        assert "ready_for_live" in report
        
        # Session should be ended
        assert training_executor.current_session.end_time is not None
    
    def test_order_placement_with_analysis(self, training_executor):
        """Test order placement with decision analysis."""
        # Start session
        training_executor.start_training_session(["AAPL"])
        
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100
        )
        
        training_executor.set_market_price("AAPL", 150.0)
        result = training_executor.place_order(order)
        
        # Order should be filled
        assert result.status == OrderStatus.FILLED
        
        # Should have decision analysis
        assert len(training_executor.decision_history) == 1
        analysis = training_executor.decision_history[0]
        assert analysis.order.order_id == result.order_id
        assert 0.0 <= analysis.decision_quality <= 1.0
        assert analysis.market_drivers is not None
    
    def test_training_feedback_generation(self, training_executor):
        """Test training feedback generation."""
        # Start session and make trades
        training_executor.start_training_session(["AAPL"])
        
        for i in range(3):
            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=100
            )
            training_executor.set_market_price("AAPL", 150.0 + i)
            training_executor.place_order(order)
        
        # Get feedback
        feedback = training_executor.get_training_feedback()
        
        assert isinstance(feedback, TrainingFeedback)
        assert len(feedback.decision_analyses) > 0
        assert 0.0 <= feedback.confidence_score <= 1.0
        assert 0.0 <= feedback.consistency_score <= 1.0
        assert 0.0 <= feedback.risk_management_score <= 1.0
        assert "learning_progress" in feedback.to_dict()
    
    def test_confidence_score_tracking(self, training_executor):
        """Test confidence score tracking."""
        confidence = training_executor.get_confidence_score()
        assert 0.0 <= confidence <= 1.0
        
        # Make some trades to build confidence
        training_executor.start_training_session(["AAPL"])
        
        for i in range(10):
            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=100
            )
            training_executor.set_market_price("AAPL", 150.0 + i)
            training_executor.place_order(order)
        
        # Confidence should change
        new_confidence = training_executor.get_confidence_score()
        assert isinstance(new_confidence, float)
        assert 0.0 <= new_confidence <= 1.0
    
    def test_market_price_setting(self, training_executor):
        """Test market price setting functionality."""
        training_executor.set_market_price("AAPL", 150.0)
        
        # Place order should use set price
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100
        )
        
        result = training_executor.place_order(order)
        assert result.avg_fill_price == 150.0
    
    def test_delegate_methods(self, training_executor):
        """Test that methods are properly delegated to paper executor."""
        # Account info
        account = training_executor.get_account()
        assert account.account_id == "PAPER_TRADING"
        assert account.cash == 100000.0
        
        # Market status
        assert training_executor.is_market_open() is True
        
        # Performance metrics
        metrics = training_executor.get_performance_metrics()
        assert metrics is not None
    
    def test_reset_functionality(self, training_executor):
        """Test reset functionality."""
        # Start session and make trades
        training_executor.start_training_session(["AAPL"])
        training_executor.set_market_price("AAPL", 150.0)
        
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100
        )
        training_executor.place_order(order)
        
        # Verify state exists
        assert training_executor.current_session is not None
        assert len(training_executor.decision_history) > 0
        
        # Reset
        training_executor.reset()
        
        # Verify reset
        assert training_executor.current_session is None
        assert len(training_executor.decision_history) == 0
        assert training_executor.get_account().cash == 100000.0


class TestTrainingExecutorIntegration:
    """Integration tests for training executor."""
    
    def test_complete_training_workflow(self):
        """Test complete training workflow."""
        config = Mock(spec=QuantChainConfig)
        config.get.return_value = False
        
        executor = TrainingExecutor(
            initial_cash=100000.0,
            config=config,
            learning_objectives=["Practice trading", "Understand risk"],
            feedback_level="comprehensive"
        )
        
        # Start training session
        session = executor.start_training_session(
            symbols=["AAPL", "MSFT"],
            objectives=["Learn technical analysis"]
        )
        
        # Make multiple trades
        trades = [
            {"symbol": "AAPL", "side": OrderSide.BUY, "quantity": 100, "price": 150.0},
            {"symbol": "MSFT", "side": OrderSide.BUY, "quantity": 50, "price": 300.0},
            {"symbol": "AAPL", "side": OrderSide.SELL, "quantity": 50, "price": 155.0},
        ]
        
        for trade in trades:
            executor.set_market_price(trade["symbol"], trade["price"])
            order = OrderRequest(
                symbol=trade["symbol"],
                side=trade["side"],
                order_type=OrderType.MARKET,
                quantity=trade["quantity"]
            )
            executor.place_order(order)
        
        # Get feedback
        feedback = executor.get_training_feedback()
        
        # Verify results
        assert len(executor.decision_history) == len(trades)
        assert feedback.session_id == session.session_id
        assert len(feedback.decision_analyses) == len(trades)
        
        # End session and get report
        report = executor.end_training_session()
        
        assert report["session"]["session_id"] == session.session_id
        assert report["ready_for_live"] is not None
        assert len(report["trade_history"]) == len(trades)
    
    def test_error_handling(self):
        """Test error handling in training mode."""
        config = Mock(spec=QuantChainConfig)
        config.get.return_value = False
        
        executor = TrainingExecutor(config=config)
        
        # Test error without session
        with pytest.raises(ValueError, match="No active training session"):
            executor.get_training_feedback()
        
        # Test error when no session to end
        with pytest.raises(ValueError, match="No training session"):
            executor.end_training_session()


@pytest.mark.unit
class TestTrainingExecutorFactoryIntegration:
    """Test training executor integration with factory."""
    
    @patch('quantchain.tools.training_mode.ChromaVectorStore')
    @patch('quantchain.tools.training_mode.SentenceTransformerProvider')
    @patch('quantchain.tools.training_mode.MarketDataRAG')
    def test_training_executor_with_rag(self, mock_rag_class, mock_provider_class, mock_store_class):
        """Test training executor with RAG system enabled."""
        mock_config = Mock(spec=QuantChainConfig)
        mock_config.get.side_effect = lambda key, default=None: {
            "rag.enabled": True,
            "rag.persist_directory": "./test_db",
            "rag.embedding_model": "test-model"
        }.get(key, default)
        
        executor = TrainingExecutor(config=mock_config)
        
        # Should attempt to initialize RAG
        mock_store_class.assert_called_once()
        mock_provider_class.assert_called_once()
        mock_rag_class.assert_called_once()
    
    def test_training_executor_without_rag(self):
        """Test training executor without RAG system."""
        mock_config = Mock(spec=QuantChainConfig)
        mock_config.get.side_effect = lambda key, default=None: {
            "rag.enabled": False
        }.get(key, default)
        
        executor = TrainingExecutor(config=mock_config)
        
        # Should work without RAG
        assert executor.rag_system is None
        assert executor is not None
