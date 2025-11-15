"""Chart Reader Agent for analyzing financial charts and patterns."""

import os
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np

try:
    import pandas as pd
    _PANDAS_AVAILABLE = True
except ImportError:
    _PANDAS_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False

try:
    import mplfinance as mpf
    _MPF_AVAILABLE = True
except ImportError:
    _MPF_AVAILABLE = False


class TimeFrame(Enum):
    """Supported timeframes for chart analysis."""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"

    @classmethod
    def from_string(cls, timeframe_str: str) -> "TimeFrame":
        """Create a TimeFrame from a string."""
        for tf in cls:
            if tf.value == timeframe_str:
                return tf
        raise ValueError(f"Unknown timeframe: {timeframe_str}")


class ChartReaderAgentConfig:
    """Configuration for the ChartReaderAgent."""

    def __init__(
        self,
        model_name: str = "gpt-4-vision-preview",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        supported_timeframes: Optional[List[str]] = None,
        enabled_patterns: Optional[List[str]] = None,
        enabled_indicators: Optional[List[str]] = None,
    ):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.supported_timeframes = supported_timeframes or [tf.value for tf in TimeFrame]
        self.enabled_patterns = enabled_patterns or [
            "head_and_shoulders", "double_top", "double_bottom",
            "triangle", "wedge", "flag"
        ]
        self.enabled_indicators = enabled_indicators or [
            "SMA", "EMA", "RSI", "MACD", "BB"
        ]


class OHLCVData:
    """Data structure for OHLCV price data."""

    def __init__(
        self,
        timestamps: List[datetime],
        opens: List[float],
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
        symbol: Optional[str] = None,
    ):
        if not (len(timestamps) == len(opens) == len(highs) == len(lows) == len(closes) == len(volumes)):
            raise ValueError("All data arrays must have the same length")

        self.timestamps = timestamps
        self.opens = opens
        self.highs = highs
        self.lows = lows
        self.closes = closes
        self.volumes = volumes
        self.symbol = symbol

    def to_dataframe(self) -> Optional["pd.DataFrame"]:
        """Convert to pandas DataFrame if pandas is available."""
        if not _PANDAS_AVAILABLE:
            return None

        return pd.DataFrame({
            'timestamp': self.timestamps,
            'open': self.opens,
            'high': self.highs,
            'low': self.lows,
            'close': self.closes,
            'volume': self.volumes
        })


class TechnicalIndicator:
    """Represents a technical indicator with its values and parameters."""

    def __init__(
        self,
        name: str,
        params: Dict[str, Any],
        values: List[float],
        signal: Optional[str] = None,
    ):
        self.name = name
        self.params = params
        self.values = values
        self.signal = signal


class TechnicalIndicatorCalculator:
    """Calculates technical indicators for OHLCV data."""

    @staticmethod
    def calculate_sma(ohlcv: OHLCVData, period: int = 20) -> TechnicalIndicator:
        """Calculate Simple Moving Average (SMA)."""
        closes = np.array(ohlcv.closes)
        sma_values = []

        for i in range(len(closes)):
            if i < period - 1:
                sma_values.append(None)
            else:
                window = closes[i-period+1:i+1]
                sma_values.append(float(np.mean(window)))

        return TechnicalIndicator(
            name="SMA",
            params={"period": period},
            values=sma_values,
            signal=None
        )

    @staticmethod
    def calculate_ema(ohlcv: OHLCVData, period: int = 20) -> TechnicalIndicator:
        """Calculate Exponential Moving Average (EMA)."""
        closes = np.array(ohlcv.closes)
        ema_values = []

        # First EMA value is the SMA
        if len(closes) >= period:
            first_ema = np.mean(closes[:period])
            ema_values = [None] * (period - 1) + [first_ema]

            # Calculate subsequent EMA values
            multiplier = 2 / (period + 1)
            for i in range(period, len(closes)):
                ema = closes[i] * multiplier + ema_values[-1] * (1 - multiplier)
                ema_values.append(float(ema))
        else:
            ema_values = [None] * len(closes)

        return TechnicalIndicator(
            name="EMA",
            params={"period": period},
            values=ema_values,
            signal=None
        )

    @staticmethod
    def calculate_rsi(ohlcv: OHLCVData, period: int = 14) -> TechnicalIndicator:
        """Calculate Relative Strength Index (RSI)."""
        closes = np.array(ohlcv.closes)
        deltas = np.diff(closes)

        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        # Initialize arrays with None values
        avg_gain = [None] * len(closes)
        avg_loss = [None] * len(closes)
        rsi_values = [None] * len(closes)

        for i in range(len(closes)):
            if i < period:
                # Not enough data points yet
                continue
            elif i == period:
                # First RSI value uses simple average
                avg_gain[i] = np.mean(gains[:period])
                avg_loss[i] = np.mean(losses[:period])
            else:
                # Subsequent values use Wilder's smoothing
                prev_avg_gain = avg_gain[i-1]
                prev_avg_loss = avg_loss[i-1]

                # gains[i-1] because gains array is one shorter than closes
                current_gain = gains[i-1] if i-1 < len(gains) else 0
                current_loss = losses[i-1] if i-1 < len(losses) else 0

                avg_gain[i] = (prev_avg_gain * (period - 1) + current_gain) / period
                avg_loss[i] = (prev_avg_loss * (period - 1) + current_loss) / period

            # Calculate RSI
            if avg_gain[i] is not None and avg_loss[i] is not None:
                if avg_loss[i] == 0:
                    rs = float('inf')
                else:
                    rs = avg_gain[i] / avg_loss[i]

                rsi = 100 - (100 / (1 + rs))
                rsi_values[i] = rsi

        return TechnicalIndicator(
            name="RSI",
            params={"period": period},
            values=rsi_values,
            signal=None
        )


