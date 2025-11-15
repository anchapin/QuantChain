"""Backtesting.py Engine adapter for QuantChain."""

import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
import pandas as pd
import numpy as np

try:
    from backtesting import Backtest, Strategy
    _BACKTESTING_AVAILABLE = True
except ImportError:
    _BACKTESTING_AVAILABLE = False

from quantchain.backtesting.engine import BacktestConfig, BacktestResult, MetricsResult


class BacktestingPyEngine:
    """Adapter for the Backtesting.py library."""

    def __init__(self, config: Optional[BacktestConfig] = None):
        """Initialize the backtesting engine.

        Args:
            config: Configuration for backtesting
        """
        if not _BACKTESTING_AVAILABLE:
            raise ImportError("backtesting.py library not installed. Install with: pip install backtesting")

        self.config = config or BacktestConfig()
        self._backtest = None
        self._results = None
        self._equity_curve_data = None

        # Initialize the backtesting.py engine
        self._initialize_backtest()

    def _initialize_backtest(self) -> None:
        """Initialize the backtesting.py engine with the configuration."""
        # Create a temporary strategy for initialization
        class TempStrategy(Strategy):
            pass

        # Create a dummy DataFrame to initialize Backtest
        dummy_data = pd.DataFrame({
            'Open': [100.0],
            'High': [101.0],
            'Low': [99.0],
            'Close': [100.5],
            'Volume': [1000.0]
        })

        try:
            self._backtest = Backtest(
                dummy_data,
                TempStrategy,
                cash=self.config.initial_capital,
                commission=self.config.commission,
                exclusive_orders=True
            )
        except Exception as e:
            raise ImportError(f"Failed to initialize backtesting.py engine: {str(e)}")

    def _convert_data_format(self, data: pd.DataFrame) -> pd.DataFrame:
        """Convert data to the format expected by backtesting.py.

        Args:
            data: Input data in various possible formats

        Returns:
            DataFrame with correct column names for backtesting.py
        """
        # Make a copy to avoid modifying the original
        data = data.copy()

        # Check for required columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']

        # Convert to lowercase for case-insensitive comparison
        data.columns = [col.lower() for col in data.columns]

        # Check if all required columns exist
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Convert to proper case for backtesting.py
        column_mapping = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }

        data = data.rename(columns=column_mapping)

        # Ensure datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            if 'timestamp' in data.columns:
                data.index = pd.to_datetime(data['timestamp'])
                data = data.drop(columns=['timestamp'])
            elif 'date' in data.columns:
                data.index = pd.to_datetime(data['date'])
                data = data.drop(columns=['date'])
            else:
                # Create a default date range
                start_date = datetime.now() - timedelta(days=len(data))
                dates = pd.date_range(start=start_date, periods=len(data), freq='D')
                data.index = dates

        return data

    def _get_performance_metrics(self, stats: Dict[str, Any]) -> MetricsResult:
        """Extract performance metrics from backtesting.py stats.

        Args:
            stats: Dictionary of statistics from backtesting.py

        Returns:
            MetricsResult object
        """
        # Map backtesting.py stat names to our metrics
        return MetricsResult(
            total_return=stats.get('Return [%]', 0) / 100,
            return_pct=stats.get('Return [%]', 0),
            annualized_return=stats.get('Return (Ann.) [%]', 0) / 100,
            sharpe_ratio=stats.get('Sharpe Ratio', 0),
            sortino_ratio=stats.get('Sortino Ratio', 0),
            calmar_ratio=stats.get('Calmar Ratio', 0),
            max_drawdown=stats.get('Max Drawdown [%]', 0) / 100,
            max_drawdown_pct=stats.get('Max Drawdown [%]', 0),
            max_drawdown_duration=stats.get('Max Drawdown Duration', 0),
            win_rate=stats.get('Win Rate [%]', 0) / 100,
            win_rate_pct=stats.get('Win Rate [%]', 0),
            profit_factor=stats.get('Profit Factor', 0),
            recovery_factor=stats.get('Recovery Factor', 0),
            total_trades=stats.get('# Trades', 0),
            avg_trade=stats.get('Avg. Trade [%]', 0) / 100,
            avg_win_pct=stats.get('Avg. Winning Trade [%]', 0),
            avg_loss_pct=stats.get('Avg. Losing Trade [%]', 0),
            largest_win=stats.get('Best Trade [%]', 0) / 100,
            largest_loss=stats.get('Worst Trade [%]', 0) / 100,
            avg_drawdown=stats.get('Avg. Drawdown [%]', 0) / 100,
            avg_drawdown_pct=stats.get('Avg. Drawdown [%]', 0),
            var_95=0.0,  # Not directly provided by backtesting.py
            var_99=0.0,  # Not directly provided by backtesting.py
            skewness=0.0,  # Not directly provided by backtesting.py
            kurtosis=0.0,  # Not directly provided by backtesting.py
        )

    def _analyze_portfolio_composition(self, portfolio: Dict[str, float]) -> Dict[str, float]:
        """Analyze portfolio composition.

        Args:
            portfolio: Dictionary with symbol and quantity

        Returns:
            Portfolio composition with symbol and percentage
        """
        if not portfolio:
            return {}

        total_value = sum(portfolio.values())
        return {
            symbol: (quantity / total_value) * 100
            for symbol, quantity in portfolio.items()
        }

    def _calculate_risk_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate risk metrics from returns.

        Args:
            returns: Series of returns

        Returns:
            Dictionary with risk metrics
        """
        returns = returns.dropna()

        if len(returns) == 0:
            return {
                'volatility': 0.0,
                'var_95': 0.0,
                'var_99': 0.0,
                'skewness': 0.0,
                'kurtosis': 0.0
            }

        # Calculate metrics
        volatility = returns.std() * np.sqrt(252)  # Annualized volatility
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        skewness = returns.skew()
        kurtosis = returns.kurtosis()

        return {
            'volatility': volatility,
            'var_95': var_95,
            'var_99': var_99,
            'skewness': skewness,
            'kurtosis': kurtosis
        }

    def run_backtest(self, data: pd.DataFrame, strategy: Any) -> BacktestResult:
        """Run a backtest with the provided data and strategy.

        Args:
            data: OHLCV data for backtesting
            strategy: Trading strategy to test

        Returns:
            BacktestResult with performance metrics
        """
        # Convert data format
        try:
            data = self._convert_data_format(data)
        except Exception as e:
            raise ValueError(f"Failed to convert data format: {str(e)}")

        # Check if strategy has required methods
        required_methods = ['init', 'next']
        for method in required_methods:
            if not hasattr(strategy, method):
                raise AttributeError(f"Strategy must have '{method}' method")

        # Initialize and run backtest
        start_time = datetime.now()

        try:
            bt = Backtest(
                data,
                strategy,
                cash=self.config.initial_capital,
                commission=self.config.commission,
                slippage=self.config.slippage,
                exclusive_orders=True
            )

            stats = bt.run()
            execution_time = (datetime.now() - start_time).total_seconds()

            # Extract metrics
            metrics = self._get_performance_metrics(stats)

            # Get equity curve
            equity_curve = bt._equity_curve

            # Get trade log
            trade_log = bt._trades

            return BacktestResult(
                equity_curve=equity_curve,
                trade_log=trade_log,
                summary_stats=stats,
                metrics=metrics,
                execution_time=execution_time,
                config=self.config
            )

        except Exception as e:
            raise RuntimeError(f"Backtest execution failed: {str(e)}")

    def get_results(self) -> Optional[BacktestResult]:
        """Get the results of the last backtest run.

        Returns:
            BacktestResult or None if no backtest has been run
        """
        return self._results

    def get_equity_curve(self) -> Optional[pd.Series]:
        """Get the equity curve from the last backtest.

        Returns:
            Series with equity curve data or None
        """
        return self._equity_curve_data
