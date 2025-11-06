"""
Market friction simulation for realistic backtesting including commission, slippage,
and latency.
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random
import math


# Custom Exceptions
class InvalidFrictionModel(Exception):
    """Raised for unsupported friction model types."""

    pass


class InvalidParameter(Exception):
    """Raised for invalid parameter values."""

    pass


class FrictionCalculationError(Exception):
    """Raised for friction calculation failures."""

    pass


# Commission Models
@dataclass
class CommissionModel:
    """Base class for commission models."""

    model_type: str = "base"

    def calculate(
        self, trade_value: float, side: str, symbol: Optional[str] = None
    ) -> float:
        """Calculate commission amount."""
        raise NotImplementedError


@dataclass
class FlatCommission(CommissionModel):
    """Fixed fee per trade."""

    fee_per_trade: float = 1.0
    fee_per_contract: float = 0.0
    min_fee: float = 0.0
    model_type: str = "flat"

    def __post_init__(self) -> None:
        """Validate parameters."""
        if self.fee_per_trade < 0:
            raise InvalidParameter("fee_per_trade must be non-negative")
        if self.fee_per_contract < 0:
            raise InvalidParameter("fee_per_contract must be non-negative")
        if self.min_fee < 0:
            raise InvalidParameter("min_fee must be non-negative")

    def calculate(
        self, trade_value: float, side: str, symbol: Optional[str] = None
    ) -> float:
        """Calculate flat commission."""
        if trade_value < 0:
            trade_value = abs(trade_value)

        commission = self.fee_per_trade + (self.fee_per_contract * trade_value)
        return max(commission, self.min_fee)


@dataclass
class PercentageCommission(CommissionModel):
    """Percentage-based commission."""

    rate: float = 0.001  # 0.1%
    min_fee: float = 0.0
    max_fee: float = float("inf")
    model_type: str = "percentage"

    def __post_init__(self) -> None:
        """Validate parameters."""
        if self.rate < 0:
            raise InvalidParameter("rate must be non-negative")
        if self.min_fee < 0:
            raise InvalidParameter("min_fee must be non-negative")
        if self.max_fee < 0:
            raise InvalidParameter("max_fee must be non-negative")

    def calculate(
        self, trade_value: float, side: str, symbol: Optional[str] = None
    ) -> float:
        """Calculate percentage commission."""
        if trade_value < 0:
            trade_value = abs(trade_value)

        commission = trade_value * self.rate
        return max(min(commission, self.max_fee), self.min_fee)


@dataclass
class TieredCommission(CommissionModel):
    """Volume-dependent tiered commission."""

    tiers: List[Tuple[float, float]] = field(default_factory=list)
    base_rate: float = 0.001
    volume_window: str = "1M"  # monthly volume tracking
    model_type: str = "tiered"

    def __post_init__(self) -> None:
        """Initialize default tiers if not provided."""
        if not self.tiers:
            self.tiers = [
                (0, 0.003),  # >0 trades: 0.3%
                (100, 0.002),  # >100 trades: 0.2%
                (1000, 0.001),  # >1000 trades: 0.1%
                (10000, 0.0005),  # >10000 trades: 0.05%
            ]

        if self.base_rate < 0:
            raise InvalidParameter("base_rate must be non-negative")

    def calculate(
        self,
        trade_value: float,
        side: str,
        symbol: Optional[str] = None,
        monthly_volume: int = 0,
    ) -> float:
        """Calculate tiered commission based on volume."""
        if trade_value < 0:
            trade_value = abs(trade_value)

        applicable_rate = next(
            (
                rate
                for threshold, rate in reversed(self.tiers)
                if monthly_volume >= threshold
            ),
            self.base_rate,
        )
        return trade_value * applicable_rate


# Slippage Models
@dataclass
class SlippageModel:
    """Base class for slippage models."""

    model_type: str = "base"

    def apply(
        self,
        price: float,
        quantity: int,
        side: str,
        market_depth: Optional[Dict[str, float]] = None,
    ) -> float:
        """Apply slippage to price."""
        raise NotImplementedError


@dataclass
class FixedSlippage(SlippageModel):
    """Fixed percentage slippage."""

    rate: float = 0.0001  # 0.01%
    model_type: str = "fixed"

    def __post_init__(self) -> None:
        """Validate parameters."""
        if self.rate < 0:
            raise InvalidParameter("rate must be non-negative")

    def apply(
        self,
        price: float,
        quantity: int,
        side: str,
        market_depth: Optional[Dict[str, float]] = None,
    ) -> float:
        """Apply fixed slippage."""
        if price <= 0:
            raise FrictionCalculationError("price must be positive")
        if quantity <= 0:
            raise FrictionCalculationError("quantity must be positive")
        if side not in ["buy", "sell"]:
            raise FrictionCalculationError("side must be 'buy' or 'sell'")

        slippage_amount = price * self.rate
        return price - slippage_amount if side == "buy" else price + slippage_amount


@dataclass
class VolumeImpactSlippage(SlippageModel):
    """Square-root volume impact model."""

    base_rate: float = 0.0001
    volume_impact_factor: float = 0.001
    avg_daily_volume: float = 1000000
    model_type: str = "volume_impact"

    def __post_init__(self) -> None:
        """Validate parameters."""
        if self.base_rate < 0:
            raise InvalidParameter("base_rate must be non-negative")
        if self.volume_impact_factor < 0:
            raise InvalidParameter("volume_impact_factor must be non-negative")
        if self.avg_daily_volume <= 0:
            raise InvalidParameter("avg_daily_volume must be positive")

    def apply(
        self,
        price: float,
        quantity: int,
        side: str,
        market_depth: Optional[Dict[str, float]] = None,
    ) -> float:
        """Apply volume impact slippage."""
        if price <= 0:
            raise FrictionCalculationError("price must be positive")
        if quantity <= 0:
            raise FrictionCalculationError("quantity must be positive")
        if side not in ["buy", "sell"]:
            raise FrictionCalculationError("side must be 'buy' or 'sell'")

        volume_impact = self.volume_impact_factor * math.sqrt(
            quantity / self.avg_daily_volume
        )
        total_slippage = price * (self.base_rate + volume_impact)

        return price - total_slippage if side == "buy" else price + total_slippage


@dataclass
class BidAskSpreadSlippage(SlippageModel):
    """Bid-ask spread simulation."""

    base_spread_rate: float = 0.0005  # 0.05%
    volatility_factor: float = 0.1
    model_type: str = "bid_ask_spread"

    def __post_init__(self) -> None:
        """Validate parameters."""
        if self.base_spread_rate < 0:
            raise InvalidParameter("base_spread_rate must be non-negative")
        if self.volatility_factor < 0:
            raise InvalidParameter("volatility_factor must be non-negative")

    def apply(
        self,
        price: float,
        quantity: int,
        side: str,
        market_depth: Optional[Dict[str, float]] = None,
    ) -> float:
        """Apply bid-ask spread slippage."""
        if price <= 0:
            raise FrictionCalculationError("price must be positive")
        if quantity <= 0:
            raise FrictionCalculationError("quantity must be positive")
        if side not in ["buy", "sell"]:
            raise FrictionCalculationError("side must be 'buy' or 'sell'")

        if market_depth and "volatility" in market_depth:
            spread = price * (
                self.base_spread_rate
                * (1 + self.volatility_factor * market_depth["volatility"])
            )
        else:
            spread = price * self.base_spread_rate

        half_spread = spread / 2
        return price - half_spread if side == "buy" else price + half_spread


# Latency Models
@dataclass
class LatencyModel:
    """Base class for latency models."""

    model_type: str = "base"

    def apply(self, timestamp: datetime) -> datetime:
        """Apply latency to timestamp."""
        raise NotImplementedError


@dataclass
class FixedLatency(LatencyModel):
    """Fixed latency in milliseconds."""

    latency_ms: float = 10.0
    model_type: str = "fixed"

    def __post_init__(self) -> None:
        """Validate parameters."""
        if self.latency_ms < 0:
            raise InvalidParameter("latency_ms must be non-negative")

    def apply(self, timestamp: datetime) -> datetime:
        """Apply fixed latency."""
        return timestamp + timedelta(milliseconds=self.latency_ms)


@dataclass
class UniformRandomLatency(LatencyModel):
    """Uniform random latency between min and max."""

    min_ms: float = 5.0
    max_ms: float = 50.0
    model_type: str = "uniform"

    def __post_init__(self) -> None:
        """Validate parameters."""
        if self.min_ms < 0 or self.max_ms < 0:
            raise InvalidParameter("latency values must be non-negative")
        if self.min_ms >= self.max_ms:
            raise InvalidParameter("min_ms must be less than max_ms")

    def apply(self, timestamp: datetime) -> datetime:
        """Apply uniform random latency."""
        latency = random.uniform(self.min_ms, self.max_ms)
        return timestamp + timedelta(milliseconds=latency)


@dataclass
class NormalRandomLatency(LatencyModel):
    """Normal distribution latency."""

    mean_ms: float = 20.0
    std_ms: float = 5.0
    min_ms: float = 1.0
    max_ms: float = 100.0
    model_type: str = "normal"

    def __post_init__(self) -> None:
        """Validate parameters."""
        if self.mean_ms < 0 or self.std_ms < 0:
            raise InvalidParameter("mean_ms and std_ms must be non-negative")
        if self.min_ms < 0 or self.max_ms < 0:
            raise InvalidParameter("min_ms and max_ms must be non-negative")
        if self.min_ms >= self.max_ms:
            raise InvalidParameter("min_ms must be less than max_ms")

    def apply(self, timestamp: datetime) -> datetime:
        """Apply normal random latency."""
        latency = max(
            self.min_ms, min(self.max_ms, random.gauss(self.mean_ms, self.std_ms))
        )
        return timestamp + timedelta(milliseconds=latency)


# Configuration System
@dataclass
class MarketFrictionConfig:
    """Global market friction configuration."""

    commission_model: CommissionModel
    slippage_model: SlippageModel
    latency_model: LatencyModel
    asset_specific: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def get_asset_config(self, symbol: str) -> Dict[str, Any]:
        """Get asset-specific friction configuration."""
        return self.asset_specific.get(symbol, {})


# Main Simulator
class MarketFrictionSimulator:
    """Simulates market friction effects in backtesting."""

    def __init__(self, config: MarketFrictionConfig):
        """Initialize with friction configuration."""
        if not isinstance(config, MarketFrictionConfig):
            raise InvalidParameter("config must be a MarketFrictionConfig instance")
        self.config = config

    def _get_asset_models(
        self, symbol: Optional[str] = None
    ) -> Tuple[CommissionModel, SlippageModel, LatencyModel]:
        """Get asset-specific models if available, otherwise use defaults."""
        asset_config = self.config.get_asset_config(symbol) if symbol else {}

        commission = asset_config.get("commission", self.config.commission_model)
        slippage = asset_config.get("slippage", self.config.slippage_model)
        latency = asset_config.get("latency", self.config.latency_model)

        return commission, slippage, latency

    def apply_commission(
        self, trade_value: float, side: str, symbol: Optional[str] = None
    ) -> float:
        """Calculate commission for a trade."""
        if not isinstance(trade_value, (int, float)):
            raise FrictionCalculationError("trade_value must be numeric")
        if side not in ["buy", "sell"]:
            raise FrictionCalculationError("side must be 'buy' or 'sell'")

        commission, _, _ = self._get_asset_models(symbol)
        return commission.calculate(trade_value, side, symbol)

    def apply_slippage(
        self,
        price: float,
        quantity: int,
        side: str,
        market_depth: Optional[Dict[str, float]] = None,
        symbol: Optional[str] = None,
    ) -> float:
        """Apply slippage to execution price."""
        if not isinstance(price, (int, float)):
            raise FrictionCalculationError("price must be numeric")
        if not isinstance(quantity, int):
            raise FrictionCalculationError("quantity must be integer")

        _, slippage, _ = self._get_asset_models(symbol)
        return slippage.apply(price, quantity, side, market_depth)

    def apply_latency(
        self, timestamp: datetime, symbol: Optional[str] = None
    ) -> datetime:
        """Apply execution latency to timestamp."""
        if not isinstance(timestamp, datetime):
            raise FrictionCalculationError("timestamp must be datetime")

        _, _, latency = self._get_asset_models(symbol)
        return latency.apply(timestamp)

    def get_total_cost(
        self, price: float, quantity: int, side: str, symbol: Optional[str] = None
    ) -> Dict[str, float]:
        """Calculate total friction costs for a trade."""
        if not isinstance(price, (int, float)):
            raise FrictionCalculationError("price must be numeric")
        if not isinstance(quantity, int):
            raise FrictionCalculationError("quantity must be integer")
        if side not in ["buy", "sell"]:
            raise FrictionCalculationError("side must be 'buy' or 'sell'")

        # Calculate trade value
        trade_value = price * quantity

        # Calculate commission
        commission_cost = self.apply_commission(trade_value, side, symbol)

        # Calculate slippage cost (difference between requested and executed price)
        executed_price = self.apply_slippage(price, quantity, side, symbol=symbol)
        slippage_cost = abs(executed_price - price) * quantity

        total_cost = commission_cost + slippage_cost

        return {
            "commission": commission_cost,
            "slippage": slippage_cost,
            "total": total_cost,
            "executed_price": executed_price,
        }


# Plugin Interface
class CustomFrictionModel:
    """Interface for custom friction model plugins."""

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration."""
        pass

    def calculate_cost(self, trade_info: Dict[str, Any]) -> float:
        """Calculate custom friction cost."""
        raise NotImplementedError

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration."""
        raise NotImplementedError
