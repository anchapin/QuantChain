"""Tests for reflection system."""

import pytest
import warnings
from datetime import datetime, timedelta

from quantchain.core.reflection import (
    AgentAction,
    PerformanceMetrics,
    ReflectionReport,
    ReflectionEngine,
)


@pytest.mark.unit
class TestAgentAction:
    """Test AgentAction dataclass."""

    def test_agent_action_creation(self) -> None:
        """Test creating an AgentAction."""
        timestamp = datetime.now()
        action = AgentAction(
            timestamp=timestamp,
            action_type="trade",
            parameters={"symbol": "AAPL", "quantity": 100},
            result="success",
            confidence_score=0.8,
            success=True,
            reward=50.0,
        )
        assert action.timestamp == timestamp
        assert action.action_type == "trade"
        assert action.parameters == {"symbol": "AAPL", "quantity": 100}
        assert action.result == "success"
        assert action.confidence_score == 0.8
        assert action.success is True
        assert action.reward == 50.0

    def test_agent_action_defaults(self) -> None:
        """Test AgentAction with defaults."""
        timestamp = datetime.now()
        action = AgentAction(
            timestamp=timestamp,
            action_type="analyze",
            parameters={},
            result=None,
            confidence_score=0.5,
        )
        assert action.success is False
        assert action.reward == 0.0


@pytest.mark.unit
class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self) -> None:
        """Test creating PerformanceMetrics."""
        metrics = PerformanceMetrics(
            total_actions=10,
            successful_actions=7,
            average_confidence=0.75,
            win_rate=0.7,
            profit_loss=150.0,
            risk_adjusted_return=1.2,
            action_type_breakdown={"trade": 8, "analyze": 2},
        )
        assert metrics.total_actions == 10
        assert metrics.successful_actions == 7
        assert metrics.average_confidence == 0.75
        assert metrics.win_rate == 0.7
        assert metrics.profit_loss == 150.0
        assert metrics.risk_adjusted_return == 1.2
        assert metrics.action_type_breakdown == {"trade": 8, "analyze": 2}
        assert metrics.no_data is False

    def test_performance_metrics_defaults(self) -> None:
        """Test PerformanceMetrics with defaults."""
        metrics = PerformanceMetrics()
        assert metrics.total_actions == 0
        assert metrics.successful_actions == 0
        assert metrics.average_confidence == 0.0
        assert metrics.win_rate == 0.0
        assert metrics.profit_loss == 0.0
        assert metrics.risk_adjusted_return == 0.0
        assert metrics.action_type_breakdown == {}
        assert metrics.no_data is False

    def test_performance_metrics_post_init(self) -> None:
        """Test PerformanceMetrics __post_init__."""
        metrics = PerformanceMetrics()
        assert metrics.action_type_breakdown == {}


@pytest.mark.unit
class TestReflectionReport:
    """Test ReflectionReport dataclass."""

    def test_reflection_report_creation(self) -> None:
        """Test creating a ReflectionReport."""
        start = datetime.now()
        end = start + timedelta(hours=1)
        metrics = PerformanceMetrics()
        report = ReflectionReport(
            period_start=start,
            period_end=end,
            metrics=metrics,
            insights=["Good performance"],
            recommendations=["Continue strategy"],
        )
        assert report.period_start == start
        assert report.period_end == end
        assert report.metrics == metrics
        assert report.insights == ["Good performance"]
        assert report.recommendations == ["Continue strategy"]


