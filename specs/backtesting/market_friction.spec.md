# Market Friction Simulation Specification

## Overview
Defines market friction simulation for realistic backtesting including transaction costs, slippage, and latency modeling.

## Core Components

### MarketFrictionSimulator
```python
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

class MarketFrictionSimulator:
    """Simulates market friction effects in backtesting."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with friction configuration."""
        pass
    
    def apply_commission(self, trade_value: float, side: str, symbol: str = None) -> float:
        """Calculate commission for a trade."""
        pass
    
    def apply_slippage(self, price: float, quantity: int, side: str, 
                      market_depth: Dict[str, float] = None, symbol: str = None) -> float:
        """Apply slippage to execution price."""
        pass
    
    def apply_latency(self, timestamp: datetime, symbol: str = None) -> datetime:
        """Apply execution latency to timestamp."""
        pass
    
    def get_total_cost(self, price: float, quantity: int, side: str, 
                      symbol: str = None) -> Dict[str, float]:
        """Calculate total friction costs for a trade."""
        pass
```

### Commission Models

#### Base Commission Model
```python
@dataclass
class CommissionModel:
    """Base class for commission models."""
    model_type: str
    
    def calculate(self, trade_value: float, side: str, symbol: str = None) -> float:
        """Calculate commission amount."""
        raise NotImplementedError
```

#### Flat Commission
```python
@dataclass
class FlatCommission(CommissionModel):
    """Fixed fee per trade."""
    fee_per_trade: float = 1.0
    fee_per_contract: float = 0.0
    min_fee: float = 0.0
    
    def calculate(self, trade_value: float, side: str, symbol: str = None) -> float:
        """Calculate flat commission."""
        return max(self.fee_per_trade + (self.fee_per_contract * abs(trade_value)), self.min_fee)
```

#### Percentage Commission
```python
@dataclass
class PercentageCommission(CommissionModel):
    """Percentage-based commission."""
    rate: float = 0.001  # 0.1%
    min_fee: float = 0.0
    max_fee: float = float('inf')
    
    def calculate(self, trade_value: float, side: str, symbol: str = None) -> float:
        """Calculate percentage commission."""
        commission = abs(trade_value) * self.rate
        return max(min(commission, self.max_fee), self.min_fee)
```

#### Tiered Commission
```python
@dataclass
class TieredCommission(CommissionModel):
    """Volume-dependent tiered commission."""
    tiers: List[Tuple[float, float]] = None  # [(volume_threshold, rate), ...]
    base_rate: float = 0.001
    volume_window: str = '1M'  # monthly volume tracking
    
    def __post_init__(self):
        if self.tiers is None:
            self.tiers = [
                (0, 0.003),      # >0 trades: 0.3%
                (100, 0.002),     # >100 trades: 0.2%
                (1000, 0.001),    # >1000 trades: 0.1%
                (10000, 0.0005),  # >10000 trades: 0.05%
            ]
    
    def calculate(self, trade_value: float, side: str, symbol: str = None, 
                  monthly_volume: int = 0) -> float:
        """Calculate tiered commission based on volume."""
        applicable_rate = self.base_rate
        for threshold, rate in reversed(self.tiers):
            if monthly_volume >= threshold:
                applicable_rate = rate
                break
        return abs(trade_value) * applicable_rate
```

### Slippage Models

#### Base Slippage Model
```python
@dataclass
class SlippageModel:
    """Base class for slippage models."""
    model_type: str
    
    def apply(self, price: float, quantity: int, side: str, 
              market_depth: Dict[str, float] = None) -> float:
        """Apply slippage to price."""
        raise NotImplementedError
```

#### Fixed Slippage
```python
@dataclass
class FixedSlippage(SlippageModel):
    """Fixed percentage slippage."""
    rate: float = 0.0001  # 0.01%
    
    def apply(self, price: float, quantity: int, side: str, 
              market_depth: Dict[str, float] = None) -> float:
        """Apply fixed slippage."""
        slippage_amount = price * self.rate
        return price - slippage_amount if side == 'buy' else price + slippage_amount
```

#### Volume Impact Slippage
```python
@dataclass
class VolumeImpactSlippage(SlippageModel):
    """Square-root volume impact model."""
    base_rate: float = 0.0001
    volume_impact_factor: float = 0.001
    avg_daily_volume: float = 1000000
    
    def apply(self, price: float, quantity: int, side: str, 
              market_depth: Dict[str, float] = None) -> float:
        """Apply volume impact slippage."""
        base_slippage = price * self.base_rate
        volume_impact = self.volume_impact_factor * (quantity / self.avg_daily_volume) ** 0.5
        total_slippage = price * (base_slippage + volume_impact)
        return price - total_slippage if side == 'buy' else price + total_slippage
```

