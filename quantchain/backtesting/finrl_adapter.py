"""
FinRL Adapter for QuantChain Backtesting

This module provides a gym-compatible environment that bridges QuantChain's
backtesting engine with FinRL's reinforcement learning framework.
"""

import logging
import numpy as np
from typing import List, Optional

from quantchain.backtesting.market_friction import MarketFrictionSimulator
from quantchain.backtesting.performance_metrics import PerformanceMetrics
from quantchain.connectors import (
    AlpacaDataConnector,
    CCXTDataConnector,
    PolygonDataConnector,
)

# Gymnasium compatibility guard
GYMNASIUM_AVAILABLE = False
try:
    import gymnasium as gym
    from gymnasium import spaces

    GYMNASIUM_AVAILABLE = True
except ImportError:
    gym = None
    spaces = None
    GYMNASIUM_AVAILABLE = False

logger = logging.getLogger(__name__)


class FinRLAdapterError(Exception):
    """Base exception for FinRL adapter errors."""

    pass


class FinRLConnectionError(FinRLAdapterError):
    """Exception for connection errors in the FinRL adapter."""

    pass


class FinRLDataError(FinRLAdapterError):
    """Exception for data errors in the FinRL adapter."""

    pass


def get_connector(connector_type: str, **kwargs):
    """Factory function to get the appropriate data connector.

    Args:
        connector_type: Type of connector to use (alpaca, ccxt, polygon)
        **kwargs: Additional arguments for the connector

    Returns:
        Data connector instance
    """
    if connector_type.lower() == "alpaca":
        return AlpacaDataConnector(**kwargs)
    elif connector_type.lower() == "ccxt":
        return CCXTDataConnector(**kwargs)
    elif connector_type.lower() == "polygon":
        return PolygonDataConnector(**kwargs)
    else:
        raise ValueError(f"Unknown connector type: {connector_type}")


