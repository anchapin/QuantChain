"""Tests for MetricsResult."""

import pytest

from quantchain.backtesting.engine import MetricsResult


@pytest.mark.unit
class TestMetricsResult:
    """Test MetricsResult."""

    def test_metrics_result_defaults(self):
        """Test MetricsResult with default values."""
        result = MetricsResult()

        assert result.win_rate == 0.0
        assert result.total_trades == 0
        assert result.profit_factor == 0.0

    def test_metrics_result_custom_values(self):
        """Test MetricsResult with custom values."""
        result = MetricsResult(
            total_return=0.15,
            annualized_return=0.12,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            max_drawdown=0.05,
            calmar_ratio=3.0,
            win_rate=0.65,
            profit_factor=1.5,
            total_trades=42
        )

        assert result.total_return == 0.15
        assert result.annualized_return == 0.12
        assert result.sharpe_ratio == 1.5
        assert result.sortino_ratio == 2.0
        assert result.max_drawdown == 0.05
        assert result.calmar_ratio == 3.0
        assert result.win_rate == 0.65
        assert result.profit_factor == 1.5
        assert result.total_trades == 42

    def test_metrics_result_equality(self):
        """Test MetricsResult equality."""
        result1 = MetricsResult(total_return=0.15)
        result2 = MetricsResult(total_return=0.15)
        result3 = MetricsResult(total_return=0.20)

        assert result1 == result2
        assert result1 != result3

    def test_metrics_result_repr(self):
        """Test MetricsResult string representation."""
        result = MetricsResult(total_return=0.15, win_rate=0.65)
        repr_str = repr(result)

        assert "MetricsResult" in repr_str
        assert "total_return=0.15" in repr_str
        assert "win_rate=0.65" in repr_str