class PatternAnalysis:
    """Result of pattern analysis on chart data."""

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        patterns: List[str],
        confidence: float,
        overall_sentiment: str,
        recommended_action: str,
        reasoning: str = "",
        confluence_score: float = 0.0,
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[List[float]] = None,
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.patterns = patterns
        self.confidence = confidence
        self.overall_sentiment = overall_sentiment
        self.recommended_action = recommended_action
        self.reasoning = reasoning
        self.confluence_score = confluence_score
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit or []


class ChartImage:
    """Represents a rendered chart image."""

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        image_data: bytes,
        indicators_applied: List[str],
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.image_data = image_data
        self.indicators_applied = indicators_applied
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}


class ChartRenderer:
    """Renders charts from OHLCV data."""

    def __init__(self, config: Optional[ChartReaderAgentConfig] = None):
        self.config = config or ChartReaderAgentConfig()

    def render_candlestick_chart(
        self,
        symbol: str,
        timeframe: str,
        ohlcv_data: OHLCVData,
        indicators: Optional[List[TechnicalIndicator]] = None,
    ) -> ChartImage:
        """Render a candlestick chart with optional indicators."""
        if not _MATPLOTLIB_AVAILABLE or not _MPF_AVAILABLE:
            raise ImportError("matplotlib and mplfinance are required for chart rendering")

        df = ohlcv_data.to_dataframe()
        if df is None:
            raise ImportError("pandas is required for chart rendering")

        # Convert DataFrame for mplfinance
        df.index = pd.to_datetime(df['timestamp'])
        df = df[['open', 'high', 'low', 'close', 'volume']]

        # Prepare plots for indicators
        additional_plots = []
        indicators_applied = []

        if indicators:
            for indicator in indicators:
                if indicator.name == "SMA" or indicator.name == "EMA":
                    df[indicator.name] = indicator.values
                    additional_plots.append(
                        mpf.make_addplot(df[indicator.name], type='line', color='orange')
                    )
                    indicators_applied.append(f"{indicator.name}({indicator.params.get('period', '?')})")

                elif indicator.name == "RSI":
                    # Create a separate panel for RSI
                    rsi_df = pd.DataFrame({'RSI': indicator.values})
                    rsi_df.index = pd.to_datetime(ohlcv_data.timestamps)

                    additional_plots.append(
                        mpf.make_addplot(rsi_df['RSI'], panel=1, color='purple')
                    )
                    indicators_applied.append(f"RSI({indicator.params.get('period', '?')})")

        # Create the plot
        fig, axes = mpf.plot(
            df,
            type='candle',
            style='yahoo',
            title=f"{symbol} - {timeframe}",
            ylabel='Price',
            volume=True,
            addplot=additional_plots,
            figsize=(12, 8),
            returnfig=True
        )

        # Convert to bytes
        from io import BytesIO
        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        image_data = buffer.read()
        buffer.close()

        return ChartImage(
            symbol=symbol,
            timeframe=timeframe,
            image_data=image_data,
            indicators_applied=indicators_applied
        )


