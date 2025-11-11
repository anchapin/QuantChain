"""Reflection system for agent performance analysis."""

import statistics
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AgentAction:
    """Represents an agent action for analysis."""

    timestamp: datetime
    action_type: str
    parameters: Dict[str, Any]
    result: Any
    confidence_score: float
    success: bool = False
    reward: float = 0.0


@dataclass
class PerformanceMetrics:
    """Performance metrics for agent analysis."""

    total_actions: int = 0
    successful_actions: int = 0
    average_confidence: float = 0.0
    win_rate: float = 0.0
    profit_loss: float = 0.0
    risk_adjusted_return: float = 0.0
    action_type_breakdown: Dict[str, int] = None  # type: ignore[assignment]
    no_data: bool = False

    def __post_init__(self) -> None:
        if self.action_type_breakdown is None:
            self.action_type_breakdown = {}


@dataclass
class ReflectionReport:
    """Comprehensive reflection report."""

    period_start: datetime
    period_end: datetime
    metrics: PerformanceMetrics
    insights: List[str]
    recommendations: List[str]


class ReflectionEngine:
    """Engine for analyzing agent performance and generating insights."""

    def __init__(self) -> None:
        self.action_history: List[AgentAction] = []

    def record_action(self, action: AgentAction) -> None:
        """Record an agent action for analysis."""
        self.action_history.append(action)

    def analyze_performance(
        self, actions: Optional[List[AgentAction]] = None
    ) -> PerformanceMetrics:
        """Analyze performance metrics from actions."""
        if actions is None:
            actions = self.action_history

        if not actions:
            import warnings

            warnings.warn(
                "No actions available for performance analysis.", RuntimeWarning
            )
            metrics = PerformanceMetrics()
            metrics.no_data = True
            return metrics

        metrics = PerformanceMetrics()
        metrics.total_actions = len(actions)
        metrics.successful_actions = sum(a.success for a in actions)
        metrics.average_confidence = statistics.mean(
            a.confidence_score for a in actions
        )

        if metrics.total_actions > 0:
            metrics.win_rate = metrics.successful_actions / metrics.total_actions

        # Calculate P&L (assuming reward represents profit)
        metrics.profit_loss = sum(a.reward for a in actions)

        # Risk-adjusted return (simplified Sharpe-like ratio)
        if actions:
            returns = [a.reward for a in actions]
            if len(returns) > 1:
                avg_return = statistics.mean(returns)
                std_return = statistics.stdev(returns)
                if std_return > 0:
                    metrics.risk_adjusted_return = avg_return / std_return

        # Action type breakdown
        for action in actions:
            metrics.action_type_breakdown[action.action_type] = (
                metrics.action_type_breakdown.get(action.action_type, 0) + 1
            )

        return metrics

    def generate_insights(self, metrics: PerformanceMetrics) -> List[str]:
        """Generate insights from performance metrics."""
        insights: List[str] = []

        if metrics.no_data:
            return insights

        # Win rate insights
        if metrics.win_rate > 0.7:
            insights.append("Excellent win rate - agent is performing well")
        elif metrics.win_rate < 0.3:
            insights.append("Low win rate - consider reviewing decision logic")

        # Confidence insights
        if metrics.average_confidence > 0.8:
            insights.append("High confidence in decisions - good calibration")
        elif metrics.average_confidence < 0.5:
            insights.append("Low confidence suggests uncertainty - may need more data")

        # P&L insights
        if metrics.profit_loss > 0:
            insights.append(f"Positive P&L of {metrics.profit_loss:.2f}")
        else:
            insights.append(
                f"Negative P&L of {metrics.profit_loss:.2f} - investigate losses"
            )

        # Action diversity
        if len(metrics.action_type_breakdown) < 3:
            insights.append("Limited action diversity - agent may be too conservative")
        elif len(metrics.action_type_breakdown) > 10:
            insights.append("High action diversity - consider specializing")

        # Risk-adjusted return
        if abs(metrics.risk_adjusted_return) > 1.0:
            insights.append("Good risk-adjusted returns")
        else:
            insights.append("Poor risk-adjusted returns - high risk for low reward")

        return insights

    def update_strategy(self, insights: List[str]) -> List[str]:
        """Generate strategy recommendations based on insights."""
        recommendations: List[str] = []

        for insight in insights:
            if "low win rate" in insight.lower():
                recommendations.extend(
                    (
                        "Implement more conservative thresholds",
                        "Add additional validation steps",
                    )
                )
            elif "low confidence" in insight.lower():
                recommendations.extend(
                    (
                        "Increase data gathering phase",
                        "Implement ensemble decision making",
                    )
                )
            elif "negative p&l" in insight.lower():
                recommendations.extend(
                    ("Reduce position sizes", "Add stop-loss mechanisms")
                )
            elif "limited action diversity" in insight.lower():
                recommendations.extend(
                    (
                        "Expand available action types",
                        "Encourage exploration in safe environments",
                    )
                )
        if not recommendations:
            recommendations.append(
                "Continue current strategy - performance is satisfactory"
            )

        return recommendations

    def generate_report(
        self,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> ReflectionReport:
        """Generate comprehensive reflection report."""
        if period_start is None:
            period_start = (
                min(a.timestamp for a in self.action_history)
                if self.action_history
                else datetime.now()
            )
        if period_end is None:
            period_end = (
                max(a.timestamp for a in self.action_history)
                if self.action_history
                else datetime.now()
            )

        # Filter actions by period
        period_actions = [
            a for a in self.action_history if period_start <= a.timestamp <= period_end
        ]

        metrics = self.analyze_performance(period_actions)
        insights = self.generate_insights(metrics)
        recommendations = self.update_strategy(insights)

        return ReflectionReport(
            period_start=period_start,
            period_end=period_end,
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
        )
