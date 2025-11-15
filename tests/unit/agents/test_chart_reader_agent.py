"""Tests for the Chart Reader Agent."""

from datetime import datetime, timedelta
from typing import Generator, List
from unittest.mock import Mock, patch
import numpy as np
import pytest
from quantchain.agents.chart_reader_agent import (
    ChartImage,
    ChartReaderAgent,
    ChartReaderAgentConfig,
    ChartRenderer,
    OHLCVData,
    PatternAnalysis,
    PatternRecognizer,
    TechnicalIndicator,
    TechnicalIndicatorCalculator,
)
from quantchain.core.config import QuantChainConfig


class TestChartReaderAgentConfig:
    """Test the ChartReaderAgentConfig."""

    def test_config_initialization(self):
        """Test configuration initialization."""
        config = ChartReaderAgentConfig(
            model_name="gpt-4-vision-preview",
            max_tokens=1000,
            temperature=0.7
        )
        assert config.model_name == "gpt-4-vision-preview"
        assert config.max_tokens == 1000
        assert config.temperature == 0.7


class TestOHLCVData:
    """Test the OHLCVData class."""

    def test_ohlcv_data_creation(self):
        """Test creation of OHLCV data."""
        from datetime import datetime
        timestamps = [datetime(2023, 1, 1), datetime(2023, 1, 2)]
        # Create 30 data points to match test expectations
        num_points = 30
        opens = [100.0 + i * 0.1 for i in range(num_points)]
        highs = [105.0 + i * 0.1 for i in range(num_points)]
        lows = [95.0 + i * 0.1 for i in range(num_points)]
        closes = [102.0 + i * 0.1 for i in range(num_points)]
        volumes = [1000 + i * 10 for i in range(num_points)]
        # Create corresponding timestamps
        from datetime import datetime, timedelta
        timestamps = [
            datetime(2023, 1, 1) + timedelta(hours=i) for i in range(num_points)
        ]

        ohlcv = OHLCVData(
            timestamps=timestamps,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes
        )

        assert ohlcv.timestamps == timestamps
        assert ohlcv.opens == opens
        assert ohlcv.highs == highs
        assert ohlcv.lows == lows
        assert ohlcv.closes == closes
        assert ohlcv.volumes == volumes


class TestTechnicalIndicator:
    """Test the TechnicalIndicator class."""

    def test_indicator_creation(self):
        """Test creation of technical indicator."""
        indicator = TechnicalIndicator(
            name="SMA",
            params={"period": 20},
            values=[100.0, 101.0, 102.0]
        )
        assert indicator.name == "SMA"
        assert indicator.params == {"period": 20}
        assert indicator.values == [100.0, 101.0, 102.0]


class TestTechnicalIndicatorCalculator:
    """Test the TechnicalIndicatorCalculator class."""

    @pytest.fixture
    def sample_ohlcv_data(self):
        """Create sample OHLCV data for testing."""
        timestamps = [
            datetime(2023, 1, 1) + timedelta(days=i)
            for i in range(30)
        ]
        opens = [100.0 + i * 0.1 for i in range(30)]
        highs = [105.0 + i * 0.1 for i in range(30)]
        lows = [95.0 + i * 0.1 for i in range(30)]
        closes = [102.0 + i * 0.1 for i in range(30)]
        volumes = [1000 + i * 10 for i in range(30)]

        return OHLCVData(
            timestamps=timestamps,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes
        )

    def test_calculate_sma(self, sample_ohlcv_data):
        """Test SMA calculation."""
        calculator = TechnicalIndicatorCalculator()
        indicator = calculator.calculate_sma(sample_ohlcv_data, period=10)

        assert indicator.name == "SMA"
        assert indicator.params["period"] == 10
        assert len(indicator.values) == 30  # Same length as input data
        assert indicator.values[8] is None  # First period-1 values should be None
        assert indicator.values[9] is not None  # First SMA value should be calculated

    def test_calculate_ema(self, sample_ohlcv_data):
        """Test EMA calculation."""
        calculator = TechnicalIndicatorCalculator()
        indicator = calculator.calculate_ema(sample_ohlcv_data, period=10)

        assert indicator.name == "EMA"
        assert indicator.params["period"] == 10
        assert len(indicator.values) == 30

    def test_calculate_rsi(self, sample_ohlcv_data):
        """Test RSI calculation."""
        calculator = TechnicalIndicatorCalculator()
        indicator = calculator.calculate_rsi(sample_ohlcv_data, period=14)

        assert indicator.name == "RSI"
        assert indicator.params["period"] == 14
        assert len(indicator.values) == 30
        assert all(0 <= value <= 100 for value in indicator.values[14:])