class PatternRecognizer:
    """Recognizes patterns in chart data."""

    def __init__(
        self,
        config: Optional[ChartReaderAgentConfig] = None,
        llm_provider: Optional[Any] = None
    ):
        self.config = config or ChartReaderAgentConfig()
        self.llm_provider = llm_provider

    def _call_vision_api(self, chart_image: ChartImage, prompt: str) -> Dict[str, Any]:
        """Call the vision API with chart image and prompt."""
        if not self.llm_provider:
            # Mock response for testing
            return {
                "patterns": ["mock_pattern"],
                "sentiment": "neutral",
                "confidence": 50,
                "recommended_action": "HOLD"
            }

        # In a real implementation, this would call the LLM vision API
        # For now, we return a mock response
        return {
            "patterns": ["mock_pattern"],
            "sentiment": "neutral",
            "confidence": 50,
            "recommended_action": "HOLD"
        }

    def analyze_chart(
        self,
        chart_image: ChartImage,
        ohlcv_data: OHLCVData,
        indicators: Optional[List[TechnicalIndicator]] = None,
    ) -> PatternAnalysis:
        """Analyze a chart for patterns."""
        # This is a simplified implementation
        # In a real scenario, this would use computer vision or LLM to analyze the chart

        # For testing purposes, we'll return a basic analysis
        patterns = []
        confidence = 50.0

        # Simple pattern detection based on indicator values
        if indicators:
            for indicator in indicators:
                if indicator.name == "RSI" and indicator.values and indicator.values[-1] is not None:
                    rsi = indicator.values[-1]
                    if rsi > 70:
                        patterns.append("RSI Overbought")
                        confidence += 10
                    elif rsi < 30:
                        patterns.append("RSI Oversold")
                        confidence += 10

                if indicator.name in ["SMA", "EMA"] and indicator.values:
                    sma = indicator.values[-1]
                    if sma is not None and len(ohlcv_data.closes) > 0:
                        close = ohlcv_data.closes[-1]
                        if close > sma:
                            patterns.append(f"Price above {indicator.name}")
                            confidence += 5

        # Determine sentiment and action
        if not patterns:
            sentiment = "neutral"
            action = "HOLD"
        elif any("Overbought" in p for p in patterns):
            sentiment = "bearish"
            action = "SELL"
        elif any("Oversold" in p for p in patterns):
            sentiment = "bullish"
            action = "BUY"
        else:
            sentiment = "neutral"
            action = "HOLD"

        # Clamp confidence between 0 and 100
        confidence = min(max(confidence, 0.0), 100.0)

        return PatternAnalysis(
            symbol=chart_image.symbol,
            timeframe=chart_image.timeframe,
            patterns=patterns,
            confidence=confidence,
            overall_sentiment=sentiment,
            recommended_action=action,
            reasoning=f"Detected patterns: {', '.join(patterns)}"
        )


class ChartReaderAgent:
    """Agent for reading and analyzing financial charts."""

    def __init__(
        self,
        config: Optional[ChartReaderAgentConfig] = None,
        data_provider: Optional[Any] = None,
        llm_provider: Optional[Any] = None,
    ):
        self.config = config or ChartReaderAgentConfig()
        self.data_provider = data_provider
        self.llm_provider = llm_provider
        self.renderer = ChartRenderer(self.config)
        self.pattern_recognizer = PatternRecognizer(self.config, self.llm_provider)

    def _get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100
    ) -> OHLCVData:
        """Get historical OHLCV data for a symbol."""
        # This is a mock implementation
        # In a real scenario, this would fetch data from an API

        # Generate some sample data
        import random
        from datetime import timedelta

        base_price = random.uniform(50, 200)
        timestamps = []
        opens = []
        highs = []
        lows = []
        closes = []
        volumes = []

        current_time = datetime.now() - timedelta(days=limit)

        for i in range(limit):
            timestamps.append(current_time)

            # Generate random OHLCV values
            open_price = base_price + random.uniform(-5, 5)
            close_change = random.uniform(-2, 2)
            close_price = open_price + close_change
            high_price = max(open_price, close_price) + random.uniform(0, 3)
            low_price = min(open_price, close_price) - random.uniform(0, 3)
            volume = random.uniform(10000, 100000)

            opens.append(open_price)
            highs.append(high_price)
            lows.append(low_price)
            closes.append(close_price)
            volumes.append(volume)

            base_price = close_price  # Next period starts at this close
            current_time += timedelta(days=1)

        return OHLCVData(
            timestamps=timestamps,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes,
            symbol=symbol
        )

    def _calculate_indicators(
        self,
        ohlcv_data: OHLCVData,
        indicator_types: Optional[List[str]] = None
    ) -> List[TechnicalIndicator]:
        """Calculate technical indicators for the OHLCV data."""
        indicators = []
        indicator_types = indicator_types or self.config.enabled_indicators

        if "SMA" in indicator_types:
            indicators.append(TechnicalIndicatorCalculator.calculate_sma(ohlcv_data))

        if "EMA" in indicator_types:
            indicators.append(TechnicalIndicatorCalculator.calculate_ema(ohlcv_data))

        if "RSI" in indicator_types:
            indicators.append(TechnicalIndicatorCalculator.calculate_rsi(ohlcv_data))

        return indicators

    def _analyze_chart(
        self,
        chart_image: ChartImage,
        ohlcv_data: OHLCVData,
        indicators: List[TechnicalIndicator],
    ) -> PatternAnalysis:
        """Analyze a chart using the pattern recognizer."""
        return self.pattern_recognizer.analyze_chart(chart_image, ohlcv_data, indicators)

    def analyze_symbol(
        self,
        symbol: str,
        timeframe: str,
        indicators: Optional[List[str]] = None,
    ) -> PatternAnalysis:
        """Analyze a symbol for trading patterns."""
        # Get historical data
        ohlcv_data = self._get_historical_data(symbol, timeframe)

        # Calculate indicators
        indicator_objects = self._calculate_indicators(ohlcv_data, indicators)

        # Render chart
        chart_image = self.renderer.render_candlestick_chart(
            symbol, timeframe, ohlcv_data, indicator_objects
        )

        # Analyze chart
        analysis = self._analyze_chart(chart_image, ohlcv_data, indicator_objects)

        return analysis
