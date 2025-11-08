"""Tests for the Chart Reader Agent."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import numpy as np

from quantchain.agents.chart_reader_agent import (
    ChartReaderAgent,
    ChartReaderAgentConfig,
    ChartRenderer,
    PatternRecognizer,
    TechnicalIndicatorCalculator,
    OHLCVData,
    ChartImage,
    TechnicalIndicator,
    PatternAnalysis,
)
from quantchain.core.config import QuantChainConfig


class TestChartReaderAgentConfig:
    """Test the ChartReaderAgentConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ChartReaderAgentConfig()

        assert config.timeframes == ["15m", "1h", "4h", "1d"]
        assert "head_and_shoulders" in config.patterns_enabled
        assert "SMA" in config.indicators_enabled
        assert config.min_pattern_confidence == 70.0
        assert config.min_confluence_score == 60.0
        assert config.max_position_size == 0.05


class TestTechnicalIndicatorCalculator:
    """Test the TechnicalIndicatorCalculator."""

    @pytest.fixture
    def sample_ohlcv(self):
        """Create sample OHLCV data."""
        num_points = 50
        base_price = 100
        returns = np.random.normal(0, 0.02, num_points)
        prices = [base_price]

        for ret in returns:
            prices.append(prices[-1] * (1 + ret))

        # Create OHLC from close prices
        ohlcv_data = {
            "timestamps": [
                datetime.now() - timedelta(hours=i) for i in range(num_points)
            ][::-1],
            "opens": [
                prices[i] * (1 + np.random.normal(0, 0.001)) for i in range(num_points)
            ],
            "closes": prices[:num_points],
            "highs": [
                prices[i] * (1 + abs(np.random.normal(0, 0.005)))
                for i in range(num_points)
            ],
            "lows": [
                prices[i] * (1 - abs(np.random.normal(0, 0.005)))
                for i in range(num_points)
            ],
            "volumes": [np.random.uniform(1000, 10000) for _ in range(num_points)],
        }

        return OHLCVData(symbol="TEST", **ohlcv_data)

    def test_calculate_sma(self, sample_ohlcv):
        """Test SMA calculation."""
        indicator = TechnicalIndicatorCalculator.calculate_sma(sample_ohlcv, period=10)

        assert indicator.name == "SMA"
        assert indicator.parameters["period"] == 10
        assert len(indicator.values) == len(sample_ohlcv.closes)
        assert indicator.signal in ["BULLISH", "BEARISH", "NEUTRAL"]

        # First 9 values should be NaN
        assert all(v is None or np.isnan(v) for v in indicator.values[:9])

        # Later values should be valid
        assert any(v is not None and not np.isnan(v) for v in indicator.values[10:])

    def test_calculate_ema(self, sample_ohlcv):
        """Test EMA calculation."""
        indicator = TechnicalIndicatorCalculator.calculate_ema(sample_ohlcv, period=10)

        assert indicator.name == "EMA"
        assert indicator.parameters["period"] == 10
        assert len(indicator.values) == len(sample_ohlcv.closes)
        assert indicator.signal in ["BULLISH", "BEARISH", "NEUTRAL"]

    def test_calculate_rsi(self, sample_ohlcv):
        """Test RSI calculation."""
        indicator = TechnicalIndicatorCalculator.calculate_rsi(sample_ohlcv, period=14)

        assert indicator.name == "RSI"
        assert indicator.parameters["period"] == 14
        assert indicator.signal in ["OVERBOUGHT", "OVERSOLD", "NEUTRAL"]

        # RSI should be between 0 and 100
        valid_values = [v for v in indicator.values if v is not None and not np.isnan(v)]
        # Some values might be NaN during warmup period
        if valid_values:
            assert all(0 <= v <= 100 for v in valid_values)


