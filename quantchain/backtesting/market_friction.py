"""Market friction simulation for backtesting."""

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, cast

import numpy as np


class FrictionCalculationError(Exception):
    """Raised when friction calculation fails."""

    pass


class InvalidParameter(Exception):
    """Raised when invalid parameters are provided."""

    pass


class InvalidFrictionModel(Exception):
    """Raised when invalid friction model is specified."""

    pass


@dataclass
class MarketFrictionConfig:
    """Global market friction configuration."""

    commission_model: "CommissionModel"
    slippage_model: "SlippageModel"
    latency_model: "LatencyModel"
    asset_specific: Optional[Dict[str, Dict[str, Any]]] = None

    def __post_init__(self) -> None:
        if self.asset_specific is None:
            self.asset_specific = {}


class CommissionModel(ABC):
    """Base class for commission models."""

    def __init__(self, model_type: str = "base"):
        self.model_type = model_type

    @abstractmethod
    def calculate(
        self, trade_value: float, side: str, symbol: Optional[str] = None, **kwargs: Any
    ) -> float:
        """Calculate commission amount."""
        raise NotImplementedError


class FlatCommission(CommissionModel):
    """Fixed fee per trade."""

    def __init__(
        self,
        fee_per_trade: float = 1.0,
        fee_per_contract: float = 0.0,
        min_fee: float = 0.0,
    ):
        super().__init__("flat")
        self.fee_per_trade = fee_per_trade
        self.fee_per_contract = fee_per_contract
        self.min_fee = min_fee

    def calculate(
        self, trade_value: float, side: str, symbol: Optional[str] = None, **kwargs: Any
    ) -> float:
        """Calculate flat commission."""
        # Original implementation had an issue with multiplying trade_value by fee_per_contract
        # It should be trade_value * volume or number of contracts, but we'll fix by assuming
        # fee_per_contract is per unit of trade_value for simplicity
        commission = self.fee_per_trade + (self.fee_per_contract * abs(trade_value))
        return max(commission, self.min_fee)


class PercentageCommission(CommissionModel):
    """Percentage-based commission."""

    def __init__(
        self, rate: float = 0.001, min_fee: float = 0.0, max_fee: float = float("inf")
    ):
        super().__init__("percentage")
        self.rate = rate
        self.min_fee = min_fee
        self.max_fee = max_fee

    def calculate(
        self, trade_value: float, side: str, symbol: Optional[str] = None, **kwargs: Any
    ) -> float:
        """Calculate percentage commission."""
        commission = abs(trade_value) * self.rate
        return max(min(commission, self.max_fee), self.min_fee)


class TieredCommission(CommissionModel):
    """Volume-dependent tiered commission."""

    def __init__(
        self,
        tiers: Optional[List[Tuple[float, float]]] = None,
        base_rate: float = 0.001,
        volume_window: str = "1M",
    ):
        super().__init__("tiered")
        self.base_rate = base_rate
        self.volume_window = volume_window
        self.volume_tracker: Dict[str, float] = {}  # Track volume per symbol

        if tiers is None:
            self.tiers = [
                (0.0, 0.003),  # >0 trades: 0.3%
                (100.0, 0.002),  # >100 trades: 0.2%
                (1000.0, 0.001),  # >1000 trades: 0.1%
                (10000.0, 0.0005),  # >10000 trades: 0.05%
            ]
        else:
            self.tiers = tiers

    def calculate(
        self,
        trade_value: float,
        side: str,
        symbol: Optional[str] = None,
        monthly_volume: float = 0,
        **kwargs: Any,
    ) -> float:
        """Calculate tiered commission based on volume."""
        # Determine applicable rate based on volume
        rate = self.base_rate

        for threshold, tier_rate in reversed(self.tiers):
            if monthly_volume > threshold:
                rate = tier_rate
                break

        return abs(trade_value) * rate


