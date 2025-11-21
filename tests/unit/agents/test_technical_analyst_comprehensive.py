"""
Comprehensive tests for TechnicalAnalyst agent to improve coverage from 21% to 85%+.
Tests all private methods and edge cases.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from datetime import datetime, timedelta

try:
    from quantchain.agents.technical_analyst import (
        TechnicalAnalystAgent,
        TechnicalIndicator,
        ChartPattern,
        TechnicalAnalysis,
        PriceData,
    )
    from quantchain.agents.base import RecommendationType
    TECHNICAL_ANALYST_AVAILABLE = True
except ImportError as e:
    TECHNICAL_ANALYST_AVAILABLE = False
    print(f"Technical analyst module not available: {e}")


@pytest.mark.skipif(not TECHNICAL_ANALYST_AVAILABLE, reason="Technical analyst not available")
@pytest.mark.unit
class TestTechnicalIndicator:
    """Test TechnicalIndicator dataclass for comprehensive coverage."""

    def test_technical_indicator_creation(self):
        """Test creating technical indicators."""
        indicator = TechnicalIndicator(
            name="RSI",
            value=65.5,
            signal="NEUTRAL",
            confidence=75.0,
            parameters={"period": 14}
        )
        assert indicator.name == "RSI"
        assert indicator.value == 65.5
        assert indicator.signal == "NEUTRAL"
        assert indicator.confidence == 75.0
        assert indicator.parameters["period"] == 14

    def test_technical_indicator_different_signals(self):
        """Test technical indicators with different signals."""
        buy_indicator = TechnicalIndicator(
            name="MACD", value=0.5, signal="BUY", confidence=80.0, parameters={}
        )
        sell_indicator = TechnicalIndicator(
            name="SMA", value=-0.3, signal="SELL", confidence=70.0, parameters={}
        )

        assert buy_indicator.signal == "BUY"
        assert sell_indicator.signal == "SELL"


@pytest.mark.skipif(not TECHNICAL_ANALYST_AVAILABLE, reason="Technical analyst not available")
@pytest.mark.unit
class TestChartPattern:
    """Test ChartPattern dataclass for comprehensive coverage."""

    def test_chart_pattern_creation(self):
        """Test creating chart patterns."""
        pattern = ChartPattern(
            pattern_type="head_and_shoulders",
            direction="bearish",
            confidence=85.0,
            completion_percentage=75.0,
            target_price=95.0,
            stop_loss=105.0,
            time_to_completion=48
        )
        assert pattern.pattern_type == "head_and_shoulders"
        assert pattern.direction == "bearish"
        assert pattern.confidence == 85.0
        assert pattern.completion_percentage == 75.0
        assert pattern.target_price == 95.0
        assert pattern.stop_loss == 105.0
        assert pattern.time_to_completion == 48

    def test_chart_pattern_optional_fields(self):
        """Test chart patterns with optional fields."""
        pattern = ChartPattern(
            pattern_type="triangle",
            direction="bullish",
            confidence=60.0,
            completion_percentage=40.0,
            target_price=None,
            stop_loss=None,
            time_to_completion=None
        )
        assert pattern.target_price is None
        assert pattern.stop_loss is None
        assert pattern.time_to_completion is None


@pytest.mark.skipif(not TECHNICAL_ANALYST_AVAILABLE, reason="Technical analyst not available")
@pytest.mark.unit
class TestTechnicalAnalysis:
    """Test TechnicalAnalysis dataclass for comprehensive coverage."""

    def test_technical_analysis_creation(self):
        """Test creating technical analysis."""
        indicator = TechnicalIndicator("RSI", 50, "NEUTRAL", 70, {})
        pattern = ChartPattern("triangle", "bullish", 60, 50, None, None, None)

        analysis = TechnicalAnalysis(
            indicators=[indicator],
            patterns=[pattern],
            overall_trend="uptrend",
            trend_strength=75.0,
            support_resistance={"support": [100, 95], "resistance": [110, 115]},
            volume_analysis={"current_volume": 1000000, "volume_ratio": 1.2},
            timeframes_analyzed=["1h", "4h"]
        )
        assert len(analysis.indicators) == 1
        assert len(analysis.patterns) == 1
        assert analysis.overall_trend == "uptrend"
        assert analysis.trend_strength == 75.0


@pytest.mark.skipif(not TECHNICAL_ANALYST_AVAILABLE, reason="Technical analyst not available")
@pytest.mark.unit
class TestPriceData:
    """Test PriceData dataclass for comprehensive coverage."""

    def test_price_data_creation(self):
        """Test creating price data."""
        timestamps = [datetime.now(), datetime.now() + timedelta(hours=1)]
        opens = [100.0, 101.0]
        highs = [102.0, 103.0]
        lows = [99.0, 100.0]
        closes = [101.0, 102.0]
        volumes = [1000000, 1100000]

        price_data = PriceData(
            symbol="AAPL",
            timestamps=timestamps,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes
        )
        assert price_data.symbol == "AAPL"
        assert len(price_data.timestamps) == 2
        assert price_data.closes == [101.0, 102.0]


@pytest.mark.skipif(not TECHNICAL_ANALYST_AVAILABLE, reason="Technical analyst not available")
@pytest.mark.unit
class TestTechnicalAnalystAgent:
    """Test TechnicalAnalystAgent for comprehensive coverage."""

    def test_agent_initialization(self):
        """Test agent initialization with default config."""
        config = {
            "technical_analyst": {
                "timeframes": ["1h", "4h"],
                "indicators": {"RSI": {"period": 14}},
                "patterns": ["head_and_shoulders"],
                "min_data_points": 100
            }
        }
        mock_llm = Mock()

        agent = TechnicalAnalystAgent(config, mock_llm)

        assert agent.role.value == "TECHNICAL"
        assert agent.timeframes == ["1h", "4h"]
        assert agent.min_data_points == 100
        assert "RSI" in agent.indicators_enabled

    def test_agent_initialization_without_config(self):
        """Test agent initialization with minimal config."""
        config = {}
        mock_llm = Mock()

        agent = TechnicalAnalystAgent(config, mock_llm)

        assert agent.timeframes == ["1h", "4h", "1d"]  # Default
        assert agent.min_data_points == 50  # Default
        assert "SMA" in agent.indicators_enabled  # Default

    def test_analyze_insufficient_data(self):
        """Test analyze with insufficient price data."""
        config = {"technical_analyst": {"min_data_points": 100}}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Mock data connector returning insufficient data
        mock_connector = Mock()
        agent.data_connector = mock_connector
        with patch.object(agent, '_get_price_data', return_value=None):
            result = agent.analyze("AAPL")

            assert result.recommendation == RecommendationType.HOLD
            assert result.confidence_score == 0.0
            assert "Insufficient price data" in result.reasoning

    def test_analyze_successful(self):
        """Test successful analysis with sufficient data."""
        config = {"technical_analyst": {"timeframes": ["1h"], "min_data_points": 50}}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Mock price data
        mock_price_data = Mock()
        mock_price_data.closes = [100.0] * 60

        with patch.object(agent, '_get_price_data', return_value=mock_price_data):
            with patch.object(agent, '_perform_technical_analysis') as mock_analysis:
                with patch.object(agent, '_synthesize_timeframe_analysis') as mock_synthesize:
                    mock_analysis.return_value = TechnicalAnalysis(
                        indicators=[], patterns=[], overall_trend="uptrend",
                        trend_strength=70.0, support_resistance={}, volume_analysis={},
                        timeframes_analyzed=["1h"]
                    )
                    mock_synthesize.return_value = (75.0, "Strong bullish signals")

                    result = agent.analyze("AAPL")

                    assert result.recommendation == RecommendationType.BUY
                    assert result.confidence_score == 75.0
                    assert "Strong bullish signals" in result.reasoning

    def test_analyze_exception_handling(self):
        """Test analyze exception handling."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        with patch.object(agent, '_get_price_data', side_effect=Exception("Data fetch error")):
            result = agent.analyze("AAPL")

            assert result.recommendation == RecommendationType.HOLD
            assert result.confidence_score == 0.0
            assert "Technical analysis failed" in result.reasoning

    def test_create_argument_no_technical_analysis(self):
        """Test create_argument without technical analysis."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        context = {"symbol": "AAPL", "technical_analysis": None}
        argument = agent.create_argument(context)

        assert argument.argument_type == "neutral"
        assert "No technical analysis available" in argument.reasoning

    def test_create_argument_bullish_signals(self):
        """Test create_argument with bullish technical signals."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Mock technical analysis
        mock_analysis = Mock()
        mock_analysis.metadata = {
            "technical_available": True,
            "overall_score": 80.0,
            "technical_analyses": {
                "1h": {"overall_trend": "uptrend", "trend_strength": 80.0, "indicators": []}
            }
        }

        context = {
            "symbol": "AAPL",
            "technical_analysis": mock_analysis
        }

        with patch.object(agent, '_analyze_trend_consistency', return_value=85.0):
            argument = agent.create_argument(context)

            assert argument.argument_type == "support"
            assert "Strong technical signals" in argument.reasoning

    def test_create_argument_bearish_signals(self):
        """Test create_argument with bearish technical signals."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Mock technical analysis
        mock_analysis = Mock()
        mock_analysis.metadata = {
            "technical_available": True,
            "overall_score": -80.0,
            "technical_analyses": {
                "1h": {"overall_trend": "downtrend", "trend_strength": 80.0, "indicators": []}
            }
        }

        context = {
            "symbol": "AAPL",
            "technical_analysis": mock_analysis
        }

        with patch.object(agent, '_analyze_trend_consistency', return_value=85.0):
            argument = agent.create_argument(context)

            assert argument.argument_type == "oppose"
            assert "Strong technical signals" in argument.reasoning

    def test_get_price_data_no_connector(self):
        """Test _get_price_data without data connector."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        result = agent._get_price_data("AAPL", "1h")

        assert result is not None
        assert result.symbol == "AAPL"
        assert isinstance(result, PriceData)

    def test_get_price_data_with_connector(self):
        """Test _get_price_data with data connector."""
        config = {}
        mock_llm = Mock()
        mock_connector = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm, mock_connector)

        with patch.object(agent, '_generate_mock_price_data') as mock_generate:
            mock_generate.return_value = Mock()

            result = agent._get_price_data("AAPL", "1h")

            mock_generate.assert_called_once_with("AAPL", "1h")

    def test_get_price_data_connector_exception(self):
        """Test _get_price_data with connector exception."""
        config = {}
        mock_llm = Mock()
        mock_connector = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm, mock_connector)

        with patch.object(agent, '_generate_mock_price_data', side_effect=Exception("API error")):
            result = agent._get_price_data("AAPL", "1h")

            assert result is None

    def test_generate_mock_price_data(self):
        """Test _generate_mock_price_data generates realistic data."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        price_data = agent._generate_mock_price_data("AAPL", "1h")

        assert price_data.symbol == "AAPL"
        assert len(price_data.closes) == 100  # Default for 1h
        assert len(price_data.opens) == len(price_data.closes)
        assert len(price_data.highs) == len(price_data.closes)
        assert len(price_data.lows) == len(price_data.closes)
        assert len(price_data.volumes) == len(price_data.closes)
        assert len(price_data.timestamps) == len(price_data.closes)

        # Check realistic price relationships
        for i in range(len(price_data.closes)):
            assert price_data.highs[i] >= price_data.closes[i]
            assert price_data.lows[i] <= price_data.closes[i]
            assert price_data.volumes[i] > 0

    def test_get_hours_per_candle(self):
        """Test _get_hours_per_candle mapping."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        assert agent._get_hours_per_candle("1m") == 0  # 1/60 truncated to int
        assert agent._get_hours_per_candle("5m") == 0  # 5/60 truncated to int
        assert agent._get_hours_per_candle("15m") == 0  # 15/60 truncated to int
        assert agent._get_hours_per_candle("30m") == 0  # 0.5 truncated to int
        assert agent._get_hours_per_candle("1h") == 1
        assert agent._get_hours_per_candle("4h") == 4
        assert agent._get_hours_per_candle("1d") == 24
        assert agent._get_hours_per_candle("1w") == 168
        assert agent._get_hours_per_candle("unknown") == 1  # Default

    def test_perform_technical_analysis(self):
        """Test _perform_technical_analysis creates complete analysis."""
        config = {"technical_analyst": {"indicators": {"SMA": {"periods": [20]}}}}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Create test price data
        price_data = PriceData(
            symbol="AAPL",
            timestamps=[datetime.now() - timedelta(hours=i) for i in range(100, 0, -1)],
            opens=[100.0] * 100,
            highs=[101.0] * 100,
            lows=[99.0] * 100,
            closes=[100.5] * 100,
            volumes=[1000000] * 100
        )

        analysis = agent._perform_technical_analysis(price_data, "1h")

        assert isinstance(analysis, TechnicalAnalysis)
        assert analysis.timeframes_analyzed == ["1h"]
        assert analysis.overall_trend in ["uptrend", "downtrend", "sideways"]
        assert 0 <= analysis.trend_strength <= 100

    def test_calculate_indicators_all_enabled(self):
        """Test _calculate_indicators with all indicators enabled."""
        config = {
            "technical_analyst": {
                "indicators": {
                    "SMA": {"periods": [20, 50]},
                    "RSI": {"period": 14},
                    "MACD": {"fast": 12, "slow": 26, "signal": 9}
                }
            }
        }
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        price_data = PriceData(
            symbol="AAPL",
            timestamps=[datetime.now() - timedelta(hours=i) for i in range(100, 0, -1)],
            opens=[100.0] * 100,
            highs=[101.0] * 100,
            lows=[99.0] * 100,
            closes=[100.5] * 100,
            volumes=[1000000] * 100
        )

        indicators = agent._calculate_indicators(price_data)

        assert len(indicators) >= 3  # At least SMA_20, SMA_50, RSI, MACD
        indicator_names = [ind.name for ind in indicators]
        assert "SMA_20" in indicator_names
        assert "SMA_50" in indicator_names
        assert "RSI" in indicator_names
        assert "MACD" in indicator_names

    def test_calculate_indicators_insufficient_data(self):
        """Test _calculate_indicators with insufficient data."""
        config = {
            "technical_analyst": {
                "indicators": {
                    "SMA": {"periods": [200]},  # Requires 200 data points
                    "RSI": {"period": 50}  # Requires 50 data points
                }
            }
        }
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Only provide 30 data points
        price_data = PriceData(
            symbol="AAPL",
            timestamps=[datetime.now() - timedelta(hours=i) for i in range(30, 0, -1)],
            opens=[100.0] * 30,
            highs=[101.0] * 30,
            lows=[99.0] * 30,
            closes=[100.5] * 30,
            volumes=[1000000] * 30
        )

        indicators = agent._calculate_indicators(price_data)

        # Should have no indicators due to insufficient data
        assert len(indicators) == 0

    def test_calculate_sma(self):
        """Test SMA calculation."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        prices = np.array([100.0, 101.0, 102.0, 103.0, 104.0])
        period = 3

        sma = agent._calculate_sma(prices, period)

        # SMA for period=3: [101.0, 102.0, 103.0]
        assert len(sma) == len(prices) - period + 1
        assert sma[0] == 101.0  # (100+101+102)/3
        assert sma[1] == 102.0  # (101+102+103)/3
        assert sma[2] == 103.0  # (102+103+104)/3

    def test_calculate_rsi(self):
        """Test RSI calculation."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Create increasing prices (should give high RSI)
        prices = np.array([100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0])
        period = 5

        rsi = agent._calculate_rsi(prices, period)

        assert len(rsi) == len(prices)
        assert 0 <= rsi[-1] <= 100

    def test_calculate_macd(self):
        """Test MACD calculation."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        prices = np.array([100.0 + i for i in range(50)])  # Trending up
        fast, slow, signal = 12, 26, 9

        macd_line, signal_line, histogram = agent._calculate_macd(prices, fast, slow, signal)

        assert len(macd_line) == len(signal_line) == len(histogram)
        # With trending up prices, MACD histogram should be positive
        assert histogram[-1] > 0

    def test_calculate_ema(self):
        """Test EMA calculation."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        prices = np.array([100.0, 101.0, 102.0, 103.0, 104.0])
        period = 3

        ema = agent._calculate_ema(prices, period)

        assert len(ema) == len(prices)
        assert ema[0] == prices[0]  # First EMA equals first price

    def test_get_ma_signal(self):
        """Test moving average signal generation."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Test BUY signal (price > MA * 1.02)
        signal = agent._get_ma_signal(110.0, 100.0)
        assert signal == "BUY"

        # Test SELL signal (price < MA * 0.98)
        signal = agent._get_ma_signal(90.0, 100.0)
        assert signal == "SELL"

        # Test NEUTRAL signal (price close to MA)
        signal = agent._get_ma_signal(101.0, 100.0)
        assert signal == "NEUTRAL"

    def test_get_rsi_signal(self):
        """Test RSI signal generation."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Test BUY signal (RSI < 30)
        signal = agent._get_rsi_signal(25.0)
        assert signal == "BUY"

        # Test SELL signal (RSI > 70)
        signal = agent._get_rsi_signal(75.0)
        assert signal == "SELL"

        # Test NEUTRAL signal (30 <= RSI <= 70)
        signal = agent._get_rsi_signal(50.0)
        assert signal == "NEUTRAL"

    def test_get_macd_signal(self):
        """Test MACD signal generation."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Test BUY signal (histogram > 0)
        signal = agent._get_macd_signal(0.5)
        assert signal == "BUY"

        # Test SELL signal (histogram < 0)
        signal = agent._get_macd_signal(-0.3)
        assert signal == "SELL"

        # Test NEUTRAL signal (histogram = 0)
        signal = agent._get_macd_signal(0.0)
        assert signal == "NEUTRAL"

    def test_detect_patterns(self):
        """Test pattern detection."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        price_data = PriceData(
            symbol="AAPL",
            timestamps=[datetime.now()],
            opens=[100.0],
            highs=[101.0],
            lows=[99.0],
            closes=[100.5],
            volumes=[1000000]
        )

        patterns = agent._detect_patterns(price_data)

        assert isinstance(patterns, list)
        # Currently returns empty list as pattern detection is not implemented

    def test_analyze_trend_uptrend(self):
        """Test trend analysis for uptrend."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Create increasing prices
        closes = np.array([100.0 + i for i in range(50)])
        price_data = PriceData(
            symbol="AAPL",
            timestamps=[datetime.now()] * 50,
            opens=[100.0] * 50,
            highs=[102.0] * 50,
            lows=[98.0] * 50,
            closes=closes,
            volumes=[1000000] * 50
        )

        trend, strength = agent._analyze_trend(price_data)

        assert trend == "uptrend"
        assert 0 <= strength <= 100

    def test_analyze_trend_downtrend(self):
        """Test trend analysis for downtrend."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Create decreasing prices
        closes = np.array([150.0 - i for i in range(50)])
        price_data = PriceData(
            symbol="AAPL",
            timestamps=[datetime.now()] * 50,
            opens=[150.0] * 50,
            highs=[152.0] * 50,
            lows=[148.0] * 50,
            closes=closes,
            volumes=[1000000] * 50
        )

        trend, strength = agent._analyze_trend(price_data)

        assert trend == "downtrend"
        assert 0 <= strength <= 100

    def test_analyze_trend_sideways(self):
        """Test trend analysis for sideways market."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Create sideways prices (small random variations)
        np.random.seed(42)
        closes = np.array([100.0 + np.random.normal(0, 0.5) for i in range(50)])
        price_data = PriceData(
            symbol="AAPL",
            timestamps=[datetime.now()] * 50,
            opens=[100.0] * 50,
            highs=[101.0] * 50,
            lows=[99.0] * 50,
            closes=closes,
            volumes=[1000000] * 50
        )

        trend, strength = agent._analyze_trend(price_data)

        assert trend in ["uptrend", "downtrend", "sideways"]
        assert 0 <= strength <= 100

    def test_find_support_resistance_with_scipy(self):
        """Test support/resistance finding with scipy."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Create price data with clear support/resistance
        highs = [100.0, 105.0, 100.0, 105.0, 100.0, 105.0, 110.0, 105.0]
        lows = [95.0, 90.0, 95.0, 90.0, 95.0, 90.0, 85.0, 90.0]

        price_data = PriceData(
            symbol="AAPL",
            timestamps=[datetime.now()] * 8,
            opens=[97.5] * 8,
            highs=highs,
            lows=lows,
            closes=[97.5] * 8,
            volumes=[1000000] * 8
        )

        # Try with scipy
        try:
            from scipy.signal import argrelextrema
            result = agent._find_support_resistance(price_data)

            assert "support" in result
            assert "resistance" in result
            assert isinstance(result["support"], list)
            assert isinstance(result["resistance"], list)
        except ImportError:
            # Fallback test
            result = agent._find_support_resistance(price_data)
            assert "support" in result
            assert "resistance" in result

    def test_find_support_resistance_fallback(self):
        """Test support/resistance finding fallback without scipy."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        price_data = PriceData(
            symbol="AAPL",
            timestamps=[datetime.now()],
            opens=[100.0],
            highs=[101.0],
            lows=[99.0],
            closes=[100.5],
            volumes=[1000000]
        )

        with patch('quantchain.agents.technical_analyst.argrelextrema', side_effect=NameError):
            result = agent._find_support_resistance(price_data)

            assert "support" in result
            assert "resistance" in result
            assert len(result["support"]) == 2
            assert len(result["resistance"]) == 2

    def test_analyze_volume(self):
        """Test volume analysis."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        volumes = [1000000, 1200000, 1500000, 800000]
        price_data = PriceData(
            symbol="AAPL",
            timestamps=[datetime.now()] * 4,
            opens=[100.0] * 4,
            highs=[101.0] * 4,
            lows=[99.0] * 4,
            closes=[100.5] * 4,
            volumes=volumes
        )

        analysis = agent._analyze_volume(price_data)

        assert "current_volume" in analysis
        assert "average_volume" in analysis
        assert "volume_ratio" in analysis
        assert "volume_trend" in analysis
        assert analysis["current_volume"] == 800000  # Last volume
        assert analysis["average_volume"] == sum(volumes) / len(volumes)

    def test_synthesize_timeframe_analysis(self):
        """Test synthesizing analysis across timeframes."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Create mock analyses for different timeframes
        indicator_buy = TechnicalIndicator("RSI", 25, "BUY", 75, {"period": 14})
        indicator_sell = TechnicalIndicator("RSI", 75, "SELL", 75, {"period": 14})

        analysis_1h = TechnicalAnalysis(
            indicators=[indicator_buy],
            patterns=[],
            overall_trend="uptrend",
            trend_strength=80.0,
            support_resistance={},
            volume_analysis={},
            timeframes_analyzed=["1h"]
        )

        analysis_4h = TechnicalAnalysis(
            indicators=[indicator_sell],
            patterns=[],
            overall_trend="downtrend",
            trend_strength=60.0,
            support_resistance={},
            volume_analysis={},
            timeframes_analyzed=["4h"]
        )

        technical_analyses = {"1h": analysis_1h, "4h": analysis_4h}

        score, reasoning = agent._synthesize_timeframe_analysis(technical_analyses, "AAPL")

        assert isinstance(score, float)
        assert isinstance(reasoning, str)
        assert "Multi-timeframe analysis" in reasoning

    def test_score_to_recommendation(self):
        """Test converting score to recommendation."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Test BUY recommendation
        rec = agent._score_to_recommendation(80.0)
        assert rec == RecommendationType.BUY

        # Test SELL recommendation
        rec = agent._score_to_recommendation(-80.0)
        assert rec == RecommendationType.SELL

        # Test HOLD recommendation (boundary cases)
        rec = agent._score_to_recommendation(50.0)
        assert rec == RecommendationType.HOLD

        rec = agent._score_to_recommendation(-50.0)
        assert rec == RecommendationType.HOLD

        rec = agent._score_to_recommendation(0.0)
        assert rec == RecommendationType.HOLD

    def test_analysis_to_dict(self):
        """Test converting TechnicalAnalysis to dictionary."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        indicator = TechnicalIndicator("RSI", 50, "NEUTRAL", 70, {"period": 14})
        pattern = ChartPattern("triangle", "bullish", 60, 50, None, None, None)

        analysis = TechnicalAnalysis(
            indicators=[indicator],
            patterns=[pattern],
            overall_trend="uptrend",
            trend_strength=75.0,
            support_resistance={"support": [100]},
            volume_analysis={"volume_ratio": 1.2},
            timeframes_analyzed=["1h"]
        )

        result = agent._analysis_to_dict(analysis)

        assert "indicators" in result
        assert "patterns" in result
        assert "overall_trend" in result
        assert "trend_strength" in result
        assert len(result["indicators"]) == 1
        assert len(result["patterns"]) == 1
        assert result["indicators"][0]["name"] == "RSI"
        assert result["patterns"][0]["pattern_type"] == "triangle"

    def test_analyze_trend_consistency(self):
        """Test analyzing trend consistency across timeframes."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        # Test with consistent trends
        analyses = {
            "1h": {"overall_trend": "uptrend"},
            "4h": {"overall_trend": "uptrend"},
            "1d": {"overall_trend": "uptrend"}
        }

        consistency = agent._analyze_trend_consistency(analyses)
        assert consistency == 100.0  # 3/3 trends agree

        # Test with mixed trends
        analyses = {
            "1h": {"overall_trend": "uptrend"},
            "4h": {"overall_trend": "downtrend"},
            "1d": {"overall_trend": "uptrend"}
        }

        consistency = agent._analyze_trend_consistency(analyses)
        assert consistency == 66.67  # 2/3 trends agree (rounded)

        # Test with empty analyses
        consistency = agent._analyze_trend_consistency({})
        assert consistency == 0.0

    def test_extract_technical_evidence(self):
        """Test extracting technical evidence from analyses."""
        config = {}
        mock_llm = Mock()
        agent = TechnicalAnalystAgent(config, mock_llm)

        analyses = {
            "1h": {
                "overall_trend": "uptrend",
                "trend_strength": 80.0,
                "indicators": [
                    {"name": "RSI", "signal": "BUY", "confidence": 75.0},
                    {"name": "MACD", "signal": "BUY", "confidence": 80.0},
                    {"name": "SMA", "signal": "NEUTRAL", "confidence": 70.0}
                ]
            },
            "4h": {
                "overall_trend": "uptrend",
                "trend_strength": 75.0,
                "indicators": [
                    {"name": "RSI", "signal": "BUY", "confidence": 70.0}
                ]
            }
        }

        evidence = agent._extract_technical_evidence(analyses, "bullish")

        assert isinstance(evidence, list)
        assert len(evidence) > 0
        # Check that evidence contains trend and indicator information
        evidence_text = " ".join(evidence)
        assert "1h: uptrend" in evidence_text
        assert "RSI" in evidence_text
        assert "MACD" in evidence_text


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])