class TestPatternAnalysis:
    """Test the PatternAnalysis class."""

    def test_pattern_analysis_creation(self):
        """Test creation of pattern analysis."""
        analysis = PatternAnalysis(
            symbol="TEST",
            timeframe="1h",
            patterns=["Head and Shoulders"],
            confidence=85,
            overall_sentiment="bearish",
            recommended_action="SELL"
        )

        assert analysis.symbol == "TEST"
        assert analysis.timeframe == "1h"
        assert analysis.patterns == ["Head and Shoulders"]
        assert analysis.confidence == 85
        assert analysis.overall_sentiment == "bearish"
        assert analysis.recommended_action == "SELL"


class TestChartImage:
    """Test the ChartImage class."""

    def test_chart_image_creation(self):
        """Test creation of chart image."""
        image_data = b"fake_image_data"
        chart_image = ChartImage(
            symbol="TEST",
            timeframe="1h",
            image_data=image_data,
            indicators_applied=["SMA", "RSI"]
        )

        assert chart_image.symbol == "TEST"
        assert chart_image.timeframe == "1h"
        assert chart_image.image_data == image_data
        assert chart_image.indicators_applied == ["SMA", "RSI"]


class TestChartRenderer:
    """Test the ChartRenderer class."""

    @pytest.fixture
    def sample_ohlcv_data(self):
        """Create sample OHLCV data for testing."""
        timestamps = [
            datetime(2023, 1, 1) + timedelta(days=i)
            for i in range(30)
        ]
        opens = [100.0 + i * 0.1 for i in range(30)]
        highs = [105.0 + i * 0.1 for i in range(30)]
        lows = [95.0 + i * 0.1 for i in range(30)]
        closes = [102.0 + i * 0.1 for i in range(30)]
        volumes = [1000 + i * 10 for i in range(30)]

        return OHLCVData(
            timestamps=timestamps,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes
        )

    def test_render_candlestick_chart(self, sample_ohlcv_data):
        """Test rendering candlestick chart."""
        renderer = ChartRenderer()
        chart_image = renderer.render_candlestick_chart(
            symbol="TEST",
            timeframe="1h",
            ohlcv_data=sample_ohlcv_data,
            indicators=[TechnicalIndicator("SMA", {"period": 20}, [101.0] * 30)]
        )

        assert isinstance(chart_image, ChartImage)
        assert chart_image.symbol == "TEST"
        assert chart_image.timeframe == "1h"
        assert chart_image.indicators_applied == ["SMA(20)"]
        assert isinstance(chart_image.image_data, bytes)


