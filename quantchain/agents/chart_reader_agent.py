"""Chart Reader Agent module.

Provides minimal implementations for classes used in the test suite.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Any

import numpy as np

# Module flag used by test setup to control pandas availability
_PANDAS_AVAILABLE = False

# ---------- Data structures ----------

@dataclass
class OHLCVData:
    """Container for OHLCV data."""
    symbol: str
    timestamps: List[datetime]
    opens: List[float]
    highs: List[float]
    lows: List[float]
    closes: List[float]
    volumes: List[float]

# ---------- Config ----------

@dataclass
class ChartReaderAgentConfig:
    """Configuration for the Chart Reader Agent."""
    timeframes: List[str] = field(default_factory=lambda: ["15m", "1h", "4h", "1d"])
    patterns_enabled: List[str] = field(default_factory=lambda: ["head_and_shoulders"])
    indicators_enabled: List[str] = field(default_factory=lambda: ["SMA"])
    min_pattern_confidence: float = 70.0
    min_confluence_score: float = 60.0
    max_position_size: float = 0.05

# ---------- Image ----------

@dataclass
class ChartImage:
    """Represents a chart image and its metadata."""
    image_data: bytes
    symbol: str
    timeframe: str
    timestamp: datetime
    indicators_applied: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

# ---------- Technical Indicator ----------

@dataclass
class TechnicalIndicator:
    """Result of a technical indicator calculation."""
    name: str
    parameters: dict
    values: List[Optional[float]]
    signal: str

# ---------- Indicator Calculator ----------

class TechnicalIndicatorCalculator:
    """Utility class to calculate technical indicators."""
    @staticmethod
    def _determine_signal(values: List[Optional[float]], name: str) -> str:
        # Simple logic: compare last two non-None values
        recent = [v for v in values if v is not None]
        if len(recent) < 2:
            return "NEUTRAL"
        if name == "RSI":
            last = recent[-1]
            if last > 70:
                return "OVERBOUGHT"
            if last < 30:
                return "OVERSOLD"
            return "NEUTRAL"
        # Default SMA/EMA
        if recent[-1] > recent[-2]:
            return "BULLISH"
        if recent[-1] < recent[-2]:
            return "BEARISH"
        return "NEUTRAL"

    @staticmethod
    def calculate_sma(ohlcv: OHLCVData, period: int) -> TechnicalIndicator:
        closes = ohlcv.closes
        values = []
        for i in range(len(closes)):
            if i + 1 < period:
                values.append(None)
            else:
                avg = sum(closes[i + 1 - period : i + 1]) / period
                values.append(avg)
        signal = TechnicalIndicatorCalculator._determine_signal(values, "SMA")
        return TechnicalIndicator(
            name="SMA",
            parameters={"period": period},
            values=values,
            signal=signal,
        )

    @staticmethod
    def calculate_ema(ohlcv: OHLCVData, period: int) -> TechnicalIndicator:
        closes = ohlcv.closes
        values = []
        k = 2 / (period + 1)
        ema = None
        for i, price in enumerate(closes):
            if i + 1 < period:
                values.append(None)
            elif i + 1 == period:
                ema = sum(closes[:period]) / period
                values.append(ema)
            else:
                ema = price * k + ema * (1 - k)
                values.append(ema)
        signal = TechnicalIndicatorCalculator._determine_signal(values, "EMA")
        return TechnicalIndicator(
            name="EMA",
            parameters={"period": period},
            values=values,
            signal=signal,
        )

    @staticmethod
    def calculate_rsi(ohlcv: OHLCVData, period: int) -> TechnicalIndicator:
        closes = ohlcv.closes
        deltas = np.diff(closes)
        seed = deltas[:period]
        up = seed[seed > 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(closes, dtype=float)
        rsi[:period] = np.nan
        rsi[period] = 100 - (100 / (1 + rs))
        for i in range(period + 1, len(closes)):
            delta = deltas[i - 1]
            if delta > 0:
                upval = delta
                downval = 0
            else:
                upval = 0
                downval = -delta
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up / down if down != 0 else 0
            rsi[i] = 100 - (100 / (1 + rs))
        values = [float(v) if not np.isnan(v) else None for v in rsi]
        signal = TechnicalIndicatorCalculator._determine_signal(values, "RSI")
        return TechnicalIndicator(
            name="RSI",
            parameters={"period": period},
            values=values,
            signal=signal,
        )

# ---------- Pattern Recognizer ----------

class PatternRecognizer:
    """Simplified pattern recognizer used only for initialization in tests."""
    def __init__(self, config: ChartReaderAgentConfig, llm_provider: Any):
        self.config = config
        self.llm_provider = llm_provider

# ---------- Chart Renderer ----------

class ChartRenderer:
    """Placeholder renderer; not used in tests."""
    def render(self, ohlcv: OHLCVData, indicators: List[TechnicalIndicator]) -> bytes:
        return b""

# ---------- Chart Reader Agent ----------

class ChartReaderAgent:
    """Placeholder agent; not used in tests."""
    def __init__(self, config: ChartReaderAgentConfig):
        self.config = config

# ---------- Pattern Analysis ----------

@dataclass
class PatternAnalysis:
    """Represents a pattern analysis result."""
    pattern_name: str
    confidence: float
    completion_percentage: float
    sentiment: str
    action: str
    resistance: Optional[float] = None
    support: Optional[float] = None

# End of module