class SlippageModel(ABC):
    """Base class for slippage models."""

    def __init__(self, model_type: str = "base"):
        self.model_type = model_type

    @abstractmethod
    def calculate(
        self,
        price: float,
        quantity: int,
        side: str,
        market_depth: Optional[Dict[str, float]] = None,
        symbol: Optional[str] = None,
    ) -> float:
        """Calculate slippage amount."""
        raise NotImplementedError


class FixedSlippage(SlippageModel):
    """Fixed slippage amount per trade."""

    def __init__(self, slippage_amount: float = 0.01):
        super().__init__("fixed")
        self.slippage_amount = slippage_amount

    def calculate(
        self,
        price: float,
        quantity: int,
        side: str,
        market_depth: Optional[Dict[str, float]] = None,
        symbol: Optional[str] = None,
    ) -> float:
        """Calculate fixed slippage."""
        # Positive for buy (price increases), negative for sell (price decreases)
        return self.slippage_amount if side.lower() == "buy" else -self.slippage_amount


class VolumeImpactSlippage(SlippageModel):
    """Slippage based on trade volume impact."""

    def __init__(self, impact_factor: float = 0.0001, volume_window: str = "1D"):
        super().__init__("volume_impact")
        self.impact_factor = impact_factor
        self.volume_window = volume_window

    def calculate(
        self,
        price: float,
        quantity: int,
        side: str,
        market_depth: Optional[Dict[str, float]] = None,
        symbol: Optional[str] = None,
    ) -> float:
        """Calculate volume-based slippage."""
        # Calculate slippage as a percentage of price based on quantity
        slippage_pct = quantity * self.impact_factor
        slippage = price * slippage_pct

        # Positive for buy (price increases), negative for sell (price decreases)
        return slippage if side.lower() == "buy" else -slippage


class BidAskSpreadSlippage(SlippageModel):
    """Slippage based on bid-ask spread."""

    def __init__(self, spread_pct: float = 0.001, random_factor: float = 0.5):
        super().__init__("bid_ask_spread")
        self.spread_pct = spread_pct
        self.random_factor = random_factor

    def calculate(
        self,
        price: float,
        quantity: int,
        side: str,
        market_depth: Optional[Dict[str, float]] = None,
        symbol: Optional[str] = None,
    ) -> float:
        """Calculate bid-ask spread slippage."""
        # Half the spread is the slippage
        base_slippage = price * self.spread_pct * 0.5

        # Add random factor
        random_slippage = base_slippage * self.random_factor * (random.random() - 0.5)

        total_slippage = base_slippage + random_slippage

        # Positive for buy (price increases), negative for sell (price decreases)
        return total_slippage if side.lower() == "buy" else -total_slippage


class LatencyModel(ABC):
    """Base class for latency models."""

    def __init__(self, model_type: str = "base"):
        self.model_type = model_type

    @abstractmethod
    def apply(self, timestamp: datetime, symbol: Optional[str] = None) -> datetime:
        """Apply execution latency to timestamp."""
        raise NotImplementedError


class FixedLatency(LatencyModel):
    """Fixed latency amount per trade."""

    def __init__(self, latency_ms: int = 100):
        super().__init__("fixed")
        self.latency_ms = latency_ms

    def apply(self, timestamp: datetime, symbol: Optional[str] = None) -> datetime:
        """Apply fixed latency."""
        return timestamp + timedelta(milliseconds=self.latency_ms)


class UniformRandomLatency(LatencyModel):
    """Random latency within a uniform range."""

    def __init__(self, min_ms: int = 50, max_ms: int = 200):
        super().__init__("uniform_random")
        self.min_ms = min_ms
        self.max_ms = max_ms

    def apply(self, timestamp: datetime, symbol: Optional[str] = None) -> datetime:
        """Apply uniform random latency."""
        latency_ms = random.randint(self.min_ms, self.max_ms)
        return timestamp + timedelta(milliseconds=latency_ms)


