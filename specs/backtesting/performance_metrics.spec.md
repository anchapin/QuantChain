# Performance Metrics Specification

## Overview
Defines comprehensive performance metrics calculation for backtesting using QuantStats and Empyrical libraries.

## Core Components

### PerformanceMetrics
```python
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from dataclasses import dataclass

class PerformanceMetrics:
    """Calculate comprehensive performance metrics for backtest results."""
    
    def __init__(self, benchmark_returns: Optional[pd.Series] = None,
                 risk_free_rate: float = 0.02):
        """Initialize with optional benchmark and risk-free rate."""
        self.benchmark_returns = benchmark_returns
        self.risk_free_rate = risk_free_rate
    
    def calculate_returns(self, equity_curve: pd.Series, 
                         frequency: str = '1d') -> pd.Series:
        """Calculate returns from equity curve."""
        pass
    
    def calculate_sharpe_ratio(self, returns: pd.Series, 
                               frequency: str = '1d') -> float:
        """Calculate Sharpe ratio with annualization."""
        pass
    
    def calculate_sortino_ratio(self, returns: pd.Series, 
                                frequency: str = '1d') -> float:
        """Calculate Sortino ratio (downside deviation)."""
        pass
    
    def calculate_max_drawdown(self, equity_curve: pd.Series) -> Dict[str, Any]:
        """Calculate maximum drawdown and duration."""
        pass
    
    def calculate_calmar_ratio(self, returns: pd.Series, 
                              max_drawdown: float) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)."""
        pass
    
    def calculate_win_rate(self, trades: pd.DataFrame) -> float:
        """Calculate win rate from trade log."""
        pass
    
    def calculate_profit_factor(self, trades: pd.DataFrame) -> float:
        """Calculate profit factor (gross profit / gross loss)."""
        pass
    
    def generate_tear_sheet(self, results: 'BacktestResult', 
                           save_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive QuantStats tear sheet."""
        pass
    
    def calculate_all_metrics(self, equity_curve: pd.Series, 
                             trades: pd.DataFrame,
                             frequency: str = '1d') -> 'MetricsResult':
        """Calculate all metrics and return MetricsResult."""
        pass
```

### MetricsResult (Dataclass)
```python
@dataclass
class MetricsResult:
    """Complete performance metrics result."""
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    max_drawdown_start: pd.Timestamp
    max_drawdown_end: pd.Timestamp
    volatility: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    best_trade: float
    worst_trade: float
    avg_trade_duration: float
    avg_trade_duration_days: float
    sharpe_ratio_qstats: float
    sortino_ratio_qstats: float
    omega_ratio: float
    alpha: float
    beta: float
    information_ratio: float
    var_95: float
    cvar_95: float
    skewness: float
    kurtosis: float
    additional_metrics: Dict[str, float]
    
    def __post_init__(self):
        """Initialize additional metrics if needed."""
        if self.additional_metrics is None:
            self.additional_metrics = {}
```

## Return Calculations

### Basic Returns
```python
def calculate_returns(self, equity_curve: pd.Series, frequency: str = '1d') -> pd.Series:
    """
    Calculate returns from equity curve.
    
    Args:
        equity_curve: Portfolio value over time
        frequency: Data frequency ('1m', '5m', '1h', '1d')
    
    Returns:
        pd.Series: Returns series with same index as equity_curve
    
    Raises:
        ValueError: If equity_curve is empty or has insufficient data
    """
    if len(equity_curve) < 2:
        raise ValueError("Equity curve must have at least 2 points")
    
    returns = equity_curve.pct_change().dropna()
    
    # Handle frequency-based annualization
    if frequency == '1m':
        annualization_factor = 525600  # minutes in year
    elif frequency == '5m':
        annualization_factor = 105120  # 5-minute periods in year
    elif frequency == '1h':
        annualization_factor = 8760    # hours in year
    elif frequency == '1d':
        annualization_factor = 252     # trading days in year
    else:
        raise ValueError(f"Unsupported frequency: {frequency}")
    
    return returns
```

### Total and Annualized Returns
```python
def calculate_total_return(self, equity_curve: pd.Series) -> float:
    """Calculate total return over the entire period."""
    if len(equity_curve) < 2:
        return 0.0
    return (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1

def calculate_annualized_return(self, returns: pd.Series, 
                               frequency: str = '1d') -> float:
    """Calculate annualized return."""
    if len(returns) == 0:
        return 0.0
    
    total_return = (1 + returns).prod() - 1
    
    # Calculate time period in years
    time_period = (returns.index[-1] - returns.index[0]).days / 365.25
    
    if time_period == 0:
        return 0.0
    
    return (1 + total_return) ** (1 / time_period) - 1
```