class TestPatternRecognizer:
    """Test the PatternRecognizer class."""

    @pytest.fixture
    def sample_chart_image(self):
        """Create a sample chart image for testing."""
        return ChartImage(
            symbol="TEST",
            timeframe="1h",
            image_data=b"fake_image_data",
            indicators_applied=["SMA"]
        )

    @pytest.fixture
    def sample_ohlcv_data(self):
        """Create sample OHLCV data for testing."""
        timestamps = [
            datetime(2023, 1, 1) + timedelta(days=i)
            for i in range(30)
        ]
        opens = [100.0 + i * 0.1 for i in range(30)]
        highs = [105.0 + i * 0.1 for i in range(30)]
        lows = [95.0 + i * 0.1 for i in range(30)]
        closes = [102.0 + i * 0.1 for i in range(30)]
        volumes = [1000 + i * 10 for i in range(30)]

        return OHLCVData(
            timestamps=timestamps,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes
        )

    @pytest.fixture
    def sample_indicators(self):
        """Create sample indicators for testing."""
        return [
            TechnicalIndicator("SMA", {"period": 20}, [101.0] * 30),
            TechnicalIndicator("RSI", {"period": 14}, [50.0] * 30)
        ]

    @patch("quantchain.agents.chart_reader_agent.PatternRecognizer._call_vision_api")
    def test_analyze_chart_with_vision_model(
        self, mock_vision_api, sample_chart_image, sample_ohlcv_data, sample_indicators
    ):
        """Test chart analysis with vision model."""
        # Mock the vision API response
        mock_vision_api.return_value = {
            "patterns": ["Double Top"],
            "sentiment": "bearish",
            "confidence": 75,
            "recommended_action": "SELL"
        }

        pattern_recognizer = PatternRecognizer()
        analysis = pattern_recognizer.analyze_chart(
            sample_chart_image, sample_ohlcv_data, sample_indicators
        )

        assert isinstance(analysis, PatternAnalysis)
        assert analysis.symbol == "TEST"
        assert analysis.timeframe == "1h"
        assert analysis.overall_sentiment in ["bullish", "bearish", "neutral"]
        assert analysis.recommended_action in ["BUY", "SELL", "HOLD"]
        assert 0 <= analysis.confidence <= 100


class TestChartReaderAgent:
    """Test the ChartReaderAgent class."""

    @pytest.fixture
    def agent_config(self):
        """Create a sample agent configuration."""
        return ChartReaderAgentConfig(
            model_name="gpt-4-vision-preview",
            max_tokens=1000,
            temperature=0.7
        )

    @pytest.fixture
    def chart_reader_agent(self, agent_config):
        """Create a ChartReaderAgent instance for testing."""
        return ChartReaderAgent(config=agent_config)

    @pytest.fixture
    def sample_symbol_data(self):
        """Create sample symbol data for testing."""
        timestamps = [
            datetime(2023, 1, 1) + timedelta(hours=i)
            for i in range(24)
        ]
        opens = [100.0 + i * 0.1 for i in range(24)]
        highs = [105.0 + i * 0.1 for i in range(24)]
        lows = [95.0 + i * 0.1 for i in range(24)]
        closes = [102.0 + i * 0.1 for i in range(24)]
        volumes = [1000 + i * 10 for i in range(24)]

        return {
            "timestamps": timestamps,
            "opens": opens,
            "highs": highs,
            "lows": lows,
            "closes": closes,
            "volumes": volumes
        }

    @patch("quantchain.agents.chart_reader_agent.ChartReaderAgent._get_historical_data")
    @patch("quantchain.agents.chart_reader_agent.ChartReaderAgent._analyze_chart")
    def test_analyze_symbol(
        self, mock_analyze_chart, mock_get_data, chart_reader_agent, sample_symbol_data
    ):
        """Test symbol analysis."""
        # Mock the data retrieval
        mock_ohlcv = OHLCVData(**sample_symbol_data)
        mock_get_data.return_value = mock_ohlcv

        # Mock the analysis
        mock_analysis = PatternAnalysis(
            symbol="TEST",
            timeframe="1h",
            patterns=["Ascending Triangle"],
            confidence=80,
            overall_sentiment="bullish",
            recommended_action="BUY"
        )
        mock_analyze_chart.return_value = mock_analysis

        # Call the method
        analysis = chart_reader_agent.analyze_symbol(
            symbol="TEST",
            timeframe="1h",
            indicators=["SMA", "RSI"]
        )

        # Assertions
        assert isinstance(analysis, PatternAnalysis)
        assert analysis.symbol == "TEST"
        assert analysis.timeframe == "1h"
        assert analysis.overall_sentiment in ["bullish", "bearish", "neutral"]
        assert analysis.recommended_action in ["BUY", "SELL", "HOLD"]
        assert 0 <= analysis.confidence <= 100