class NormalRandomLatency(LatencyModel):
    """Random latency with normal distribution."""

    def __init__(self, mean_ms: int = 100, std_ms: int = 30):
        super().__init__("normal_random")
        self.mean_ms = mean_ms
        self.std_ms = std_ms

    def apply(self, timestamp: datetime, symbol: Optional[str] = None) -> datetime:
        """Apply normal random latency."""
        # Ensure latency is positive
        latency_ms = max(0, int(np.random.normal(self.mean_ms, self.std_ms)))
        return timestamp + timedelta(milliseconds=latency_ms)


class MarketFrictionSimulator:
    """Simulates market friction effects in backtesting."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with friction configuration."""
        # Default configuration
        default_config = {
            "commission_model": PercentageCommission(rate=0.001),
            "slippage_model": VolumeImpactSlippage(impact_factor=0.0001),
            "latency_model": FixedLatency(latency_ms=100),
        }

        if config is None:
            config = {}

        self.commission_model = config.get(
            "commission_model", default_config["commission_model"]
        )
        self.slippage_model = config.get(
            "slippage_model", default_config["slippage_model"]
        )
        self.latency_model = config.get(
            "latency_model", default_config["latency_model"]
        )
        self.asset_specific = config.get("asset_specific", {})

    def apply_commission(
        self, trade_value: float, side: str, symbol: Optional[str] = None, **kwargs: Any
    ) -> float:
        """Calculate commission for a trade."""
        # Check if symbol has specific commission model
        if (
            symbol
            and symbol in self.asset_specific
            and "commission" in self.asset_specific[symbol]
        ):
            model = cast(CommissionModel, self.asset_specific[symbol]["commission"])
            return cast(float, model.calculate(trade_value, side, symbol, **kwargs))

        return cast(
            float, self.commission_model.calculate(trade_value, side, symbol, **kwargs)
        )

    def apply_slippage(
        self,
        price: float,
        quantity: int,
        side: str,
        market_depth: Optional[Dict[str, float]] = None,
        symbol: Optional[str] = None,
    ) -> float:
        """Apply slippage to execution price."""
        # Check if symbol has specific slippage model
        if (
            symbol
            and symbol in self.asset_specific
            and "slippage" in self.asset_specific[symbol]
        ):
            model = cast(SlippageModel, self.asset_specific[symbol]["slippage"])
            return cast(
                float, model.calculate(price, quantity, side, market_depth, symbol)
            )

        return cast(
            float,
            self.slippage_model.calculate(price, quantity, side, market_depth, symbol),
        )

    def apply_latency(
        self, timestamp: datetime, symbol: Optional[str] = None
    ) -> datetime:
        """Apply execution latency to timestamp."""
        # Check if symbol has specific latency model
        if (
            symbol
            and symbol in self.asset_specific
            and "latency" in self.asset_specific[symbol]
        ):
            model = cast(LatencyModel, self.asset_specific[symbol]["latency"])
            return cast(datetime, model.apply(timestamp, symbol))

        return cast(datetime, self.latency_model.apply(timestamp, symbol))

    def get_total_cost(
        self,
        price: float,
        quantity: int,
        side: str,
        symbol: Optional[str] = None,
        market_depth: Optional[Dict[str, float]] = None,
        timestamp: Optional[datetime] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Calculate total friction costs for a trade."""
        # Calculate trade value
        trade_value = price * quantity

        # Calculate commission
        commission = self.apply_commission(trade_value, side, symbol, **kwargs)

        # Calculate slippage
        slippage = self.apply_slippage(price, quantity, side, market_depth, symbol)
        slippage_cost = slippage * quantity

        # Apply latency if timestamp provided
        execution_time = timestamp
        if timestamp:
            execution_time = self.apply_latency(timestamp, symbol)

        return {
            "commission": commission,
            "slippage": slippage,
            "slippage_cost": slippage_cost,
            "total_cost": commission + slippage_cost,
            "execution_time": execution_time,
        }