## Risk Metrics

### Sharpe Ratio
```python
def calculate_sharpe_ratio(self, returns: pd.Series, frequency: str = '1d') -> float:
    """
    Calculate Sharpe ratio: (return - risk_free_rate) / volatility
    
    Args:
        returns: Returns series
        frequency: Data frequency for annualization
    
    Returns:
        float: Sharpe ratio
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    
    # Annualization factor
    freq_map = {'1m': 525600, '5m': 105120, '1h': 8760, '1d': 252}
    annual_factor = freq_map.get(frequency, 252)
    
    # Annualized return and volatility
    annual_return = returns.mean() * annual_factor
    annual_volatility = returns.std() * np.sqrt(annual_factor)
    
    if annual_volatility == 0:
        return 0.0
    
    # Risk-free rate is already annual
    excess_return = annual_return - self.risk_free_rate
    return excess_return / annual_volatility
```

### Sortino Ratio
```python
def calculate_sortino_ratio(self, returns: pd.Series, frequency: str = '1d') -> float:
    """
    Calculate Sortino ratio using downside deviation.
    
    Args:
        returns: Returns series
        frequency: Data frequency for annualization
    
    Returns:
        float: Sortino ratio
    """
    if len(returns) == 0:
        return 0.0
    
    # Annualization factor
    freq_map = {'1m': 525600, '5m': 105120, '1h': 8760, '1d': 252}
    annual_factor = freq_map.get(frequency, 252)
    
    # Annualized return
    annual_return = returns.mean() * annual_factor
    
    # Downside deviation (only negative returns)
    downside_returns = returns[returns < 0]
    if len(downside_returns) == 0:
        return float('inf') if annual_return > self.risk_free_rate else 0.0
    
    downside_volatility = downside_returns.std() * np.sqrt(annual_factor)
    
    if downside_volatility == 0:
        return 0.0
    
    excess_return = annual_return - self.risk_free_rate
    return excess_return / downside_volatility
```

### Maximum Drawdown
```python
def calculate_max_drawdown(self, equity_curve: pd.Series) -> Dict[str, Any]:
    """
    Calculate maximum drawdown and related metrics.
    
    Args:
        equity_curve: Portfolio value over time
    
    Returns:
        Dict with max_drawdown, duration, start_date, end_date
    """
    if len(equity_curve) < 2:
        return {
            'max_drawdown': 0.0,
            'duration': 0,
            'start_date': None,
            'end_date': None
        }
    
    # Calculate running maximum
    running_max = equity_curve.expanding().max()
    
    # Calculate drawdown
    drawdown = (equity_curve - running_max) / running_max
    max_dd = drawdown.min()
    
    # Find drawdown periods
    drawdown_periods = []
    in_drawdown = False
    start_idx = None
    
    for i, dd in enumerate(drawdown):
        if dd < -0.001 and not in_drawdown:  # Start of drawdown
            in_drawdown = True
            start_idx = i
        elif dd >= -0.001 and in_drawdown:  # End of drawdown
            in_drawdown = False
            end_idx = i
            duration = end_idx - start_idx
            drawdown_periods.append((start_idx, end_idx, duration))
    
    # Handle ongoing drawdown
    if in_drawdown:
        end_idx = len(drawdown) - 1
        duration = end_idx - start_idx
        drawdown_periods.append((start_idx, end_idx, duration))
    
    # Find max duration
    max_duration = max([d[2] for d in drawdown_periods]) if drawdown_periods else 0
    
    # Find dates for max drawdown
    max_dd_idx = drawdown.idxmin()
    if max_dd_idx in drawdown.index:
        max_dd_start_date = None
        for start_idx, end_idx, _ in drawdown_periods:
            if start_idx <= max_dd_idx <= end_idx:
                max_dd_start_date = equity_curve.index[start_idx]
                max_dd_end_date = equity_curve.index[end_idx]
                break
    else:
        max_dd_start_date = None
        max_dd_end_date = None
    
    return {
        'max_drawdown': abs(max_dd),
        'max_drawdown_duration': max_duration,
        'max_drawdown_start': max_dd_start_date,
        'max_drawdown_end': max_dd_end_date
    }
```