class TestPatternRecognizer:
    """Test the PatternRecognizer."""

    @pytest.fixture
    def mock_llm_provider(self):
        """Create a mock LLM provider."""
        mock_provider = Mock()
        response = Mock()
        response.text = """
        Analysis:
        - Identified ascending_triangle pattern with 80% confidence
        - Completion percentage: 60%
        - Overall sentiment: bullish
        - Recommended action: BUY
        - Key resistance at $105, support at $95
        """
        mock_provider.generate_vision.return_value = response
        return mock_provider

    @pytest.fixture
    def pattern_recognizer(self, mock_llm_provider):
        """Create a PatternRecognizer instance."""
        config = ChartReaderAgentConfig()
        return PatternRecognizer(config, mock_llm_provider)

    @pytest.fixture
    def sample_chart_image(self):
        """Create a sample chart image."""
        image_data = b"fake_image_data"
        return ChartImage(
            image_data=image_data,
            symbol="TEST",
            timeframe="1h",
            timestamp=datetime.now(),
            indicators_applied=["SMA", "RSI"],
            metadata={},
        )

    @pytest.fixture
    def sample_ohlcv(self):
        """Create sample OHLCV data."""
        return OHLCVData(
            symbol="TEST",
            timestamps=[datetime.now()],
            opens=[100],
            highs=[105],
            lows=[95],
            closes=[102],
            volumes=[1000],
        )

    @pytest.fixture
    def sample_indicators(self):
        """Create sample technical indicators."""
        return [
            TechnicalIndicator(
                name="SMA",
                values=[100],
                signal="BULLISH",
                divergence=None,
                timestamp=datetime.now(),
            ),
            TechnicalIndicator(
                name="RSI",
                values=[60],
                signal="NEUTRAL",
                divergence=None,
                timestamp=datetime.now(),
            ),
        ]

    def test_analyze_chart_with_vision_model(
        self, pattern_recognizer, sample_chart_image, sample_ohlcv, sample_indicators
    ):
        """Test chart analysis with vision model."""
        analysis = pattern_recognizer.analyze_chart(
            sample_chart_image, sample_ohlcv, sample_indicators
        )

        assert isinstance(analysis, PatternAnalysis)
        assert analysis.symbol == "TEST"
        assert analysis.timeframe == "1h"
        assert analysis.overall_sentiment in ["bullish", "bearish", "neutral"]
        assert analysis.recommended_action in ["BUY", "SELL", "HOLD"]
        assert 0 <= analysis.confidence <= 100

    def test_analyze_chart_vision_model_failure(
        self, pattern_recognizer, sample_chart_image, sample_ohlcv, sample_indicators
    ):
        """Test chart analysis when vision model fails."""
        pattern_recognizer.llm_provider.generate_vision.side_effect = Exception(
            "Vision model failed"
        )

        analysis = pattern_recognizer.analyze_chart(
            sample_chart_image, sample_ohlcv, sample_indicators
        )

        assert isinstance(analysis, PatternAnalysis)
        assert "fallback" in analysis.reasoning.lower() or "without visual" in analysis.reasoning.lower()

    def test_parse_patterns_from_response(self, pattern_recognizer):
        """Test pattern parsing from model response."""
        response_text = """
        The chart shows a head_and_shoulders pattern forming.
        There is also an ascending_triangle visible.
        Overall sentiment is bullish.
        """

        patterns = pattern_recognizer._parse_patterns_from_response(response_text)

        assert len(patterns) >= 2
        pattern_types = [p.pattern_type for p in patterns]
        assert "head_and_shoulders" in pattern_types
        assert "triangle" in pattern_types or "ascending_triangle" in pattern_types


class TestChartRenderer:
    """Test the ChartRenderer."""

    @pytest.fixture
    def renderer(self):
        """Create a ChartRenderer instance."""
        config = ChartReaderAgentConfig()
        return ChartRenderer(config)

    @pytest.fixture
    def sample_ohlcv(self):
        """Create sample OHLCV data for rendering."""
        num_points = 100
        base_price = 100
        closes = [base_price + np.random.normal(0, 2) for _ in range(num_points)]

        return OHLCVData(
            symbol="TEST",
            timestamps=[datetime.now() - timedelta(hours=i) for i in range(num_points)][
                ::-1
            ],
            opens=[c * 0.99 for c in closes],
            highs=[c * 1.02 for c in closes],
            lows=[c * 0.98 for c in closes],
            closes=closes,
            volumes=[np.random.uniform(1000, 10000) for _ in range(num_points)],
        )

    @pytest.fixture
    def sample_indicators(self):
        """Create sample technical indicators."""
        num_points = 100

        return [
            TechnicalIndicator(
                name="SMA",
                values=[100 + i * 0.1 for i in range(num_points)],
                signal="BULLISH",
                divergence=None,
                timestamp=datetime.now(),
            )
        ]

    @patch("quantchain.agents.chart_reader_agent.mpf")
    @patch("quantchain.agents.chart_reader_agent.plt")
    def test_render_candlestick_chart(
        self, mock_plt, mock_mpf, renderer, sample_ohlcv, sample_indicators
    ):
        """Test chart rendering."""
        # Mock the plot function
        mock_fig = Mock()
        mock_axes = [Mock(), Mock()]
        mock_mpf.plot.return_value = (mock_fig, mock_axes)

        # Create a mock buffer
        mock_buf = Mock()
        mock_buf.getvalue.return_value = b"fake_png_data"
        mock_plt.savefig.side_effect = lambda *args, **kwargs: None
        mock_plt.BytesIO.return_value = mock_buf

        chart_image = renderer.render_candlestick_chart(
            sample_ohlcv, sample_indicators, "1h"
        )

        assert isinstance(chart_image, ChartImage)
        assert chart_image.symbol == "TEST"
        assert chart_image.timeframe == "1h"
        assert chart_image.indicators_applied == ["SMA"]
        assert isinstance(chart_image.image_data, bytes)
        assert "candle_count" in chart_image.metadata