class FinRLAdapter:
    """Gymnasium environment adapter for QuantChain backtesting engine.

    This class provides a gym-compatible environment that can be used with
    FinRL's reinforcement learning framework for training trading agents.
    """

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        connector_type: str = "alpaca",
        initial_balance: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        market_hours_only: bool = True,
        lookback_window: int = 30,
        tech_indicators: Optional[List[str]] = None,
        **connector_kwargs,
    ):
        """Initialize the FinRL adapter.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe (e.g., '1D', '1H', '5T')
            start_date: Start date in format 'YYYY-MM-DD'
            end_date: End date in format 'YYYY-MM-DD'
            connector_type: Type of data connector to use
            initial_balance: Initial portfolio balance
            commission: Trading commission rate
            slippage: Trading slippage rate
            market_hours_only: Whether to only consider market hours
            lookback_window: Window size for historical observations
            tech_indicators: List of technical indicators to add
            **connector_kwargs: Additional arguments for the data connector
        """
        if not GYMNASIUM_AVAILABLE:
            raise FinRLConnectionError(
                "Gymnasium is not available. Install with: pip install gymnasium"
            )

        self.symbol = symbol
        self.timeframe = timeframe
        self.start_date = start_date
        self.end_date = end_date
        self.initial_balance = initial_balance
        self.commission = commission
        self.slippage = slippage
        self.market_hours_only = market_hours_only
        self.lookback_window = lookback_window
        self.tech_indicators = tech_indicators or []

        # Setup components
        self.data_connector = get_connector(connector_type, **connector_kwargs)
        self._setup_data_connector()
        self.market_friction = MarketFrictionSimulator(
            commission=commission, slippage=slippage
        )
        self.performance_metrics = PerformanceMetrics()

        # Initialize state
        self.current_step = 0
        self.balance = initial_balance
        self.position = 0.0
        self.position_value = 0.0
        self.portfolio_value = initial_balance
        self.trade_history = []
        self.observations = []

        # Setup spaces
        self._setup_spaces()

    def _setup_data_connector(self):
        """Setup the data connector and fetch initial data."""
        try:
            self.data = self.data_connector.get_historical_data(
                symbol=self.symbol,
                timeframe=self.timeframe,
                start_date=self.start_date,
                end_date=self.end_date,
                market_hours_only=self.market_hours_only,
            )
            self.data_len = len(self.data)
            self._add_technical_indicators()
        except Exception as e:
            raise FinRLDataError(f"Error fetching data: {str(e)}")

    def _setup_market_friction(self):
        """Setup market friction simulator."""
        self.market_friction = MarketFrictionSimulator(
            commission=self.commission, slippage=self.slippage
        )

    def _setup_performance_metrics(self):
        """Setup performance metrics calculator."""
        self.performance_metrics = PerformanceMetrics()

    def _setup_spaces(self):
        """Setup action and observation spaces."""
        # Action space: [hold, buy, sell]
        self.action_space = spaces.Discrete(3)

        # Observation space includes price data and technical indicators
        # Base features: open, high, low, close, volume, position, portfolio_value, cash
        base_features = 8
        # Add technical indicators
        indicator_features = len(self.tech_indicators) if self.tech_indicators else 0
        # Total features = base features + indicators
        total_features = base_features + indicator_features

        # Multiply by lookback window for temporal dimension
        observation_dim = total_features * self.lookback_window

        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(observation_dim,), dtype=np.float32
        )

    def _add_technical_indicators(self):
        """Add technical indicators to the data."""
        if not self.tech_indicators:
            return

        try:
            # Import here to avoid circular imports
            from quantchain.analysis.technical_indicators import add_indicators

            self.data = add_indicators(self.data, self.tech_indicators)
        except ImportError:
            logger.warning(
                "Technical indicators module not found. No indicators will be added."
            )
        except Exception as e:
            logger.warning(f"Error adding technical indicators: {str(e)}")

    def reset(self, seed=None, options=None):
        """Reset the environment to initial state.

        Args:
            seed: Random seed for reproducibility
            options: Additional options for reset

        Returns:
            Initial observation and info dictionary
        """
        # Set random seed if provided
        if seed is not None:
            np.random.seed(seed)

        # Reset state
        self.current_step = self.lookback_window  # Start after initial window
        self.balance = self.initial_balance
        self.position = 0.0
        self.position_value = 0.0
        self.portfolio_value = self.initial_balance
        self.trade_history = []
        self.observations = []

        # Get initial observation
        observation = self._get_observation()

        # Info dictionary
        info = {
            "balance": self.balance,
            "position": self.position,
            "position_value": self.position_value,
            "portfolio_value": self.portfolio_value,
        }

        return observation, info

    def step(self, action):
        """Execute one step in the environment.

        Args:
            action: Action to take (0: hold, 1: buy, 2: sell)

        Returns:
            Tuple of (observation, reward, terminated, truncated, info)
        """
        # Get current price
        current_price = self.data["close"].iloc[self.current_step]

        # Store previous portfolio value for reward calculation
        prev_portfolio_value = self.portfolio_value

        # Execute action
        self._execute_action(action, current_price)

        # Move to next step
        self.current_step += 1

        # Check if episode is done
        terminated = self.current_step >= self.data_len - 1
        truncated = False

        # Get new observation
        observation = self._get_observation()

        # Calculate reward
        reward = self._calculate_reward(prev_portfolio_value)

        # Info dictionary
        info = {
            "balance": self.balance,
            "position": self.position,
            "position_value": self.position_value,
            "portfolio_value": self.portfolio_value,
            "current_price": current_price,
        }

        return observation, reward, terminated, truncated, info

    def _execute_action(self, action, current_price):
        """Execute the specified action.

        Args:
            action: Action to take (0: hold, 1: buy, 2: sell)
            current_price: Current price of the asset
        """
        # Hold action
        if action == 0:
            return

        # Buy action - use 95% of available balance
        elif action == 1 and self.balance > 0:
            trade_value = self.balance * 0.95
            trade_size = trade_value / current_price

            # Apply market friction
            executed_size, executed_price, cost = self.market_friction.execute_trade(
                "buy", trade_size, current_price
            )

            # Update position and balance
            self.position += executed_size
            self.balance -= executed_size * executed_price
            self.balance -= cost

            # Record trade
            self.trade_history.append(
                {
                    "step": self.current_step,
                    "action": "buy",
                    "size": executed_size,
                    "price": executed_price,
                    "cost": cost,
                }
            )

        # Sell action - sell all position
        elif action == 2 and self.position > 0:
            trade_size = self.position

            # Apply market friction
            executed_size, executed_price, cost = self.market_friction.execute_trade(
                "sell", trade_size, current_price
            )

            # Update position and balance
            proceeds = executed_size * executed_price
            self.position = 0
            self.balance += proceeds
            self.balance -= cost

            # Record trade
            self.trade_history.append(
                {
                    "step": self.current_step,
                    "action": "sell",
                    "size": executed_size,
                    "price": executed_price,
                    "cost": cost,
                }
            )

        # Update position value and portfolio value
        self.position_value = self.position * current_price
        self.portfolio_value = self.balance + self.position_value

    def _get_observation(self):
        """Get the current observation.

        Returns:
            Numpy array containing the observation
        """
        # Get recent data
        start_idx = max(0, self.current_step - self.lookback_window)
        end_idx = self.current_step + 1
        recent_data = self.data.iloc[start_idx:end_idx]

        # Prepare observation features
        observations = []

        for _, row in recent_data.iterrows():
            # Base features: open, high, low, close, volume
            ohlcv = [row["open"], row["high"], row["low"], row["close"], row["volume"]]

            # Portfolio features
            portfolio_features = [
                self.position,
                self.position_value,
                self.portfolio_value,
            ]

            # Technical indicator features
            indicator_features = []
            for indicator in self.tech_indicators:
                if indicator in row:
                    indicator_features.append(row[indicator])

            # Combine all features
            obs_features = ohlcv + portfolio_features + indicator_features
            observations.extend(obs_features)

        # Convert to numpy array and ensure correct size
        observations_array = np.array(observations, dtype=np.float32)

        # Pad or truncate to match observation space
        obs_dim = self.observation_space.shape[0]
        if len(observations_array) < obs_dim:
            # Pad with zeros
            padding = np.zeros(obs_dim - len(observations_array))
            observations_array = np.concatenate([observations_array, padding])
        elif len(observations_array) > obs_dim:
            # Truncate
            observations_array = observations_array[:obs_dim]

        return observations_array

    def _get_last_observation(self):
        """Get the last observation without updating the current step.

        Returns:
            Numpy array containing the last observation
        """
        # Save current step
        current_step_backup = self.current_step

        # Get observation
        observation = self._get_observation()

        # Restore current step
        self.current_step = current_step_backup

        return observation

    def _calculate_reward(self, prev_portfolio_value):
        """Calculate reward based on portfolio value change.

        Args:
            prev_portfolio_value: Previous portfolio value

        Returns:
            Calculated reward
        """
        # Simple reward: portfolio value change percentage
        reward = (self.portfolio_value - prev_portfolio_value) / prev_portfolio_value

        # Scale reward to be in reasonable range
        reward *= 100

        return reward

    def render(self, mode="human"):
        """Render the environment state.

        Args:
            mode: Rendering mode ('human' for print, 'rgb_array' for array)
        """
        if mode == "human":
            print(f"Step: {self.current_step}")
            print(f"Balance: ${self.balance:.2f}")
            print(f"Position: {self.position:.6f}")
            print(f"Position Value: ${self.position_value:.2f}")
            print(f"Portfolio Value: ${self.portfolio_value:.2f}")
        elif mode == "rgb_array":
            # Not implemented yet
            pass

    def get_performance_metrics(self):
        """Get detailed performance metrics.

        Returns:
            Dictionary with performance metrics
        """
        # Calculate returns from trade history
        returns = []
        for i in range(1, len(self.trade_history)):
            if self.trade_history[i]["action"] == "sell" and i > 0:
                # Find corresponding buy
                for j in range(i - 1, -1, -1):
                    if self.trade_history[j]["action"] == "buy":
                        buy_price = self.trade_history[j]["price"]
                        sell_price = self.trade_history[i]["price"]
                        returns.append((sell_price - buy_price) / buy_price)
                        break

        # Calculate metrics
        metrics = {
            "total_return": (
                (self.portfolio_value - self.initial_balance) / self.initial_balance
            ),
            "trades_count": len(self.trade_history),
            "average_return": sum(returns) / len(returns) if returns else 0,
            "win_rate": (
                sum(1 for r in returns if r > 0) / len(returns) if returns else 0
            ),
        }

        return metrics