## Trade-Based Metrics

### Win Rate
```python
def calculate_win_rate(self, trades: pd.DataFrame) -> float:
    """
    Calculate win rate from trade log.
    
    Args:
        trades: Trade log with columns including 'pnl'
    
    Returns:
        float: Win rate (0.0 to 1.0)
    """
    if len(trades) == 0 or 'pnl' not in trades.columns:
        return 0.0
    
    winning_trades = trades[trades['pnl'] > 0]
    return len(winning_trades) / len(trades)
```

### Profit Factor
```python
def calculate_profit_factor(self, trades: pd.DataFrame) -> float:
    """
    Calculate profit factor: gross profit / gross loss.
    
    Args:
        trades: Trade log with columns including 'pnl'
    
    Returns:
        float: Profit factor
    """
    if len(trades) == 0 or 'pnl' not in trades.columns:
        return 0.0
    
    gross_profit = trades[trades['pnl'] > 0]['pnl'].sum()
    gross_loss = abs(trades[trades['pnl'] < 0]['pnl'].sum())
    
    return gross_profit / gross_loss if gross_loss > 0 else float('inf')
```

## QuantStats Integration

### Tear Sheet Generation
```python
def generate_tear_sheet(self, results: 'BacktestResult', 
                       save_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate comprehensive QuantStats tear sheet.
    
    Args:
        results: BacktestResult object
        save_path: Optional path to save HTML tear sheet
    
    Returns:
        Dict: QuantStats metrics and analysis
    """
    try:
        import quantstats as qs
    except ImportError:
        raise ImportError("QuantStats is required for tear sheet generation")
    
    returns = self.calculate_returns(results.equity_curve)
    
    # Generate basic stats
    stats = qs.reports.metrics(returns, mode='basic')
    
    # Generate HTML report if save path provided
    if save_path:
        qs.reports.html(returns, output=save_path, title='Backtest Analysis')
    
    # Generate full stats if benchmark available
    if self.benchmark_returns is not None:
        full_stats = qs.reports.metrics(returns, mode='full', 
                                       benchmark=self.benchmark_returns)
        return {'basic_stats': stats, 'full_stats': full_stats}
    
    return {'basic_stats': stats}
```

## Empyrical Integration

### Risk Metrics
```python
def calculate_empyrical_metrics(self, returns: pd.Series) -> Dict[str, float]:
    """
    Calculate Empyrical risk metrics.
    
    Args:
        returns: Returns series
    
    Returns:
        Dict: Empyrical metrics
    """
    try:
        import empyrical
    except ImportError:
        raise ImportError("Empyrical is required for advanced risk metrics")
    
    metrics = {}
    
    # Alpha and Beta (if benchmark available)
    if self.benchmark_returns is not None:
        metrics['alpha'] = empyrical.alpha(returns, self.benchmark_returns)
        metrics['beta'] = empyrical.beta(returns, self.benchmark_returns)
        metrics['information_ratio'] = empyrical.information_ratio(
            returns, self.benchmark_returns)
    
    # Value at Risk
    metrics['var_95'] = empyrical.value_at_risk(returns, 0.05)
    metrics['cvar_95'] = empyrical.conditional_value_at_risk(returns, 0.05)
    
    # Other risk metrics
    metrics['omega_ratio'] = empyrical.omega_ratio(returns)
    metrics['skewness'] = empyrical.stats.skew(returns)
    metrics['kurtosis'] = empyrical.stats.kurtosis(returns)
    
    return metrics
```

## Error Handling

### Data Validation
- `InsufficientDataError` for insufficient data points
- `InvalidFrequencyError` for unsupported data frequencies
- `MissingColumnError` for required trade log columns

### Calculation Errors
- `MetricsCalculationError` for general calculation failures
- `DivisionByZeroError` for denominator zero cases
- `LibraryImportError` for missing QuantStats/Empyrical

## Performance Requirements

- Calculate basic metrics in < 10ms for 10K returns
- Generate tear sheet in < 1 second for 10K returns
- Memory usage < 50MB for 1M returns
- Support for parallel metric calculation

## Dependencies
- quantstats >= 0.0.62
- empyrical-reloaded >= 0.5.7
- numpy >= 1.24.0
- pandas >= 2.0.0
- scipy >= 1.10.0
