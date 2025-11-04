# Backtesting Engine Specification

## Overview
Defines the core backtesting engine interface that supports both Backtesting.py and custom vector implementations.

## Core Components

### BacktestEngine (Abstract Base Class)
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import pandas as pd
from datetime import datetime

class BacktestEngine(ABC):
    """Abstract base class for backtesting engines."""
    
    @abstractmethod
    def run(self, strategy: Any, data: pd.DataFrame, config: 'BacktestConfig') -> 'BacktestResult':
        """Run backtest with given strategy, data, and configuration."""
        pass
    
    @abstractmethod
    def get_results(self) -> Optional['BacktestResult']:
        """Get results of the last backtest."""
        pass
    
    @abstractmethod
    def get_equity_curve(self) -> Optional[pd.Series]:
        """Get equity curve from the last backtest."""
        pass
```

### BacktestConfig (Dataclass)
```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class BacktestConfig:
    """Configuration for backtesting parameters."""
    initial_cash: float = 100000.0
    commission_rate: float = 0.001
    slippage_model: str = 'fixed'  # 'fixed', 'volume_impact', 'bid_ask_spread'
    slippage_rate: float = 0.0001
    latency_model: str = 'fixed'   # 'fixed', 'uniform', 'normal'
    latency_ms: float = 10.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    data_frequency: str = '1d'     # '1m', '5m', '1h', '1d'
    additional_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}
```

### BacktestResult (Dataclass)
```python
@dataclass
class BacktestResult:
    """Results from a backtest run."""
    equity_curve: pd.Series
    trade_log: pd.DataFrame
    summary_stats: Dict[str, float]
    metrics: 'MetricsResult'
    execution_time: float
    config: BacktestConfig
    
    def __post_init__(self):
        """Validate result structure."""
        if not isinstance(self.equity_curve, pd.Series):
            raise ValueError("equity_curve must be a pandas Series")
        if not isinstance(self.trade_log, pd.DataFrame):
            raise ValueError("trade_log must be a pandas DataFrame")
```

### MetricsResult (Dataclass)
```python
@dataclass
class MetricsResult:
    """Performance metrics from backtest."""
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_duration: float
    additional_metrics: Dict[str, float]
    
    def __post_init__(self):
        if self.additional_metrics is None:
            self.additional_metrics = {}
```

## Error Handling

### Configuration Errors
- `ValueError` for invalid configuration parameters
- `TypeError` for wrong data types
- `ConfigurationError` for logical inconsistencies (e.g., start_date > end_date)

### Data Errors
- `DataValidationError` for invalid or missing data
- `InsufficientDataError` for insufficient historical data
- `DataFrequencyError` for inconsistent data frequency

### Execution Errors
- `BacktestExecutionError` for runtime errors during backtesting
- `StrategyError` for strategy-specific errors
- `MarketFrictionError` for market friction simulation errors

## Interface Requirements

### Strategy Interface
```python
class Strategy(ABC):
    """Interface for trading strategies."""
    
    @abstractmethod
    def init(self):
        """Initialize strategy."""
        pass
    
    @abstractmethod
    def next(self, bar: Dict[str, Any]) -> Optional[str]:
        """Process next bar and return signal: 'buy', 'sell', or None."""
        pass
```

### Data Requirements
- Input data must be pandas DataFrame with OHLCV columns
- Datetime index required for time series operations
- Data must be sorted chronologically
- Missing data handling must be specified

### Performance Requirements
- Support for large datasets (>1M bars)
- Memory-efficient processing for vector operations
- Execution time < 1 second for 100K bars with simple strategies
- Thread-safe for parallel backtesting

## Implementation Notes

### Backtesting.py Integration
- Wrapper class `BacktestingPyEngine` inherits from `BacktestEngine`
- Convert BacktestConfig to Backtesting.py parameters
- Handle Backtesting.py-specific result format conversion
- Support for Backtesting.py optimization features

### Custom Vector Implementation
- Vectorized operations using NumPy/Pandas
- Signal-based strategy support
- Position tracking using cumulative operations
- Trade log generation from position changes

### Validation
- Configuration validation before execution
- Data integrity checks
- Performance metrics validation
- Error reporting with detailed context

## Dependencies
- pandas >= 2.0.0
- numpy >= 1.24.0
- python >= 3.9
- typing_extensions (for dataclass validation)