@pytest.mark.unit
class TestReflectionEngine:
    """Test ReflectionEngine."""

    @pytest.fixture
    def engine(self):
        """Create a ReflectionEngine instance."""
        return ReflectionEngine()

    @pytest.fixture
    def sample_actions(self):
        """Create sample actions for testing."""
        base_time = datetime.now()
        return [
            AgentAction(
                timestamp=base_time,
                action_type="trade",
                parameters={"symbol": "AAPL"},
                result="profit",
                confidence_score=0.8,
                success=True,
                reward=100.0,
            ),
            AgentAction(
                timestamp=base_time + timedelta(minutes=30),
                action_type="trade",
                parameters={"symbol": "GOOGL"},
                result="loss",
                confidence_score=0.6,
                success=False,
                reward=-50.0,
            ),
            AgentAction(
                timestamp=base_time + timedelta(hours=1),
                action_type="analyze",
                parameters={"symbol": "MSFT"},
                result="data",
                confidence_score=0.9,
                success=True,
                reward=0.0,
            ),
        ]

    def test_engine_init(self, engine) -> None:
        """Test ReflectionEngine initialization."""
        assert engine.action_history == []

    def test_record_action(self, engine, sample_actions) -> None:
        """Test recording actions."""
        action = sample_actions[0]
        engine.record_action(action)

        assert len(engine.action_history) == 1
        assert engine.action_history[0] == action

    def test_analyze_performance_no_actions(self, engine, sample_actions) -> None:
        """Test analyzing performance with no actions."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            metrics = engine.analyze_performance()

        assert len(w) == 1
        assert issubclass(w[0].category, RuntimeWarning)
        assert "No actions available" in str(w[0].message)

        assert metrics.total_actions == 0
        assert metrics.no_data is True

    def test_analyze_performance_with_actions(self, engine, sample_actions) -> None:
        """Test analyzing performance with actions."""
        for action in sample_actions:
            engine.record_action(action)

        metrics = engine.analyze_performance()

        assert metrics.total_actions == 3
        assert metrics.successful_actions == 2
        assert metrics.average_confidence == pytest.approx((0.8 + 0.6 + 0.9) / 3)
        assert metrics.win_rate == 2 / 3
        assert metrics.profit_loss == 50.0
        assert metrics.action_type_breakdown == {"trade": 2, "analyze": 1}
        assert metrics.no_data is False

    def test_analyze_performance_with_external_actions(
        self, engine, sample_actions
    ) -> None:
        """Test analyzing performance with external actions list."""
        metrics = engine.analyze_performance(sample_actions)

        assert metrics.total_actions == 3
        assert metrics.successful_actions == 2

    def test_analyze_performance_risk_adjusted_return(self, engine) -> None:
        """Test risk-adjusted return calculation."""
        actions = [
            AgentAction(
                timestamp=datetime.now(),
                action_type="trade",
                parameters={},
                result="",
                confidence_score=0.5,
                success=True,
                reward=10.0,
            ),
            AgentAction(
                timestamp=datetime.now(),
                action_type="trade",
                parameters={},
                result="",
                confidence_score=0.5,
                success=True,
                reward=20.0,
            ),
            AgentAction(
                timestamp=datetime.now(),
                action_type="trade",
                parameters={},
                result="",
                confidence_score=0.5,
                success=True,
                reward=30.0,
            ),
        ]

        metrics = engine.analyze_performance(actions)

        # Risk-adjusted return = mean / std
        mean_return = (10 + 20 + 30) / 3  # 20.0
        std_return = 10.0  # std of [10, 20, 30]
        expected_rar = mean_return / std_return
        assert metrics.risk_adjusted_return == pytest.approx(expected_rar, abs=0.1)

    def test_generate_insights_high_win_rate(self, engine) -> None:
        """Test insights generation for high win rate."""
        metrics = PerformanceMetrics(
            total_actions=10,
            successful_actions=8,
            win_rate=0.8,
            average_confidence=0.9,
            profit_loss=100.0,
            action_type_breakdown={"trade": 10},
        )

        insights = engine.generate_insights(metrics)

        assert "Excellent win rate" in " ".join(insights)
        assert "High confidence" in " ".join(insights)
        assert "Positive P&L" in " ".join(insights)

    def test_generate_insights_low_performance(self, engine) -> None:
        """Test insights generation for low performance."""
        metrics = PerformanceMetrics(
            total_actions=10,
            successful_actions=2,
            win_rate=0.2,
            average_confidence=0.3,
            profit_loss=-50.0,
            action_type_breakdown={"trade": 10},
        )

        insights = engine.generate_insights(metrics)

        assert "Low win rate" in " ".join(insights)
        assert "Low confidence" in " ".join(insights)
        assert "Negative P&L" in " ".join(insights)

    def test_generate_insights_action_diversity(self, engine) -> None:
        """Test insights generation for action diversity."""
        # Low diversity
        metrics_low = PerformanceMetrics(action_type_breakdown={"trade": 10})
        insights_low = engine.generate_insights(metrics_low)
        assert "Limited action diversity" in " ".join(insights_low)

        # High diversity
        metrics_high = PerformanceMetrics(
            action_type_breakdown={f"type_{i}": 1 for i in range(12)}
        )
        insights_high = engine.generate_insights(metrics_high)
        assert "High action diversity" in " ".join(insights_high)

    def test_update_strategy_low_win_rate(self, engine) -> None:
        """Test strategy updates for low win rate."""
        insights = ["Low win rate - consider reviewing decision logic"]
        recommendations = engine.update_strategy(insights)

        assert "conservative thresholds" in " ".join(recommendations)
        assert "validation steps" in " ".join(recommendations)

    def test_update_strategy_low_confidence(self, engine) -> None:
        """Test strategy updates for low confidence."""
        insights = ["Low confidence suggests uncertainty"]
        recommendations = engine.update_strategy(insights)

        assert "data gathering" in " ".join(recommendations)
        assert "ensemble decision" in " ".join(recommendations)

    def test_update_strategy_negative_pnl(self, engine) -> None:
        """Test strategy updates for negative P&L."""
        insights = ["Negative P&L - investigate losses"]
        recommendations = engine.update_strategy(insights)

        assert "position sizes" in " ".join(recommendations)
        assert "stop-loss" in " ".join(recommendations)

    def test_update_strategy_good_performance(self, engine) -> None:
        """Test strategy updates for good performance."""
        insights = ["Excellent win rate", "High confidence"]
        recommendations = engine.update_strategy(insights)

        assert "Continue current strategy" in " ".join(recommendations)

    def test_generate_report_no_history(self, engine, sample_actions) -> None:
        """Test generating report with no action history."""
        report = engine.generate_report()

        assert isinstance(report, ReflectionReport)
        assert report.metrics.no_data is True
        assert report.insights == []
        assert report.recommendations == [
            "Continue current strategy - performance is satisfactory"
        ]

    def test_generate_report_with_history(self, engine, sample_actions) -> None:
        """Test generating report with action history."""
        for action in sample_actions:
            engine.record_action(action)

        report = engine.generate_report()

        assert isinstance(report, ReflectionReport)
        assert report.metrics.total_actions == 3
        assert len(report.insights) > 0
        assert len(report.recommendations) > 0

    def test_generate_report_with_period_filter(self, engine, sample_actions) -> None:
        """Test generating report with period filtering."""
        for action in sample_actions:
            engine.record_action(action)

        base_time = sample_actions[0].timestamp
        start = base_time - timedelta(minutes=30)
        end = base_time + timedelta(minutes=15)  # Only include first action

        report = engine.generate_report(period_start=start, period_end=end)

        # Should only include first action
        assert report.metrics.total_actions == 1
        assert report.period_start == start
        assert report.period_end == end
