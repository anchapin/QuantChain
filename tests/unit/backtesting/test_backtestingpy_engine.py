"""Tests for BacktestingPyEngine."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from quantchain.backtesting.backtestingpy_engine import BacktestingPyEngine
from quantchain.backtesting.engine import BacktestConfig, BacktestResult, MetricsResult


class TestBacktestingPyEngine:
    """Test the BacktestingPyEngine class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.config = BacktestConfig(
            initial_capital=100000,
            commission=0.001,
            slippage=0.0005
        )
        self.engine = BacktestingPyEngine(config=self.config)

    def test_initialization(self):
        """Test engine initialization."""
        assert self.engine.initial_capital == 100000
        assert self.engine.commission == 0.001
        assert self.engine.slippage == 0.0005

    @patch('backtesting.Backtest')
    def test_run_backtest(self, mock_backtest):
        """Test running a backtest."""
        # Create mock data
        data = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [101, 102, 103],
            'Low': [99, 100, 101],
            'Close': [101, 102, 103],
            'Volume': [1000, 1500, 2000],
        })
        data.index = pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03'])

        # Create mock backtest instance
        mock_bt = Mock()
        mock_bt.run.return_value = {
            'Return [%]': 10.0,
            'Sharpe Ratio': 1.5,
            'Max Drawdown [%]': -5.0,
            'Win Rate [%]': 60.0,
        }
        mock_backtest.return_value = mock_bt

        # Run the backtest
        strategy = Mock()
        result = self.engine.run_backtest(data, strategy)

        # Assertions
        assert isinstance(result, BacktestResult)
        assert mock_backtest.called
        mock_bt.run.assert_called_once()

    def test_get_performance_metrics(self):
        """Test performance metrics calculation."""
        # Create mock backtest results
        mock_results = {
            'Return [%]': 15.0,
            'Sharpe Ratio': 1.8,
            'Max Drawdown [%]': -7.0,
            'Win Rate [%]': 65.0,
            '# Trades': 100,
            'Avg. Drawdown [%]': -3.0,
        }

        metrics = self.engine._get_performance_metrics(mock_results)

        assert isinstance(metrics, MetricsResult)
        assert metrics.return_pct == 15.0
        assert metrics.sharpe_ratio == 1.8
        assert metrics.max_drawdown_pct == -7.0
        assert metrics.win_rate_pct == 65.0
        assert metrics.total_trades == 100
        assert metrics.avg_drawdown_pct == -3.0

    def test_analyze_portfolio_composition(self):
        """Test portfolio composition analysis."""
        # Create mock portfolio data
        portfolio = {
            'AAPL': 50,
            'GOOGL': 30,
            'MSFT': 20
        }

        composition = self.engine._analyze_portfolio_composition(portfolio)

        assert 'AAPL' in composition
        assert 'GOOGL' in composition
        assert 'MSFT' in composition
        assert composition['AAPL'] == 50
        assert composition['GOOGL'] == 30
        assert composition['MSFT'] == 20

    def test_calculate_risk_metrics(self):
        """Test risk metrics calculation."""
        # Create mock returns data
        returns = pd.Series([0.01, 0.02, -0.01, 0.03, -0.02])

        risk_metrics = self.engine._calculate_risk_metrics(returns)

        assert 'volatility' in risk_metrics
        assert 'var_95' in risk_metrics
        assert 'var_99' in risk_metrics
        assert 'skewness' in risk_metrics
        assert 'kurtosis' in risk_metrics

    def test_invalid_data_format(self):
        """Test handling of invalid data format."""
        # Create invalid data
        invalid_data = pd.DataFrame({
            'Invalid': [1, 2, 3]
        })

        strategy = Mock()

        with pytest.raises(ValueError):
            self.engine.run_backtest(invalid_data, strategy)

    def test_empty_data(self):
        """Test handling of empty data."""
        # Create empty data
        empty_data = pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
        empty_data.index = pd.to_datetime([])

        strategy = Mock()

        with pytest.raises(ValueError):
            self.engine.run_backtest(empty_data, strategy)

    def test_strategy_without_required_methods(self):
        """Test handling of strategy without required methods."""
        # Create valid data
        data = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [101, 102, 103],
            'Low': [99, 100, 101],
            'Close': [101, 102, 103],
            'Volume': [1000, 1500, 2000],
        })
        data.index = pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03'])

        # Create incomplete strategy
        incomplete_strategy = Mock()
        # Remove required methods
        if hasattr(incomplete_strategy, 'init'):
            delattr(incomplete_strategy, 'init')
        if hasattr(incomplete_strategy, 'next'):
            delattr(incomplete_strategy, 'next')

        with pytest.raises(AttributeError):
            self.engine.run_backtest(data, incomplete_strategy)
