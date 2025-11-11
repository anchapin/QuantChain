"""Chart Reader Agent module.

Provides minimal implementations for classes used in the test suite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Any

import numpy as np

# Module flag used by test setup to control pandas availability
_PANDAS_AVAILABLE = False

# Optional pandas import - will be mocked in tests
try:
    import pandas as pd

    _PANDAS_AVAILABLE = True
except ImportError:
    pd = None

# Optional matplotlib imports - will be mocked in tests
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

try:
    import mplfinance as mpf
except ImportError:
    mpf = None

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
    divergence: Optional[str] = None
    timestamp: Optional[datetime] = None
    symbol: Optional[str] = None
    timeframe: Optional[str] = None


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
        values: List[Optional[float]] = []
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
        values: List[Optional[float]] = []
        k = 2 / (period + 1)
        ema = None
        for i, price in enumerate(closes):
            if i + 1 < period:
                values.append(None)
            elif i + 1 == period:
                ema = sum(closes[:period]) / period
                values.append(ema)
            else:
                if ema is not None:
                    ema = price * k + ema * (1 - k)
                else:
                    ema = price
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

    def analyze_chart(
        self,
        chart_image: ChartImage,
        ohlcv: OHLCVData,
        indicators: List[TechnicalIndicator],
    ) -> "PatternAnalysis":
        """Analyze chart with vision model."""
        try:
            response = self.llm_provider.generate_vision(chart_image.image_data)
            # Parse response for patterns
            patterns = self._parse_patterns_from_response(response.text)

            # Create a simple analysis
            return PatternAnalysis(
                symbol=chart_image.symbol,
                timeframe=chart_image.timeframe,
                timestamp=chart_image.timestamp,
                patterns=patterns,
                overall_sentiment=(
                    "bullish"
                    if "bullish" in response.text.lower()
                    else "bearish" if "bearish" in response.text.lower() else "neutral"
                ),
                confluence_score=70.0,
                recommended_action=(
                    "BUY"
                    if "bullish" in response.text.lower()
                    else "SELL" if "bearish" in response.text.lower() else "HOLD"
                ),
                entry_price=ohlcv.closes[-1] if ohlcv.closes else None,
                stop_loss=None,
                take_profit=[],
                reasoning=response.text,
                confidence=80.0,
            )
        except Exception as e:
            # Fallback analysis without vision model
            return PatternAnalysis(
                symbol=chart_image.symbol,
                timeframe=chart_image.timeframe,
                timestamp=chart_image.timestamp,
                patterns=[],
                overall_sentiment="neutral",
                confluence_score=30.0,
                recommended_action="HOLD",
                entry_price=ohlcv.closes[-1] if ohlcv.closes else None,
                stop_loss=None,
                take_profit=[],
                reasoning=f"Analysis completed without visual data due to error: {str(e)}",
                confidence=40.0,
            )

    def _parse_patterns_from_response(self, response_text: str) -> List["PatternData"]:
        """Parse patterns from model response."""
        patterns = []
        text_lower = response_text.lower()

        # Simple pattern detection based on keywords
        pattern_keywords = {
            "head_and_shoulders": ["head and shoulders", "head_and_shoulders"],
            "ascending_triangle": ["ascending triangle", "triangle"],
            "descending_triangle": ["descending triangle"],
            "double_top": ["double top"],
            "double_bottom": ["double bottom"],
            "flag": ["flag", "flag pattern"],
            "pennant": ["pennant"],
        }

        for pattern_type, keywords in pattern_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    patterns.append(
                        PatternData(
                            pattern_type=pattern_type,
                            confidence=75.0,
                            completion_percentage=60.0,
                            description=f"Detected {pattern_type} pattern",
                        )
                    )
                    break

        return patterns


# ---------- Chart Renderer ----------


class ChartRenderer:
    """Placeholder renderer; not used in tests."""

    def __init__(self, config: ChartReaderAgentConfig):
        self.config = config

    def render(self, ohlcv: OHLCVData, indicators: List[TechnicalIndicator]) -> bytes:
        return b""

    def render_candlestick_chart(
        self, ohlcv: OHLCVData, indicators: List[TechnicalIndicator], timeframe: str
    ) -> ChartImage:
        """Render a candlestick chart with indicators."""
        # In a real implementation, this would use matplotlib/mplfinance
        # For tests, we just return a mock chart image
        return ChartImage(
            image_data=b"mock_candlestick_chart",
            symbol=ohlcv.symbol,
            timeframe=timeframe,
            timestamp=datetime.now(),
            indicators_applied=[ind.name for ind in indicators],
            metadata={
                "indicators_count": len(indicators),
                "data_points": len(ohlcv.closes),
                "candle_count": len(ohlcv.closes),
            },
        )


# ---------- Chart Reader Agent ----------


class ChartReaderAgent:
    """Placeholder agent; not used in tests."""

    def __init__(
        self,
        config: ChartReaderAgentConfig,
        data_connector: Any = None,
        llm_provider: Any = None,
    ):
        self.config = config
        self.data_connector = data_connector
        self.llm_provider = llm_provider
        self.pattern_recognizer = (
            PatternRecognizer(config, llm_provider) if llm_provider else None
        )
        self.chart_renderer = ChartRenderer(config)

    def analyze_symbol(self, symbol: str, timeframes: List[str]) -> dict:
        """Analyze a symbol across multiple timeframes."""
        results = {}

        for timeframe in timeframes:
            try:
                # Get OHLCV data
                if self.data_connector:
                    bars = self.data_connector.get_bars(symbol, timeframe)
                    if not bars:
                        results[timeframe] = PatternAnalysis(
                            symbol=symbol,
                            timeframe=timeframe,
                            timestamp=datetime.now(),
                            patterns=[],
                            overall_sentiment="neutral",
                            confluence_score=0.0,
                            recommended_action="HOLD",
                            entry_price=None,
                            stop_loss=None,
                            take_profit=[],
                            reasoning="No data available",
                            confidence=0.0,
                        )
                        continue

                    # Convert bars to OHLCVData
                    ohlcv = OHLCVData(
                        symbol=symbol,
                        timestamps=[bar["timestamp"] for bar in bars],
                        opens=[bar["open"] for bar in bars],
                        highs=[bar["high"] for bar in bars],
                        lows=[bar["low"] for bar in bars],
                        closes=[bar["close"] for bar in bars],
                        volumes=[bar["volume"] for bar in bars],
                    )
                else:
                    # Mock data when no connector provided
                    results[timeframe] = PatternAnalysis(
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=datetime.now(),
                        patterns=[],
                        overall_sentiment="neutral",
                        confluence_score=50.0,
                        recommended_action="HOLD",
                        entry_price=100.0,
                        stop_loss=None,
                        take_profit=[],
                        reasoning="No data connector provided",
                        confidence=50.0,
                    )
                    continue

                # Perform analysis
                if self.pattern_recognizer:
                    # Create chart image
                    chart_image = ChartImage(
                        image_data=b"mock_image",
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=datetime.now(),
                    )

                    # Calculate technical indicators
                    indicators = [
                        TechnicalIndicatorCalculator.calculate_sma(ohlcv, 10),
                        TechnicalIndicatorCalculator.calculate_rsi(ohlcv, 14),
                    ]

                    # Analyze chart
                    analysis = self.pattern_recognizer.analyze_chart(
                        chart_image, ohlcv, indicators
                    )
                    results[timeframe] = analysis
                else:
                    # Simple analysis without pattern recognition
                    results[timeframe] = PatternAnalysis(
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=datetime.now(),
                        patterns=[],
                        overall_sentiment="neutral",
                        confluence_score=50.0,
                        recommended_action="HOLD",
                        entry_price=ohlcv.closes[-1] if ohlcv.closes else None,
                        stop_loss=None,
                        take_profit=[],
                        reasoning="Basic analysis without pattern recognition",
                        confidence=50.0,
                    )

            except Exception as e:
                results[timeframe] = PatternAnalysis(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=datetime.now(),
                    patterns=[],
                    overall_sentiment="neutral",
                    confluence_score=0.0,
                    recommended_action="HOLD",
                    entry_price=None,
                    stop_loss=None,
                    take_profit=[],
                    reasoning=f"Analysis failed: {str(e)}",
                    confidence=0.0,
                )

        return results

    def generate_trading_recommendation(self, symbol: str) -> dict:
        """Generate trading recommendation based on analyses."""
        analyses = self.analyze_symbol(symbol, self.config.timeframes)

        if not analyses:
            return {
                "symbol": symbol,
                "action": "HOLD",
                "confidence": 0.0,
                "reasoning": "No data available",
                "timeframe_analyses": {},
            }

        # Analyze sentiments across timeframes
        buy_signals = sum(1 for a in analyses.values() if a.recommended_action == "BUY")
        sell_signals = sum(
            1 for a in analyses.values() if a.recommended_action == "SELL"
        )
        hold_signals = sum(
            1 for a in analyses.values() if a.recommended_action == "HOLD"
        )

        # Determine overall action
        if buy_signals > sell_signals and buy_signals > hold_signals:
            action = "BUY"
        elif sell_signals > buy_signals and sell_signals > hold_signals:
            action = "SELL"
        else:
            action = "HOLD"

        # Calculate average confidence
        avg_confidence = sum(a.confidence for a in analyses.values()) / len(analyses)

        # Generate reasoning
        reasoning_parts = []
        for tf, analysis in analyses.items():
            reasoning_parts.append(
                f"{tf}: {analysis.overall_sentiment} ({analysis.confidence:.1f}% confidence)"
            )

        return {
            "symbol": symbol,
            "action": action,
            "confidence": avg_confidence,
            "reasoning": f"Analysis across {len(analyses)} timeframes. {'; '.join(reasoning_parts)}",
            "timeframe_analyses": analyses,
        }


# ---------- Pattern Data ----------


@dataclass
class PatternData:
    """Represents a detected pattern."""

    pattern_type: str
    confidence: float
    completion_percentage: float
    description: str


# ---------- Pattern Analysis ----------


@dataclass
class PatternAnalysis:
    """Represents a pattern analysis result."""

    symbol: str
    timeframe: str
    timestamp: datetime
    patterns: List[PatternData]
    overall_sentiment: str
    confluence_score: float
    recommended_action: str
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: List[float]
    reasoning: str
    confidence: float
    resistance: Optional[float] = None
    support: Optional[float] = None


# End of module
