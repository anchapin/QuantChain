"""
FinRL Adapter for QuantChain Backtesting

This module provides a gym-compatible environment that bridges QuantChain's
backtesting engine with FinRL's reinforcement learning framework.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from quantchain.backtesting.market_friction import MarketFrictionSimulator
from quantchain.backtesting.performance_metrics import PerformanceMetrics
from quantchain.connectors import (
    AlpacaDataConnector,
    CCXTDataConnector,
    PolygonDataConnector,
)

logger = logging.getLogger(__name__)


def get_connector(
    connector_name: str, **kwargs: Any
) -> Union[AlpacaDataConnector, PolygonDataConnector, CCXTDataConnector]:
    """
    Get a data connector instance.

    Args:
        connector_name: Name of the connector to create
        **kwargs: Additional arguments for connector initialization

    Returns:
        Data connector instance

    Raises:
        ValueError: If connector name is not recognized
    """
    connector_map = {
        "alpaca": AlpacaDataConnector,
        "polygon": PolygonDataConnector,
        "ccxt": CCXTDataConnector,
    }

    connector_class = connector_map.get(connector_name.lower())
    if not connector_class:
        raise ValueError(f"Unknown connector: {connector_name}")

    # Explicitly cast to the correct union type
    return connector_class(**kwargs)  # type: ignore


class FinRLAdapter(gym.Env):
    """
    Gym-compatible environment for integrating FinRL agents with QuantChain backtesting.

    This adapter provides:
    - Market data from QuantChain connectors
    - Realistic market friction modeling
    - Performance metrics integration
    - Gym-compatible observation and action spaces
    """

    metadata = {"render.modes": ["human"]}

    def __init__(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        initial_balance: float = 100000,
        data_connector: str = "alpaca",
        market_friction_config: Optional[Dict] = None,
        observation_features: Optional[List[str]] = None,
        reward_strategy: str = "risk_adjusted_return",
        **kwargs: Any,
    ):
        """
        Initialize the FinRL adapter environment.

        Args:
            symbol: Trading symbol (e.g., "AAPL", "BTC/USD")
            start_date: Backtest start date (YYYY-MM-DD)
            end_date: Backtest end date (YYYY-MM-DD)
            initial_balance: Starting portfolio balance
            data_connector: Name of QuantChain data connector to use
            market_friction_config: Configuration for market friction model
            observation_features: List of features to include in observation space
            reward_strategy: Strategy for calculating rewards
            **kwargs: Additional arguments passed to connectors
        """
        super(FinRLAdapter, self).__init__()

        # Store parameters
        self.symbol = symbol
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.initial_balance = initial_balance
        self.reward_strategy = reward_strategy
        self.kwargs = kwargs

        # Initialize components
        self._setup_data_connector(data_connector)
        self._setup_market_friction(market_friction_config)
        self._setup_performance_metrics()

        # Setup observation and action spaces
        self._setup_spaces(observation_features)

        # State tracking
        self.current_step: int = 0
        self.max_steps: int = int(len(self.market_data) - 1)
        self.done: bool = False

        # Portfolio state
        self.balance: float = float(initial_balance)
        self.position: float = 0.0
        self.position_value: float = 0.0
        self.total_value: float = float(initial_balance)

        # Tracking for rewards
        self.last_total_value: float = float(initial_balance)
        self.transaction_costs: float = 0.0
        self.portfolio_values: List[float] = [float(initial_balance)]

    def _setup_data_connector(self, connector_name: str) -> None:
        """Initialize the data connector and fetch market data."""
        try:
            connector = get_connector(connector_name, **self.kwargs)
            self.market_data = connector.get_historical_data(
                symbol=self.symbol,
                timeframe="1D",
                start_date=self.start_date,
                end_date=self.end_date,
            )

            # Add technical indicators
            self._add_technical_indicators()

        except Exception as e:
            logger.error(f"Failed to setup data connector: {e}")
            raise

    def _setup_market_friction(self, config: Optional[Dict]) -> None:
        """Initialize market friction model."""
        from quantchain.backtesting.market_friction import (
            FixedLatency,
            MarketFrictionConfig,
            PercentageCommission,
            VolumeImpactSlippage,
        )

        # Use empty dict if config is None
        if config is None:
            config = {}

        # Default models
        commission = PercentageCommission(rate=config.get("commission", 0.001))
        slippage = VolumeImpactSlippage(
            base_rate=config.get("slippage", 0.0005), volume_impact_factor=0.0001
        )
        latency = FixedLatency(latency_ms=config.get("latency_ms", 50))

        # Create configuration
        friction_config = MarketFrictionConfig(
            commission_model=commission, slippage_model=slippage, latency_model=latency
        )

        self.market_friction = MarketFrictionSimulator(config=friction_config)

    def _setup_performance_metrics(self) -> None:
        """Initialize performance metrics tracker."""
        self.performance_metrics = PerformanceMetrics()

    def _setup_spaces(self, features: Optional[List[str]]) -> None:
        """Setup observation and action spaces."""
        # Default observation features
        if features is None:
            features = [
                "open",
                "high",
                "low",
                "close",
                "volume",
                "rsi",
                "macd",
                "macd_signal",
                "macd_histogram",
                "bb_upper",
                "bb_middle",
                "bb_lower",
                "balance",
                "position",
                "position_value",
                "total_value",
                "pnl_ratio",
                "action_history",
            ]

        self.observation_features = features

        # Calculate observation space size
        obs_size = len(features)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_size,), dtype=np.float32
        )

        # Action space: [hold, buy, sell] with position sizing
        # Extended action: [action_type(0-2), amount(0-1)]
        self.action_space = spaces.Box(
            low=np.array([0, 0]), high=np.array([2, 1]), dtype=np.float32
        )

    def _add_technical_indicators(self) -> None:
        """Add technical indicators to market data."""
        # RSI
        delta = self.market_data["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        self.market_data["rsi"] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = self.market_data["close"].ewm(span=12).mean()
        exp2 = self.market_data["close"].ewm(span=26).mean()
        self.market_data["macd"] = exp1 - exp2
        self.market_data["macd_signal"] = self.market_data["macd"].ewm(span=9).mean()
        self.market_data["macd_histogram"] = (
            self.market_data["macd"] - self.market_data["macd_signal"]
        )

        # Bollinger Bands
        rolling_mean = self.market_data["close"].rolling(window=20).mean()
        rolling_std = self.market_data["close"].rolling(window=20).std()
        self.market_data["bb_middle"] = rolling_mean
        self.market_data["bb_upper"] = rolling_mean + (rolling_std * 2)
        self.market_data["bb_lower"] = rolling_mean - (rolling_std * 2)

    def reset(self) -> np.ndarray:
        """
        Reset the environment to initial state.

        Returns:
            Initial observation
        """
        self.current_step = 0
        self.done = False

        # Reset portfolio state
        self.balance = float(self.initial_balance)
        self.position = 0.0
        self.position_value = 0.0
        self.total_value = float(self.initial_balance)

        # Reset tracking
        self.last_total_value = float(self.initial_balance)
        self.transaction_costs = 0.0
        self.portfolio_values = [float(self.initial_balance)]

        # Reset performance metrics (create new instance as reset method not available)
        self._setup_performance_metrics()

        return self._get_observation()

    def step(
        self, action: Union[np.ndarray, List]
    ) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute one step in the environment.

        Args:
            action: Action to take [action_type, amount]

        Returns:
            Tuple of (observation, reward, done, info)
        """
        if self.done:
            return self._get_observation(), 0, self.done, {}

        # Parse action
        action_type = int(action[0])  # 0=hold, 1=buy, 2=sell
        amount = float(action[1]) if len(action) > 1 else 0.5  # Position size (0-1)

        # Execute action
        self._execute_action(action_type, amount)

        # Calculate reward
        reward = self._calculate_reward()

        # Update step
        self.current_step += 1
        if self.current_step >= self.max_steps:
            self.done = True

        # Get new observation
        observation = self._get_observation()

        # Prepare info dict
        info = {
            "balance": self.balance,
            "position": self.position,
            "position_value": self.position_value,
            "total_value": self.total_value,
            "transaction_costs": self.transaction_costs,
            "step": self.current_step,
        }

        return observation, reward, self.done, info

    def _execute_action(self, action_type: int, amount: float) -> None:
        """Execute trading action with market frictions."""
        current_price = self.market_data.iloc[self.current_step]["close"]

        if action_type == 1:  # Buy
            # Calculate order amount
            available_balance = self.balance * 0.95  # Keep 5% reserve
            max_shares = available_balance / current_price
            shares_to_buy = max_shares * amount

            # Only execute if shares_to_buy is positive
            if shares_to_buy > 0:
                # Apply market frictions
                cost_info = self.market_friction.get_total_cost(
                    price=current_price,
                    quantity=int(shares_to_buy),
                    side="buy",
                    symbol=self.symbol,
                )
                execution_price = float(cost_info["executed_price"])
                cost = float(cost_info["total"])

                # Execute trade if sufficient balance
                if shares_to_buy * execution_price + cost <= self.balance:
                    self.position += shares_to_buy
                    self.balance -= shares_to_buy * execution_price + cost
                    self.transaction_costs += cost

        elif action_type == 2:  # Sell
            # Calculate sell amount
            shares_to_sell = self.position * amount

            if shares_to_sell > 0:
                # Apply market frictions
                cost_info = self.market_friction.get_total_cost(
                    price=current_price,
                    quantity=int(shares_to_sell),
                    side="sell",
                    symbol=self.symbol,
                )
                execution_price = float(cost_info["executed_price"])
                cost = float(cost_info["total"])

                # Execute trade
                self.position -= shares_to_sell
                self.balance += shares_to_sell * execution_price - cost
                self.transaction_costs += cost

    def _get_observation(self) -> np.ndarray:
        """Get current observation as numpy array."""
        current_data = self.market_data.iloc[self.current_step]
        obs = []

        # Market data features
        for feature in self.observation_features:
            if feature in current_data:
                value = float(current_data[feature])
                # Handle NaN values
                if np.isnan(value):
                    value = 0.0
                obs.append(value)
            elif feature == "balance":
                obs.append(float(self.balance))
            elif feature == "position":
                obs.append(float(self.position))
            elif feature == "position_value":
                obs.append(float(self.position_value))
            elif feature == "total_value":
                obs.append(float(self.total_value))
            elif feature == "pnl_ratio":
                pnl = self.total_value - self.initial_balance
                pnl_ratio = pnl / self.initial_balance
                obs.append(pnl_ratio)
            elif feature == "action_history":
                # Simple action history feature (last 5 actions)
                obs.append(0)  # Placeholder
            else:
                obs.append(0.0)  # Default value

        return np.array(obs, dtype=np.float32)  # type: ignore

    def _calculate_reward(self) -> float:
        """Calculate reward based on strategy."""
        # Update portfolio value
        if self.current_step < len(self.market_data):
            current_price = self.market_data.iloc[self.current_step]["close"]
            self.position_value = self.position * current_price
        self.total_value = self.balance + self.position_value

        # Track portfolio values
        self.portfolio_values.append(self.total_value)

        # Calculate returns
        if self.reward_strategy == "simple_return":
            reward = (self.total_value - self.last_total_value) / self.last_total_value
        elif self.reward_strategy == "risk_adjusted_return":
            # Simple Sharpe-like reward
            returns = np.diff(self.portfolio_values) / np.array(
                self.portfolio_values[:-1]
            )
            if len(returns) > 1:
                reward = float(np.mean(returns) / (np.std(returns) + 1e-6))
            else:
                reward = 0
        elif self.reward_strategy == "log_return":
            reward = (
                np.log(self.total_value / self.last_total_value)
                if self.last_total_value > 0
                else 0
            )
        else:
            reward = self.total_value - self.last_total_value

        self.last_total_value = self.total_value

        # Penalty for transaction costs
        reward -= self.transaction_costs * 0.1

        return float(reward)

    def render(self, mode: str = "human") -> None:
        """Render environment state."""
        if mode == "human":
            print(f"Step: {self.current_step}/{self.max_steps}")
            print(f"Balance: ${self.balance:,.2f}")
            print(f"Position: {self.position:.6f} shares")
            print(f"Position Value: ${self.position_value:,.2f}")
            print(f"Total Value: ${self.total_value:,.2f}")
            print(f"Transaction Costs: ${self.transaction_costs:,.2f}")
            print("-" * 50)

    def get_performance_metrics(self) -> Dict:
        """Get comprehensive performance metrics."""
        # Import pandas for metrics calculation
        import pandas as pd

        # Convert portfolio values to pandas Series for metrics calculation
        # Create date range matching the portfolio values
        dates = pd.date_range(
            start=self.start_date, periods=len(self.portfolio_values), freq="D"
        )
        equity_curve = pd.Series(self.portfolio_values, index=dates)

        # Create simple trades DataFrame (placeholder for now)
        dates = pd.date_range(
            start=self.start_date, periods=len(self.portfolio_values), freq="D"
        )
        trades_data = {
            "entry_time": [dates[0]],  # placeholder
            "exit_time": [dates[-1]],  # placeholder
            "entry_price": [self.initial_balance],  # placeholder
            "exit_price": [self.total_value],  # placeholder
            "quantity": [1],  # placeholder
            "side": ["long"],  # placeholder
            "pnl": [self.total_value - self.initial_balance],  # placeholder
        }
        trades_df = pd.DataFrame(trades_data)

        metrics_result = self.performance_metrics.calculate_all_metrics(
            equity_curve=equity_curve, trades=trades_df, frequency="1d"
        )

        # Convert MetricsResult to dict and add custom metrics
        metrics = dict(metrics_result.__dict__.copy())
        metrics.update(
            {
                "total_return": (self.total_value - self.initial_balance)
                / self.initial_balance,
                "transaction_costs": self.transaction_costs,
                "final_balance": self.balance,
                "final_position": self.position,
                "total_trades": len(self.portfolio_values) - 1,  # Simple trade count,
            }
        )

        return metrics
