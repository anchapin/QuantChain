"""Comprehensive tests for chart_reader_agent module."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

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
    TimeFrame,
)


class TestTimeFrame:
    """Test TimeFrame enum functionality."""

    @pytest.mark.unit
    def test_timeframe_values(self):
        """Test TimeFrame enum values."""
        assert TimeFrame.MINUTE_1.value == "1m"
        assert TimeFrame.MINUTE_5.value == "5m"
        assert TimeFrame.HOUR_1.value == "1h"
        assert TimeFrame.DAY_1.value == "1d"

    @pytest.mark.unit
    def test_from_string_valid(self):
        """Test creating TimeFrame from valid string."""
        assert TimeFrame.from_string("1m") == TimeFrame.MINUTE_1
        assert TimeFrame.from_string("1h") == TimeFrame.HOUR_1
        assert TimeFrame.from_string("1d") == TimeFrame.DAY_1

    @pytest.mark.unit
    def test_from_string_invalid(self):
        """Test TimeFrame.from_string with invalid string."""
        with pytest.raises(ValueError, match="Unknown timeframe"):
            TimeFrame.from_string("invalid")


class TestChartReaderAgentConfig:
    """Test ChartReaderAgentConfig functionality."""

    @pytest.mark.unit
    def test_default_config(self):
        """Test default configuration values."""
        config = ChartReaderAgentConfig()
        assert config.model_name == "gpt-4-vision-preview"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert len(config.enabled_patterns) > 0
        assert len(config.enabled_indicators) > 0

    @pytest.mark.unit
    def test_custom_config(self):
        """Test custom configuration values."""
        config = ChartReaderAgentConfig(
            model_name="custom-model",
            max_tokens=2048,
            temperature=0.5,
            supported_timeframes=["1m", "5m"],
            enabled_patterns=["custom_pattern"],
            enabled_indicators=["CUSTOM"],
        )
        assert config.model_name == "custom-model"
        assert config.max_tokens == 2048
        assert config.temperature == 0.5
        assert config.supported_timeframes == ["1m", "5m"]
        assert config.enabled_patterns == ["custom_pattern"]
        assert config.enabled_indicators == ["CUSTOM"]


class TestOHLCVData:
    """Test OHLCVData functionality."""

    @pytest.mark.unit
    def test_ohlcv_data_creation(self):
        """Test creating valid OHLCV data."""
        timestamps = [datetime.now(), datetime.now() + timedelta(days=1)]
        opens = [100.0, 101.0]
        highs = [102.0, 103.0]
        lows = [99.0, 100.0]
        closes = [101.0, 102.0]
        volumes = [1000, 1100]

        ohlcv = OHLCVData(timestamps, opens, highs, lows, closes, volumes, "AAPL")

        assert ohlcv.timestamps == timestamps
        assert ohlcv.opens == opens
        assert ohlcv.highs == highs
        assert ohlcv.lows == lows
        assert ohlcv.closes == closes
        assert ohlcv.volumes == volumes
        assert ohlcv.symbol == "AAPL"

    @pytest.mark.unit
    def test_ohlcv_data_length_mismatch(self):
        """Test OHLCV data creation with mismatched array lengths."""
        timestamps = [datetime.now()]
        opens = [100.0, 101.0]  # Different length
        highs = [102.0]
        lows = [99.0]
        closes = [101.0]
        volumes = [1000]

        with pytest.raises(
            ValueError, match="All data arrays must have the same length"
        ):
            OHLCVData(timestamps, opens, highs, lows, closes, volumes)

    @pytest.mark.unit
    def test_to_dataframe_with_pandas(self):
        """Test converting to DataFrame when pandas is available."""
        timestamps = [datetime.now()]
        opens = [100.0]
        highs = [102.0]
        lows = [99.0]
        closes = [101.0]
        volumes = [1000]

        ohlcv = OHLCVData(timestamps, opens, highs, lows, closes, volumes)

        # Mock pandas availability
        with patch("quantchain.agents.chart_reader_agent._PANDAS_AVAILABLE", True):
            with patch("quantchain.agents.chart_reader_agent.pd") as mock_pd:
                mock_df = Mock()
                mock_pd.DataFrame.return_value = mock_df

                result = ohlcv.to_dataframe()
                assert result == mock_df
                mock_pd.DataFrame.assert_called_once()

    @pytest.mark.unit
    def test_to_dataframe_without_pandas(self):
        """Test converting to DataFrame when pandas is not available."""
        timestamps = [datetime.now()]
        opens = [100.0]
        highs = [102.0]
        lows = [99.0]
        closes = [101.0]
        volumes = [1000]

        ohlcv = OHLCVData(timestamps, opens, highs, lows, closes, volumes)

        with patch("quantchain.agents.chart_reader_agent._PANDAS_AVAILABLE", False):
            result = ohlcv.to_dataframe()
            assert result is None


class TestTechnicalIndicator:
    """Test TechnicalIndicator functionality."""

    @pytest.mark.unit
    def test_technical_indicator_creation(self):
        """Test creating a technical indicator."""
        indicator = TechnicalIndicator(
            name="SMA",
            params={"period": 20},
            values=[100.0, 101.0, 102.0],
            signal="BUY",
        )

        assert indicator.name == "SMA"
        assert indicator.params == {"period": 20}
        assert indicator.values == [100.0, 101.0, 102.0]
        assert indicator.signal == "BUY"

    @pytest.mark.unit
    def test_technical_indicator_creation_defaults(self):
        """Test creating technical indicator with defaults."""
        indicator = TechnicalIndicator(
            name="RSI", params={"period": 14}, values=[50.0, 55.0]
        )

        assert indicator.name == "RSI"
        assert indicator.params == {"period": 14}
        assert indicator.values == [50.0, 55.0]
        assert indicator.signal is None


class TestTechnicalIndicatorCalculator:
    """Test TechnicalIndicatorCalculator functionality."""

    @pytest.fixture
    def sample_ohlcv(self):
        """Create sample OHLCV data for testing."""
        timestamps = [datetime.now() + timedelta(days=i) for i in range(30)]
        closes = [100 + i for i in range(30)]  # Simple increasing price series
        opens = [99.5 + i for i in range(30)]
        highs = [101 + i for i in range(30)]
        lows = [98.5 + i for i in range(30)]
        volumes = [1000] * 30

        return OHLCVData(timestamps, opens, highs, lows, closes, volumes)

    @pytest.mark.unit
    def test_calculate_sma(self, sample_ohlcv):
        """Test SMA calculation."""
        indicator = TechnicalIndicatorCalculator.calculate_sma(sample_ohlcv, period=10)

        assert indicator.name == "SMA"
        assert indicator.params == {"period": 10}
        assert len(indicator.values) == len(sample_ohlcv.closes)

        # First 9 values should be None (not enough data)
        for i in range(9):
            assert indicator.values[i] is None

        # 10th value should be the average of first 10 closes
        expected_sma = sum(sample_ohlcv.closes[:10]) / 10
        assert abs(indicator.values[9] - expected_sma) < 0.01

    @pytest.mark.unit
    def test_calculate_ema(self, sample_ohlcv):
        """Test EMA calculation."""
        indicator = TechnicalIndicatorCalculator.calculate_ema(sample_ohlcv, period=10)

        assert indicator.name == "EMA"
        assert indicator.params == {"period": 10}
        assert len(indicator.values) == len(sample_ohlcv.closes)

        # First 9 values should be None
        for i in range(9):
            assert indicator.values[i] is None

        # Should have valid EMA values after period
        assert indicator.values[9] is not None
        assert indicator.values[10] is not None

    @pytest.mark.unit
    def test_calculate_rsi(self, sample_ohlcv):
        """Test RSI calculation."""
        indicator = TechnicalIndicatorCalculator.calculate_rsi(sample_ohlcv, period=14)

        assert indicator.name == "RSI"
        assert indicator.params == {"period": 14}
        assert len(indicator.values) == len(sample_ohlcv.closes)

        # First values should be None
        for i in range(14):
            assert indicator.values[i] is None

        # Should have valid RSI values after period
        if indicator.values[14] is not None:
            assert 0 <= indicator.values[14] <= 100

    @pytest.mark.unit
    def test_sma_insufficient_data(self):
        """Test SMA calculation with insufficient data."""
        timestamps = [datetime.now()]
        closes = [100.0]
        opens = [99.0]
        highs = [101.0]
        lows = [98.0]
        volumes = [1000]

        ohlcv = OHLCVData(timestamps, opens, highs, lows, closes, volumes)

        indicator = TechnicalIndicatorCalculator.calculate_sma(ohlcv, period=10)
        assert indicator.values[0] is None


class TestPatternAnalysis:
    """Test PatternAnalysis functionality."""

    @pytest.mark.unit
    def test_pattern_analysis_creation(self):
        """Test creating pattern analysis."""
        analysis = PatternAnalysis(
            symbol="AAPL",
            timeframe="1d",
            patterns=["head_and_shoulders", "RSI_oversold"],
            confidence=75.5,
            overall_sentiment="bullish",
            recommended_action="BUY",
            reasoning="Head and shoulders pattern detected with RSI oversold condition",
            confluence_score=8.5,
            entry_price=150.0,
            stop_loss=145.0,
            take_profit=[160.0, 170.0],
        )

        assert analysis.symbol == "AAPL"
        assert analysis.timeframe == "1d"
        assert "head_and_shoulders" in analysis.patterns
        assert "RSI_oversold" in analysis.patterns
        assert analysis.confidence == 75.5
        assert analysis.overall_sentiment == "bullish"
        assert analysis.recommended_action == "BUY"
        assert analysis.confluence_score == 8.5
        assert analysis.entry_price == 150.0
        assert analysis.stop_loss == 145.0
        assert analysis.take_profit == [160.0, 170.0]

    @pytest.mark.unit
    def test_pattern_analysis_defaults(self):
        """Test pattern analysis with default values."""
        analysis = PatternAnalysis(
            symbol="BTC",
            timeframe="1h",
            patterns=[],
            confidence=50.0,
            overall_sentiment="neutral",
            recommended_action="HOLD",
        )

        assert analysis.symbol == "BTC"
        assert analysis.timeframe == "1h"
        assert analysis.patterns == []
        assert analysis.confidence == 50.0
        assert analysis.overall_sentiment == "neutral"
        assert analysis.recommended_action == "HOLD"
        assert analysis.confluence_score == 0.0
        assert analysis.entry_price is None
        assert analysis.stop_loss is None
        assert analysis.take_profit == []


class TestChartImage:
    """Test ChartImage functionality."""

    @pytest.mark.unit
    def test_chart_image_creation(self):
        """Test creating chart image."""
        image_data = b"fake_image_data"
        timestamp = datetime.now()
        metadata = {"resolution": "1920x1080", "format": "PNG"}

        chart_image = ChartImage(
            symbol="AAPL",
            timeframe="1d",
            image_data=image_data,
            indicators_applied=["SMA(20)", "RSI(14)"],
            timestamp=timestamp,
            metadata=metadata,
        )

        assert chart_image.symbol == "AAPL"
        assert chart_image.timeframe == "1d"
        assert chart_image.image_data == image_data
        assert chart_image.indicators_applied == ["SMA(20)", "RSI(14)"]
        assert chart_image.timestamp == timestamp
        assert chart_image.metadata == metadata

    @pytest.mark.unit
    def test_chart_image_defaults(self):
        """Test chart image with default values."""
        image_data = b"fake_image_data"

        chart_image = ChartImage(
            symbol="BTC", timeframe="1h", image_data=image_data, indicators_applied=[]
        )

        assert chart_image.symbol == "BTC"
        assert chart_image.timeframe == "1h"
        assert chart_image.image_data == image_data
        assert chart_image.indicators_applied == []
        assert chart_image.timestamp is not None  # Should default to now()
        assert chart_image.metadata == {}


class TestChartRenderer:
    """Test ChartRenderer functionality."""

    @pytest.mark.unit
    def test_chart_renderer_init(self):
        """Test chart renderer initialization."""
        config = ChartReaderAgentConfig(model_name="test-model")
        renderer = ChartRenderer(config)

        assert renderer.config == config

    @pytest.mark.unit
    def test_chart_renderer_default_config(self):
        """Test chart renderer with default config."""
        renderer = ChartRenderer()

        assert renderer.config is not None
        assert renderer.config.model_name == "gpt-4-vision-preview"

    @pytest.mark.unit
    def test_render_candlestick_chart_missing_dependencies(self):
        """Test rendering chart without required dependencies."""
        renderer = ChartRenderer()

        # Mock missing dependencies
        with patch("quantchain.agents.chart_reader_agent._MATPLOTLIB_AVAILABLE", False):
            with patch("quantchain.agents.chart_reader_agent._MPF_AVAILABLE", False):
                with pytest.raises(
                    ImportError, match="matplotlib and mplfinance are required"
                ):
                    renderer.render_candlestick_chart("AAPL", "1d", Mock())

    @pytest.mark.unit
    def test_render_candlestick_chart_missing_pandas(self):
        """Test rendering chart without pandas."""
        renderer = ChartRenderer()
        ohlcv = Mock()
        ohlcv.to_dataframe.return_value = None

        with patch("quantchain.agents.chart_reader_agent._MATPLOTLIB_AVAILABLE", True):
            with patch("quantchain.agents.chart_reader_agent._MPF_AVAILABLE", True):
                with pytest.raises(ImportError, match="pandas is required"):
                    renderer.render_candlestick_chart("AAPL", "1d", ohlcv)


class TestPatternRecognizer:
    """Test PatternRecognizer functionality."""

    @pytest.mark.unit
    def test_pattern_recognizer_init(self):
        """Test pattern recognizer initialization."""
        config = ChartReaderAgentConfig()
        llm_provider = Mock()

        recognizer = PatternRecognizer(config, llm_provider)

        assert recognizer.config == config
        assert recognizer.llm_provider == llm_provider

    @pytest.mark.unit
    def test_pattern_recognizer_defaults(self):
        """Test pattern recognizer with default values."""
        recognizer = PatternRecognizer()

        assert recognizer.config is not None
        assert recognizer.llm_provider is None

    @pytest.mark.unit
    def test_call_vision_api_without_llm(self):
        """Test vision API call without LLM provider."""
        recognizer = PatternRecognizer()
        chart_image = Mock()
        prompt = "Analyze this chart"

        result = recognizer._call_vision_api(chart_image, prompt)

        assert "patterns" in result
        assert "sentiment" in result
        assert "confidence" in result
        assert "recommended_action" in result
        assert result["sentiment"] == "neutral"

    @pytest.mark.unit
    def test_call_vision_api_with_llm(self):
        """Test vision API call with LLM provider."""
        llm_provider = Mock()
        recognizer = PatternRecognizer(llm_provider=llm_provider)

        chart_image = Mock()
        prompt = "Analyze this chart"

        result = recognizer._call_vision_api(chart_image, prompt)

        # Should return mock response even with LLM provider
        assert "patterns" in result
        assert result["sentiment"] == "neutral"

    @pytest.mark.unit
    def test_analyze_chart_basic(self):
        """Test basic chart analysis."""
        recognizer = PatternRecognizer()

        chart_image = Mock()
        chart_image.symbol = "AAPL"
        chart_image.timeframe = "1d"

        ohlcv = Mock()
        ohlcv.closes = [100, 101, 102, 103]

        # Create RSI indicator with oversold condition
        rsi_indicator = Mock()
        rsi_indicator.name = "RSI"
        rsi_indicator.values = [None] * 10 + [25.0]  # RSI oversold
        rsi_indicator.params = {"period": 14}

        result = recognizer.analyze_chart(chart_image, ohlcv, [rsi_indicator])

        assert isinstance(result, PatternAnalysis)
        assert result.symbol == "AAPL"
        assert result.timeframe == "1d"
        assert "RSI Oversold" in result.patterns
        assert result.overall_sentiment == "bullish"
        assert result.recommended_action == "BUY"

    @pytest.mark.unit
    def test_analyze_chart_overbought(self):
        """Test chart analysis with overbought condition."""
        recognizer = PatternRecognizer()

        chart_image = Mock()
        chart_image.symbol = "AAPL"
        chart_image.timeframe = "1d"

        ohlcv = Mock()
        ohlcv.closes = [100, 101, 102, 103]

        # Create RSI indicator with overbought condition
        rsi_indicator = Mock()
        rsi_indicator.name = "RSI"
        rsi_indicator.values = [None] * 10 + [75.0]  # RSI overbought
        rsi_indicator.params = {"period": 14}

        result = recognizer.analyze_chart(chart_image, ohlcv, [rsi_indicator])

        assert result.overall_sentiment == "bearish"
        assert result.recommended_action == "SELL"

    @pytest.mark.unit
    def test_analyze_chart_no_patterns(self):
        """Test chart analysis with no patterns detected."""
        recognizer = PatternRecognizer()

        chart_image = Mock()
        chart_image.symbol = "AAPL"
        chart_image.timeframe = "1d"

        ohlcv = Mock()
        ohlcv.closes = [100, 101, 102, 103]

        result = recognizer.analyze_chart(chart_image, ohlcv, [])

        assert result.overall_sentiment == "neutral"
        assert result.recommended_action == "HOLD"

    @pytest.mark.unit
    def test_analyze_chart_price_above_sma(self):
        """Test chart analysis with price above SMA."""
        recognizer = PatternRecognizer()

        chart_image = Mock()
        chart_image.symbol = "AAPL"
        chart_image.timeframe = "1d"

        ohlcv = Mock()
        ohlcv.closes = [105, 106, 107, 108]  # Price above SMA

        # Create SMA indicator
        sma_indicator = Mock()
        sma_indicator.name = "SMA"
        sma_indicator.values = [100.0]  # SMA lower than price
        sma_indicator.params = {"period": 20}

        result = recognizer.analyze_chart(chart_image, ohlcv, [sma_indicator])

        assert "Price above SMA" in result.patterns

    @pytest.mark.unit
    def test_confidence_clamping(self):
        """Test that confidence is properly clamped between 0 and 100."""
        recognizer = PatternRecognizer()

        chart_image = Mock()
        chart_image.symbol = "AAPL"
        chart_image.timeframe = "1d"

        ohlcv = Mock()
        ohlcv.closes = [100, 101, 102, 103]

        # Create multiple indicators that would increase confidence beyond 100
        indicators = []
        for i in range(20):  # Many patterns
            indicator = Mock()
            indicator.name = f"RSI{i}"
            indicator.values = [None] * 10 + [25.0]  # All oversold
            indicator.params = {"period": 14}
            indicators.append(indicator)

        result = recognizer.analyze_chart(chart_image, ohlcv, indicators)

        assert 0 <= result.confidence <= 100


class TestChartReaderAgent:
    """Test ChartReaderAgent functionality."""

    @pytest.mark.unit
    def test_agent_init(self):
        """Test agent initialization."""
        config = ChartReaderAgentConfig(model_name="test-model")
        data_provider = Mock()
        llm_provider = Mock()

        agent = ChartReaderAgent(config, data_provider, llm_provider)

        assert agent.config == config
        assert agent.data_provider == data_provider
        assert agent.llm_provider == llm_provider
        assert agent.renderer is not None
        assert agent.pattern_recognizer is not None

    @pytest.mark.unit
    def test_agent_init_defaults(self):
        """Test agent initialization with defaults."""
        agent = ChartReaderAgent()

        assert agent.config is not None
        assert agent.data_provider is None
        assert agent.llm_provider is None
        assert agent.renderer is not None
        assert agent.pattern_recognizer is not None

    @pytest.mark.unit
    def test_get_historical_data(self):
        """Test getting historical data."""
        agent = ChartReaderAgent()

        data = agent._get_historical_data("AAPL", "1d", limit=5)

        assert isinstance(data, OHLCVData)
        assert data.symbol == "AAPL"
        assert len(data.timestamps) == 5
        assert len(data.closes) == 5
        assert len(data.opens) == 5
        assert len(data.highs) == 5
        assert len(data.lows) == 5
        assert len(data.volumes) == 5

    @pytest.mark.unit
    def test_calculate_indicators(self):
        """Test calculating indicators."""
        agent = ChartReaderAgent()

        # Create sample data
        timestamps = [datetime.now() + timedelta(days=i) for i in range(30)]
        closes = [100 + i for i in range(30)]
        opens = [99.5 + i for i in range(30)]
        highs = [101 + i for i in range(30)]
        lows = [98.5 + i for i in range(30)]
        volumes = [1000] * 30

        ohlcv = OHLCVData(timestamps, opens, highs, lows, closes, volumes)

        indicators = agent._calculate_indicators(ohlcv, ["SMA", "EMA", "RSI"])

        assert len(indicators) == 3
        assert indicators[0].name == "SMA"
        assert indicators[1].name == "EMA"
        assert indicators[2].name == "RSI"

    @pytest.mark.unit
    def test_calculate_indicators_default_types(self):
        """Test calculating indicators with default types."""
        agent = ChartReaderAgent()

        # Create sample data
        timestamps = [datetime.now() + timedelta(days=i) for i in range(30)]
        closes = [100 + i for i in range(30)]
        opens = [99.5 + i for i in range(30)]
        highs = [101 + i for i in range(30)]
        lows = [98.5 + i for i in range(30)]
        volumes = [1000] * 30

        ohlcv = OHLCVData(timestamps, opens, highs, lows, closes, volumes)

        indicators = agent._calculate_indicators(ohlcv)  # Use default indicator types

        # Should include default indicators from config
        assert len(indicators) >= 3  # At least SMA, EMA, RSI

        indicator_names = [ind.name for ind in indicators]
        assert "SMA" in indicator_names
        assert "EMA" in indicator_names
        assert "RSI" in indicator_names

    @pytest.mark.unit
    def test_analyze_chart(self):
        """Test analyzing a chart."""
        agent = ChartReaderAgent()

        chart_image = Mock()
        ohlcv = Mock()
        indicators = []

        # Mock the pattern recognizer
        agent.pattern_recognizer.analyze_chart = Mock(return_value=Mock())

        result = agent._analyze_chart(chart_image, ohlcv, indicators)

        agent.pattern_recognizer.analyze_chart.assert_called_once_with(
            chart_image, ohlcv, indicators
        )

    @pytest.mark.unit
    def test_analyze_symbol(self):
        """Test analyzing a symbol end-to-end."""
        agent = ChartReaderAgent()

        # Mock dependencies to avoid complex rendering
        with patch.object(agent, "_get_historical_data") as mock_data, patch.object(
            agent, "_calculate_indicators"
        ) as mock_indicators, patch.object(
            agent.renderer, "render_candlestick_chart"
        ) as mock_render, patch.object(
            agent, "_analyze_chart"
        ) as mock_analyze:

            mock_data.return_value = Mock()
            mock_indicators.return_value = [Mock()]
            mock_render.return_value = Mock()
            mock_analyze.return_value = Mock()

            result = agent.analyze_symbol("AAPL", "1d", ["SMA"])

            # Verify all steps were called
            mock_data.assert_called_once_with("AAPL", "1d")
            mock_indicators.assert_called_once()
            mock_render.assert_called_once()
            mock_analyze.assert_called_once()
