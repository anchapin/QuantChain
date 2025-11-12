# Auto-generated test file for ccxt_connector.py
# Generated using Z.AI GLM-4.6 API

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the parent directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

"""Test cases for CCXT data connector."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from ccxt_connector import CCXTDataConnector
from core.exceptions import (
    AuthenticationError,
    DataSourceError,
    RateLimitError,
    SymbolNotFoundError,
)


@pytest.fixture
def mock_ccxt():
    """Mock ccxt module."""
    with patch("ccxt_connector.ccxt") as mock:
        yield mock


@pytest.fixture
def mock_exchange():
    """Mock exchange instance."""
    exchange = MagicMock()
    exchange.load_markets.return_value = {
        "BTC/USDT": {"active": True, "type": "spot", "quote": "USDT"},
        "ETH/USDT": {"active": True, "type": "spot", "quote": "USDT"},
        "BTC/USD": {"active": False, "type": "spot", "quote": "USD"},
    }
    exchange.fetch_ohlcv.return_value = [
        [1609459200000, 29000.0, 29100.0, 28900.0, 29050.0, 100.0],
        [1609459260000, 29050.0, 29200.0, 29000.0, 29150.0, 150.0],
    ]
    exchange.fetch_ticker.return_value = {
        "symbol": "BTC/USDT",
        "last": 30000.0,
        "bid": 29950.0,
        "ask": 30050.0,
        "baseVolume": 1000.0,
        "bidVolume": 500.0,
        "askVolume": 600.0,
    }
    exchange.markets = {
        "BTC/USDT": {
            "active": True,
            "type": "spot",
            "quote": "USDT",
            "limits": {"amount": {"min": 0.001, "max": 1000}},
            "precision": {"price": 2, "amount": 8},
            "info": {"name": "Bitcoin/Tether"},
        }
    }
    return exchange


@pytest.fixture
def connector(mock_ccxt, mock_exchange):
    """Create a CCXTDataConnector instance with mocked dependencies."""
    mock_ccxt.binance = mock_exchange
    mock_ccxt.AuthenticationError = Exception
    mock_ccxt.NetworkError = Exception
    mock_ccxt.ExchangeNotAvailable = Exception
    mock_ccxt.RateLimitExceeded = Exception
    mock_ccxt.BadSymbol = Exception

    with patch("ccxt_connector.CCXT_AVAILABLE", True):
        return CCXTDataConnector(api_key="test_key", api_secret="test_secret")


class TestCCXTDataConnectorInit:
    """Test CCXTDataConnector initialization."""

    def test_init_with_default_parameters(self, mock_ccxt, mock_exchange):
        """Test initialization with default parameters."""
        mock_ccxt.binance = mock_exchange

        with patch("ccxt_connector.CCXT_AVAILABLE", True):
            connector = CCXTDataConnector()

        assert connector.exchange_name == "binance"
        assert connector.sandbox is False
        assert connector.enable_rate_limit is True
        assert connector._cache_ttl == 3600
        assert connector.timeout == 30

    def test_init_with_custom_parameters(self, mock_ccxt, mock_exchange):
        """Test initialization with custom parameters."""
        mock_ccxt.kraken = mock_exchange

        with patch("ccxt_connector.CCXT_AVAILABLE", True):
            connector = CCXTDataConnector(
                api_key="custom_key",
                api_secret="custom_secret",
                exchange="kraken",
                sandbox=True,
                enableRateLimit=False,
                cache_ttl=7200,
                timeout=60,
            )

        assert connector.exchange_name == "kraken"
        assert connector.sandbox is True
        assert connector.enable_rate_limit is False
        assert connector._cache_ttl == 7200
        assert connector.timeout == 60

    def test_init_without_ccxt_library(self):
        """Test initialization when ccxt is not installed."""
        with patch("ccxt_connector.CCXT_AVAILABLE", False):
            with pytest.raises(ImportError, match="CCXT library is not installed"):
                CCXTDataConnector()

    def test_init_with_invalid_exchange(self, mock_ccxt):
        """Test initialization with invalid exchange name."""
        mock_ccxt.invalid_exchange = None

        with patch("ccxt_connector.CCXT_AVAILABLE", True):
            with pytest.raises(
                ValueError, match="Exchange 'invalid_exchange' not found"
            ):
                CCXTDataConnector(exchange="invalid_exchange")

    def test_init_with_authentication_error(self, mock_ccxt):
        """Test initialization with authentication error."""
        mock_ccxt.binance.side_effect = mock_ccxt.AuthenticationError(
            "Invalid credentials"
        )

        with patch("ccxt_connector.CCXT_AVAILABLE", True):
            with pytest.raises(AuthenticationError, match="Failed to authenticate"):
                CCXTDataConnector(api_key="invalid", api_secret="invalid")

    def test_init_with_sandbox_mode_unsupported(self, mock_ccxt, mock_exchange):
        """Test initialization with sandbox mode when not supported."""
        del mock_exchange.set_sandbox_mode
        mock_ccxt.binance = mock_exchange

        with patch("ccxt_connector.CCXT_AVAILABLE", True):
            with patch("ccxt_connector.logging.getLogger") as mock_logger:
                connector = CCXTDataConnector(sandbox=True)
                mock_logger.return_value.warning.assert_called_once()


class TestConvertTimeframe:
    """Test _convert_timeframe method."""

    def test_convert_valid_timeframes(self, connector):
        """Test conversion of valid timeframes."""
        assert connector._convert_timeframe("1Min") == "1m"
        assert connector._convert_timeframe("5Min") == "5m"
        assert connector._convert_timeframe("15Min") == "15m"
        assert connector._convert_timeframe("1H") == "1h"
        assert connector._convert_timeframe("4H") == "4h"
        assert connector._convert_timeframe("1D") == "1d"
        assert connector._convert_timeframe("1W") == "1w"

    def test_convert_invalid_timeframe(self, connector):
        """Test conversion of invalid timeframe."""
        with pytest.raises(ValueError, match="Timeframe 2Min not supported"):
            connector._convert_timeframe("2Min")


class TestNormalizeSymbol:
    """Test _normalize_symbol method."""

    def test_normalize_ccxt_format(self, connector):
        """Test normalization of symbol already in ccxt format."""
        assert connector._normalize_symbol("BTC/USDT") == "BTC/USDT"
        assert connector._normalize_symbol("eth/usdt") == "ETH/USDT"

    def test_normalize_dash_format(self, connector):
        """Test normalization of symbol with dash."""
        assert connector._normalize_symbol("BTC-USDT") == "BTC/USDT"
        assert connector._normalize_symbol("eth-usd") == "ETH/USD"

    def test_normalize_concatenated_format(self, connector):
        """Test normalization of concatenated symbol."""
        assert connector._normalize_symbol("BTCUSDT") == "BTC/USDT"
        assert connector._normalize_symbol("ETHUSDC") == "ETH/USDC"
        assert connector._normalize_symbol("BTCUSD") == "BTC/USD"

    def test_normalize_unknown_format(self, connector):
        """Test normalization of unknown symbol format."""
        assert connector._normalize_symbol("UNKNOWN") == "UNKNOWN"
        assert connector._normalize_symbol("XYZ") == "XYZ"


class TestRefreshMarketCache:
    """Test _refresh_market_cache method."""

    def test_refresh_cache_first_time(self, connector):
        """Test refreshing cache for the first time."""
        connector._refresh_market_cache()

        assert connector._market_cache is not None
        assert connector._cache_timestamp is not None
        connector.exchange.load_markets.assert_called_once()

    def test_refresh_cache_when_expired(self, connector):
        """Test refreshing cache when expired."""
        # Set old timestamp
        connector._cache_timestamp = 1000000.0

        connector._refresh_market_cache()

        assert connector._cache_timestamp > 1000000.0
        connector.exchange.load_markets.assert_called_once()

    def test_refresh_cache_when_fresh(self, connector):
        """Test not refreshing cache when still fresh."""
        # Set fresh timestamp
        connector._cache_timestamp = datetime.now().timestamp()
        connector._market_cache = {"test": "data"}

        connector._refresh_market_cache()

        # Should not call load_markets again
        connector.exchange.load_markets.assert_not_called()

    def test_refresh_cache_rate_limit_error(self, connector):
        """Test refreshing cache with rate limit error."""
        connector.exchange.load_markets.side_effect = Exception("RateLimitExceeded")

        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            connector._refresh_market_cache()

    def test_refresh_cache_network_error(self, connector):
        """Test refreshing cache with network error."""
        connector.exchange.load_markets.side_effect = Exception("NetworkError")

        with pytest.raises(DataSourceError, match="Failed to load markets"):
            connector._refresh_market_cache()

    def test_refresh_cache_without_ccxt(self, connector):
        """Test refreshing cache when ccxt is not available."""
        with patch("ccxt_connector.CCXT_AVAILABLE", False):
            with pytest.raises(ImportError, match="CCXT library is not installed"):
                connector._refresh_market_cache()


class TestGetHistoricalData:
    """Test get_historical_data method."""

    def test_get_historical_data_success(self, connector):
        """Test successful retrieval of historical data."""
        start_date = datetime(2021, 1, 1, tzinfo=timezone.utc)

        df = connector.get_historical_data("BTC/USDT", "1H", start_date)

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
        assert len(df) == 2
        assert df["timestamp"].iloc[0] == pd.to_datetime(
            1609459200000, unit="ms", utc=True
        )

    def test_get_historical_data_with_end_date(self, connector):
        """Test retrieval of historical data with end date."""
        start_date = datetime(2021, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2021, 1, 1, 0, 1, tzinfo=timezone.utc)

        df = connector.get_historical_data("BTC/USDT", "1H", start_date, end_date)

        assert isinstance(df, pd.DataFrame)
        connector.exchange.fetch_ohlcv.assert_called_once()

    def test_get_historical_data_with_limit(self, connector):
        """Test retrieval of historical data with limit."""
        start_date = datetime(2021, 1, 1, tzinfo=timezone.utc)

        df = connector.get_historical_data("BTC/USDT", "1H", start_date, limit=100)

        assert isinstance(df, pd.DataFrame)
        connector.exchange.fetch_ohlcv.assert_called_once()

    def test_get_historical_data_empty_result(self, connector):
        """Test retrieval of historical data with empty result."""
        connector.exchange.fetch_ohlcv.return_value = []

        df = connector.get_historical_data("BTC/USDT", "1H", datetime.now())

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert list(df.columns) == [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

    def test_get_historical_data_symbol_not_found(self, connector):
        """Test retrieval with symbol not found."""
        connector.exchange.fetch_ohlcv.side_effect = Exception("BadSymbol")

        with pytest.raises(SymbolNotFoundError, match="Symbol INVALID not found"):
            connector.get_historical_data("INVALID", "1H", datetime.now())

    def test_get_historical_data_rate_limit(self, connector):
        """Test retrieval with rate limit error."""
        connector.exchange.fetch_ohlcv.side_effect = Exception("RateLimitExceeded")

        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            connector.get_historical_data("BTC/USDT", "1H", datetime.now())

    def test_get_historical_data_network_error(self, connector):
        """Test retrieval with network error."""
        connector.exchange.fetch_ohlcv.side_effect = Exception("NetworkError")

        with pytest.raises(DataSourceError, match="Failed to fetch data"):
            connector.get_historical_data("BTC/USDT", "1H", datetime.now())

    def test_get_historical_data_invalid_timeframe(self, connector):
        """Test retrieval with invalid timeframe."""
        with pytest.raises(ValueError, match="Timeframe 2Min not supported"):
            connector.get_historical_data("BTC/USDT", "2Min", datetime.now())


class TestGetRealTimeData:
    """Test get_real_time_data method."""

    def test_get_real_time_data_success(self, connector):
        """Test successful retrieval of real-time data."""
        data = connector.get_real_time_data("BTC/USDT")

        assert isinstance(data, dict)
        assert "timestamp" in data
        assert "price" in data
        assert "bid" in data
        assert "ask" in data
        assert "volume" in data
        assert data["price"] == 30000.0
        assert data["bid"] == 29950.0
        assert data["ask"] == 30050.0

    def test_get_real_time_data_without_last_price(self, connector):
        """Test retrieval when last price is not available."""
        connector.exchange.fetch_ticker.return_value = {
            "bid": 29950.0,
            "ask": 30050.0,
            "baseVolume": 1000.0,
        }

        data = connector.get_real_time_data("BTC/USDT")

        assert data["price"] == 30000.0  # (bid + ask) / 2

    def test_get_real_time_data_symbol_not_found(self, connector):
        """Test retrieval with symbol not found."""
        connector.exchange.fetch_ticker.side_effect = Exception("BadSymbol")

        with pytest.raises(SymbolNotFoundError, match="Symbol INVALID not found"):
            connector.get_real_time_data("INVALID")

    def test_get_real_time_data_rate_limit(self, connector):
        """Test retrieval with rate limit error."""
        connector.exchange.fetch_ticker.side_effect = Exception("RateLimitExceeded")

        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            connector.get_real_time_data("BTC/USDT")

    def test_get_real_time_data_authentication_error(self, connector):
        """Test retrieval with authentication error."""
        connector.exchange.fetch_ticker.side_effect = Exception("Invalid API key")

        with pytest.raises(AuthenticationError, match="Authentication failed"):
            connector.get_real_time_data("BTC/USDT")

    def test_get_real_time_data_exchange_down(self, connector):
        """Test retrieval when exchange is down."""
        connector.exchange.fetch_ticker.side_effect = Exception("Exchange down")

        with pytest.raises(DataSourceError, match="Failed to fetch ticker"):
            connector.get_real_time_data("BTC/USDT")


class TestGetQuote:
    """Test get_quote method."""

    def test_get_quote_success(self, connector):
        """Test successful retrieval of quote data."""
        quote = connector.get_quote("BTC/USDT")

        assert isinstance(quote, dict)
        assert "symbol" in quote
        assert "timestamp" in quote
        assert "bid_price" in quote
        assert "ask_price" in quote
        assert "bid_size" in quote
        assert "ask_size" in quote
        assert "last_price" in quote
        assert "last_size" in quote
        assert quote["symbol"] == "BTC/USDT"
        assert quote["bid_price"] == 29950.0
        assert quote["ask_price"] == 30050.0

    def test_get_quote_without_sizes(self, connector):
        """Test retrieval when bid/ask sizes are not available."""
        connector.exchange.fetch_ticker.return_value = {
            "last": 30000.0,
            "bid": 29950.0,
            "ask": 30050.0,
            "baseVolume": 1000.0,
        }

        quote = connector.get_quote("BTC/USDT")

        assert quote["bid_size"] == 500.0  # Estimated from volume
        assert quote["ask_size"] == 500.0  # Estimated from volume

    def test_get_quote_symbol_not_found(self, connector):
        """Test retrieval with symbol not found."""
        connector.exchange.fetch_ticker.side_effect = Exception("BadSymbol")

        with pytest.raises(SymbolNotFoundError, match="Symbol INVALID not found"):
            connector.get_quote("INVALID")

    def test_get_quote_rate_limit(self, connector):
        """Test retrieval with rate limit error."""
        connector.exchange.fetch_ticker.side_effect = Exception("RateLimitExceeded")

        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            connector.get_quote("BTC/USDT")

    def test_get_quote_authentication_error(self, connector):
        """Test retrieval with authentication error."""
        connector.exchange.fetch_ticker.side_effect = Exception("Invalid API key")

        with pytest.raises(AuthenticationError, match="Authentication failed"):
            connector.get_quote("BTC/USDT")


class TestGetAvailableSymbols:
    """Test get_available_symbols method."""

    def test_get_available_symbols_success(self, connector):
        """Test successful retrieval of available symbols."""
        symbols = connector.get_available_symbols()

        assert isinstance(symbols, list)
        assert "BTC/USDT" in symbols
        assert "ETH/USDT" in symbols
        assert "BTC/USD" not in symbols  # Inactive

    def test_get_available_symbols_with_limit(self, connector):
        """Test retrieval with limit."""
        symbols = connector.get_available_symbols(limit=1)

        assert len(symbols) == 1

    def test_get_available_symbols_rate_limit(self, connector):
        """Test retrieval with rate limit error."""
        connector.exchange.load_markets.side_effect = Exception("RateLimitExceeded")

        with pytest.raises(Exception) as excinfo:
            connector.get_available_symbols()

        assert "RateLimitExceeded" in str(excinfo.value)
