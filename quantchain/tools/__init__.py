"""Tools and utility functions for QuantChain."""

from .trading_execution import (
    TradingExecutionInterface,
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderType,
    OrderStatus,
    TimeInForce,
    Position,
    AccountInfo,
    ExecutionError,
    ValidationError,
    InsufficientFundsError,
    OrderNotFoundError,
)

from .paper_trading import (
    PaperTradingExecutor,
    SlippageModel,
    NoSlippage,
    FixedSlippage,
    VolumeSlippage,
    RandomSlippage,
    FillModel,
    ImmediateFill,
    PerformanceMetrics,
)

from .execution_factory import create_execution_interface

__all__ = [
    "TradingExecutionInterface",
    "OrderRequest",
    "OrderResult",
    "OrderSide",
    "OrderType",
    "OrderStatus",
    "TimeInForce",
    "Position",
    "AccountInfo",
    "ExecutionError",
    "ValidationError",
    "InsufficientFundsError",
    "OrderNotFoundError",
    "PaperTradingExecutor",
    "SlippageModel",
    "NoSlippage",
    "FixedSlippage",
    "VolumeSlippage",
    "RandomSlippage",
    "FillModel",
    "ImmediateFill",
    "PerformanceMetrics",
    "create_execution_interface",
]
