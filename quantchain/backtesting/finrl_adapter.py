"""FinRL adapter for QuantChain backtesting."""

import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
import pandas as pd
import numpy as np

try:
    import gymnasium
    _GYMNASIUM_AVAILABLE = True
except ImportError:
    _GYMNASIUM_AVAILABLE = False

try:
    import stable_baselines3
    _SB3_AVAILABLE = True
except ImportError:
    _SB3_AVAILABLE = False

try:
    import quantchain.backtesting.engine as engine
    _ENGINE_AVAILABLE = True
except ImportError:
    _ENGINE_AVAILABLE = False


class FinRLError(Exception):
    """Base exception for FinRL adapter."""
    pass


class FinRLAdapterError(FinRLError):
    """Base adapter error for FinRL."""
    pass


class FinRLConnectionError(FinRLError):
    """Exception for connection errors."""
    pass


class FinRLDataError(FinRLError):
    """Exception for data errors."""
    pass


class FinRLConfig:
    """Configuration for FinRL adapter."""

    def __init__(
        self,
        initial_cash: float = 1000000,
        initial_position: Optional[Dict[str, int]] = None,
        buy_cost_pct: float = 0.001,
        sell_cost_pct: float = 0.001,
        min_cost_pct: float = 0.001,
    ):
        self.initial_cash = initial_cash
        self.initial_position = initial_position or {}
        self.buy_cost_pct = buy_cost_pct
        self.sell_cost_pct = sell_cost_pct
        self.min_cost_pct = min_cost_pct


class FinRLPortfolio:
    """Portfolio representation for FinRL."""

    def __init__(
        self,
        initial_cash: float = 1000000,
        initial_position: Optional[Dict[str, int]] = None,
    ):
        self.initial_cash = initial_cash
        self.initial_position = initial_position or {}
        self.reset()

    def reset(self) -> None:
        """Reset portfolio to initial values."""
        self.cash = self.initial_cash
        self.positions = dict(self.initial_position)

    def buy_stock(
        self,
        symbol: str,
        amount: int,
        price: float,
        cost_pct: float = 0.001
    ) -> bool:
        """Buy stocks and update portfolio."""
        cost = amount * price * (1 + cost_pct)
        if self.cash < cost:
            return False

        self.cash -= cost
        if symbol in self.positions:
            self.positions[symbol] += amount
        else:
            self.positions[symbol] = amount
        return True

    def sell_stock(
        self,
        symbol: str,
        amount: int,
        price: float,
        cost_pct: float = 0.001
    ) -> bool:
        """Sell stocks and update portfolio."""
        if symbol not in self.positions or self.positions[symbol] < amount:
            return False

        revenue = amount * price * (1 - cost_pct)
        self.cash += revenue
        self.positions[symbol] -= amount

        if self.positions[symbol] == 0:
            del self.positions[symbol]

        return True

    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value."""
        total_value = self.cash
        for symbol, amount in self.positions.items():
            if symbol in current_prices:
                total_value += amount * current_prices[symbol]
        return total_value

    @property
    def portfolio_value(self) -> float:
        """Get portfolio value (placeholder without current prices)."""
        return self.cash


class FinRLStrategy:
    """Strategy for FinRL."""

    def __init__(self, strategy_type: str, params: Optional[Dict[str, Any]] = None):
        self.strategy_type = strategy_type
        self.params = params or {}

    def predict(self, state: pd.DataFrame) -> Dict[str, Any]:
        """Predict action based on state."""
        # This is a simplified implementation
        # In a real scenario, this would use a trained RL model
        return {"action": 0}  # Default to HOLD


class FinRLResult:
    """Result of FinRL backtest."""

    def __init__(
        self,
        total_return: float = 0.0,
        annualized_return: float = 0.0,
        sharpe_ratio: float = 0.0,
        max_drawdown: float = 0.0,
        win_rate: float = 0.0,
        total_trades: int = 0,
    ):
        self.total_return = total_return
        self.annualized_return = annualized_return
        self.sharpe_ratio = sharpe_ratio
        self.max_drawdown = max_drawdown
        self.win_rate = win_rate
        self.total_trades = total_trades


class FinRLAdapter:
    """Adapter for FinRL integration."""

    def __init__(self, config: Optional[FinRLConfig] = None):
        self.config = config or FinRLConfig()
        self.portfolio = FinRLPortfolio(
            self.config.initial_cash,
            self.config.initial_position
        )
        self.strategy = None

    def reset(self) -> None:
        """Reset adapter state."""
        self.portfolio.reset()

    def trade(self, state: pd.DataFrame, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trade based on action."""
        # Default price (in a real scenario, this would be from market data)
        price = state.iloc[-1]['close'] if len(state) > 0 else 100
        symbol = "SYMBOL"  # Default symbol

        action_type = action.get('action', 0)  # 0=HOLD, 1=BUY, 2=SELL

        if action_type == 1:  # BUY
            # Buy 10% of current cash worth of stock
            amount = int(self.portfolio.cash * 0.1 / price)
            if amount > 0 and self.portfolio.buy_stock(
                symbol, amount, price, self.config.buy_cost_pct
            ):
                return {
                    "status": "buy",
                    "amount": amount,
                    "cost": amount * price * (1 + self.config.buy_cost_pct)
                }
        elif action_type == 2:  # SELL
            # Sell all position
            if symbol in self.portfolio.positions:
                amount = self.portfolio.positions[symbol]
                if amount > 0 and self.portfolio.sell_stock(
                    symbol, amount, price, self.config.sell_cost_pct
                ):
                    return {
                        "status": "sell",
                        "amount": amount,
                        "cost": amount * price * self.config.sell_cost_pct
                    }

        # Default to HOLD
        return {
            "status": "hold",
            "amount": 0,
            "cost": 0
        }

    def get_state(self) -> Dict[str, Any]:
        """Get current state."""
        return {
            "portfolio_value": self.portfolio.portfolio_value,
            "cash": self.portfolio.cash,
            "positions": dict(self.portfolio.positions)
        }


def get_connector(config: Optional[FinRLConfig] = None) -> FinRLAdapter:
    """Get a FinRL connector with the given configuration."""
    return FinRLAdapter(config)