#### Bid-Ask Spread Slippage
```python
@dataclass
class BidAskSpreadSlippage(SlippageModel):
    """Bid-ask spread simulation."""
    base_spread_rate: float = 0.0005  # 0.05%
    volatility_factor: float = 0.1
    
    def apply(self, price: float, quantity: int, side: str, 
              market_depth: Dict[str, float] = None) -> float:
        """Apply bid-ask spread slippage."""
        if market_depth and 'volatility' in market_depth:
            spread = price * (self.base_spread_rate * (1 + self.volatility_factor * market_depth['volatility']))
        else:
            spread = price * self.base_spread_rate
        
        half_spread = spread / 2
        return price - half_spread if side == 'buy' else price + half_spread
```

### Latency Models

#### Base Latency Model
```python
@dataclass
class LatencyModel:
    """Base class for latency models."""
    model_type: str
    
    def apply(self, timestamp: datetime) -> datetime:
        """Apply latency to timestamp."""
        raise NotImplementedError
```

#### Fixed Latency
```python
@dataclass
class FixedLatency(LatencyModel):
    """Fixed latency in milliseconds."""
    latency_ms: float = 10.0
    
    def apply(self, timestamp: datetime) -> datetime:
        """Apply fixed latency."""
        return timestamp + pd.Timedelta(milliseconds=self.latency_ms)
```

#### Random Uniform Latency
```python
@dataclass
class UniformRandomLatency(LatencyModel):
    """Uniform random latency between min and max."""
    min_ms: float = 5.0
    max_ms: float = 50.0
    
    def apply(self, timestamp: datetime) -> datetime:
        """Apply uniform random latency."""
        import random
        latency = random.uniform(self.min_ms, self.max_ms)
        return timestamp + pd.Timedelta(milliseconds=latency)
```

#### Random Normal Latency
```python
@dataclass
class NormalRandomLatency(LatencyModel):
    """Normal distribution latency."""
    mean_ms: float = 20.0
    std_ms: float = 5.0
    min_ms: float = 1.0
    max_ms: float = 100.0
    
    def apply(self, timestamp: datetime) -> datetime:
        """Apply normal random latency."""
        import random
        latency = max(self.min_ms, min(self.max_ms, 
                     random.gauss(self.mean_ms, self.std_ms)))
        return timestamp + pd.Timedelta(milliseconds=latency)
```

## Configuration System

### Global Friction Configuration
```python
@dataclass
class MarketFrictionConfig:
    """Global market friction configuration."""
    commission_model: CommissionModel
    slippage_model: SlippageModel
    latency_model: LatencyModel
    asset_specific: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.asset_specific is None:
            self.asset_specific = {}
    
    def get_asset_config(self, symbol: str) -> Dict[str, Any]:
        """Get asset-specific friction configuration."""
        return self.asset_specific.get(symbol, {})
```

### Asset-Specific Configuration
```python
# Example configuration
asset_config = {
    'AAPL': {
        'commission': PercentageCommission(rate=0.0005),
        'slippage': VolumeImpactSlippage(avg_daily_volume=50000000),
        'latency': FixedLatency(latency_ms=5.0)
    },
    'BTC-USD': {
        'commission': PercentageCommission(rate=0.001),
        'slippage': BidAskSpreadSlippage(base_spread_rate=0.001),
        'latency': NormalRandomLatency(mean_ms=10.0, std_ms=2.0)
    }
}
```

## Plugin Interface

### Custom Friction Model Plugin
```python
class CustomFrictionModel:
    """Interface for custom friction model plugins."""
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration."""
        pass
    
    def calculate_cost(self, trade_info: Dict[str, Any]) -> float:
        """Calculate custom friction cost."""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration."""
        pass
```

## Error Handling

### Configuration Errors
- `InvalidFrictionModel` for unsupported model types
- `InvalidParameter` for invalid parameter values
- `IncompatibleConfig` for conflicting configurations

### Runtime Errors
- `FrictionCalculationError` for calculation failures
- `InsufficientDataError` when market depth data is missing
- `AssetConfigError` for asset-specific configuration issues

## Performance Requirements

- Slippage calculation < 100 microseconds per trade
- Commission calculation < 50 microseconds per trade
- Memory usage < 1MB for 1M trades
- Support for parallel friction calculation

## Dependencies
- numpy >= 1.24.0
- pandas >= 2.0.0
- dataclasses (Python 3.7+)
- typing extensions