class TestChartReaderAgent:
    """Test the ChartReaderAgent."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock QuantChainConfig."""
        config = Mock(spec=QuantChainConfig)
        config.agent_type = "chart_reader"
        config.llm_provider = "anthropic"
        config.llm_model = "claude-3-5-20241022"
        config.temperature = 0.7
        config.max_tokens = 4096
        config.enable_rag = True
        config.enable_reflection = True
        config.vector_store_path = "/tmp/test_vector_store"
        config.db_path = "test_db.json"
        config.vision_provider = "gpt-4-vision-preview"
        config.max_retries = 3
        config.retry_delay = 1
        
        # Add get method for config
        def get_side_effect(key, default=None):
            if key == "rag":
                return {
                    "enabled": config.enable_rag,
                    "persist_directory": config.vector_store_path,
                    "embedding_model": "all-MiniLM-L6-v2"
                }
            elif key == "agent_type":
                return config.agent_type
            elif key == "llm_provider":
                return config.llm_provider
            elif key == "llm_model":
                return config.llm_model
            elif key == "temperature":
                return config.temperature
            elif key == "max_tokens":
                return config.max_tokens
            elif key == "enable_reflection":
                return config.enable_reflection
            return default
        
        config.get = Mock(side_effect=get_side_effect)
        return config

    @pytest.fixture
    def mock_data_connector(self):
        """Create a mock data connector."""
        connector = Mock()
        # Mock OHLCV data response
        bars = []
        for i in range(100):
            bars.append(
                {
                    "timestamp": datetime.now() - timedelta(hours=i),
                    "open": 100,
                    "high": 105,
                    "low": 95,
                    "close": 102,
                    "volume": 1000,
                }
            )
        connector.get_bars.return_value = bars
        return connector

    @pytest.fixture
    def mock_llm_provider(self):
        """Create a mock LLM provider."""
        mock_provider = Mock()
        response = Mock()
        response.text = "Chart analysis complete"
        mock_provider.generate_vision.return_value = response
        return mock_provider

    @patch("quantchain.core.rag_system.ChromaVectorStore")
    @pytest.fixture
    def agent(self, mock_config, mock_data_connector, mock_llm_provider):
        """Create a ChartReaderAgent instance."""
        return ChartReaderAgent(mock_config, mock_data_connector, mock_llm_provider)

    def test_analyze_symbol_success(self, agent, mock_data_connector):
        """Test successful symbol analysis."""
        results = agent.analyze_symbol("TEST", timeframes=["1h"])

        assert "1h" in results
        analysis = results["1h"]
        assert isinstance(analysis, PatternAnalysis)
        assert analysis.symbol == "TEST"

    def test_analyze_symbol_no_data(self, agent, mock_data_connector):
        """Test symbol analysis when no data is available."""
        mock_data_connector.get_bars.return_value = None

        results = agent.analyze_symbol("TEST", timeframes=["1h"])

        assert "1h" in results
        analysis = results["1h"]
        assert analysis.recommended_action == "HOLD"
        assert "No data available" in analysis.reasoning

    def test_analyze_symbol_with_error(self, agent, mock_data_connector):
        """Test symbol analysis when an error occurs."""
        mock_data_connector.get_bars.side_effect = Exception("Data fetch failed")

        results = agent.analyze_symbol("TEST", timeframes=["1h"])

        assert "1h" in results
        analysis = results["1h"]
        assert analysis.confidence == 0.0
        assert "Analysis failed" in analysis.reasoning

    def test_generate_trading_recommendation(self, agent):
        """Test trading recommendation generation."""
        with patch.object(agent, "analyze_symbol") as mock_analyze:
            # Mock analysis results
            mock_analyses = {
                "1h": PatternAnalysis(
                    symbol="TEST",
                    timeframe="1h",
                    timestamp=datetime.now(),
                    patterns=[],
                    overall_sentiment="bullish",
                    confluence_score=80.0,
                    recommended_action="BUY",
                    entry_price=100,
                    stop_loss=95,
                    take_profit=[110, 120],
                    reasoning="Strong bullish signals",
                    confidence=85.0,
                ),
                "4h": PatternAnalysis(
                    symbol="TEST",
                    timeframe="4h",
                    timestamp=datetime.now(),
                    patterns=[],
                    overall_sentiment="neutral",
                    confluence_score=50.0,
                    recommended_action="HOLD",
                    entry_price=100,
                    stop_loss=None,
                    take_profit=[],
                    reasoning="Mixed signals",
                    confidence=60.0,
                ),
            }
            mock_analyze.return_value = mock_analyses

            recommendation = agent.generate_trading_recommendation("TEST")

            assert recommendation["symbol"] == "TEST"
            assert recommendation["action"] in ["BUY", "SELL", "HOLD"]
            assert "confidence" in recommendation
            assert "reasoning" in recommendation
            assert "timeframe_analyses" in recommendation

    def test_generate_trading_recommendation_no_analyses(self, agent):
        """Test recommendation when no analyses are available."""
        with patch.object(agent, "analyze_symbol") as mock_analyze:
            mock_analyze.return_value = {}

            recommendation = agent.generate_trading_recommendation("TEST")

            assert recommendation["action"] == "HOLD"
            assert recommendation["confidence"] == 0.0
            assert "No data available" in recommendation["reasoning"]
