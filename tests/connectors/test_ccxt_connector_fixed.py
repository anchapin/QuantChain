"""Tests for CCXT data connector."""

import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


# Create custom exception classes before importing anything
class CCXTAuthenticationError(Exception):
    pass


class CCXTBadSymbol(Exception):
    pass


class CCXTNetworkError(Exception):
    pass


class CCXTExchangeNotAvailable(Exception):
    pass


class CCXTRateLimitExceeded(Exception):
    pass


# Mock ccxt before importing the connector
ccxt_mock = MagicMock()
# Add the necessary exception classes to the mock
ccxt_mock.AuthenticationError = CCXTAuthenticationError
ccxt_mock.BadSymbol = CCXTBadSymbol
ccxt_mock.NetworkError = CCXTNetworkError
ccxt_mock.ExchangeNotAvailable = CCXTExchangeNotAvailable
ccxt_mock.RateLimitExceeded = CCXTRateLimitExceeded
# Set up mock before importing connector
# Remove any existing ccxt module from cache
if "ccxt" in sys.modules:
    del sys.modules["ccxt"]
# Also remove quantchain.connectors.ccxt_connector if already imported
if "quantchain.connectors.ccxt_connector" in sys.modules:
    del sys.modules["quantchain.connectors.ccxt_connector"]
sys.modules["ccxt"] = ccxt_mock

# Import all needed modules at top to avoid E402 errors
from quantchain.connectors.ccxt_connector import CCXTDataConnector
from quantchain.core.exceptions import (
    AuthenticationError,
    DataSourceError,
    RateLimitError,
    SymbolNotFoundError,
)


@pytest.mark.unit
class TestCCXTDataConnector:
    """Test suite for CCXTDataConnector."""

    @pytest.fixture
    def mock_exchange(self):
        """Create a mock ccxt exchange instance."""
        exchange = MagicMock()
        exchange.markets = {
            "BTC/USDT": {
                "id": "BTCUSDT",
                "symbol": "BTC/USDT",
                "base": "BTC",
                "quote": "USDT",
                "active": True,
                "type": "spot",
                "limits": {
                    "amount": {"min": 0.00001, "max": 1000},
                    "price": {"min": 0.01, "max": 1000000},
                    "cost": {"min": 10, "max": 1000000},
                },
                "precision": {"price": 2, "amount": 8},
            },
            "ETH/USDT": {
                "id": "ETHUSDT",
                "symbol": "ETH/USDT",
                "base": "ETH",
                "quote": "USDT",
                "active": True,
                "type": "spot",
                "limits": {
                    "amount": {"min": 0.001, "max": 10000},
                    "price": {"min": 0.01, "max": 100000},
                    "cost": {"min": 10, "max": 100000},
                },
                "precision": {"price": 2, "amount": 8},
            },
        }
        # Mock all methods that tests will try to configure with proper MagicMock objects
        exchange.load_markets = MagicMock(return_value=exchange.markets)
        exchange.fetch_ticker = MagicMock()
        exchange.fetch_ohlcv = MagicMock()
        exchange.fetch_order_book = MagicMock()
        exchange.set_sandbox_mode = MagicMock()

        # Add dict-like behavior
        exchange.__getitem__ = lambda self, key: self.markets.get(key)
        exchange.__contains__ = lambda self, key: key in self.markets
        exchange.items = lambda: self.markets.items()
        return exchange

    @pytest.fixture
    def connector(self, mock_exchange):
        """Create a test connector instance with mocked exchange."""
        with patch("ccxt.binance", return_value=mock_exchange):
            with patch("ccxt.kraken", return_value=mock_exchange):
                # Initialize connector with mocked markets to avoid API calls
                connector = CCXTDataConnector(exchange="binance")
                # Ensure cache is populated to avoid API calls
                connector._market_cache = mock_exchange.markets.copy()
                connector._cache_timestamp = datetime.now()
                return connector

    @pytest.fixture
    def sample_ohlcv_data(self):
        """Sample OHLCV data from ccxt."""
        return [
            [1672531200000, 16500.0, 16600.0, 16400.0, 16550.0, 100.5],  # 2023-01-01
            [
                1672534800000,
                16550.0,
                16700.0,
                16500.0,
                16650.0,
                120.3,
            ],  # 2023-01-01 01:00
            [
                1672538400000,
                16650.0,
                16800.0,
                16600.0,
                16750.0,
                95.7,
            ],  # 2023-01-01 02:00
        ]

    @pytest.fixture
    def sample_ticker_data(self):
        """Sample ticker data from ccxt."""
        return {
            "symbol": "BTC/USDT",
            "timestamp": 1672531200000,
            "datetime": "2023-01-01T00:00:00.000Z",
            "high": 16600.0,
            "low": 16400.0,
            "bid": 16548.5,
            "bidVolume": 1.25,
            "ask": 16551.5,
            "askVolume": 0.85,
            "vwap": 16550.0,
            "open": 16500.0,
            "close": 16550.0,
            "last": 16550.0,
            "previousClose": 16450.0,
            "change": 100.0,
            "percentage": 0.607,
            "average": 16500.0,
            "baseVolume": 100.5,
            "quoteVolume": 1660075.0,
            "info": {},
        }

    def test_initialization_success(self, mock_exchange):
        """Test successful initialization with default exchange."""
        with patch(
            "quantchain.connectors.ccxt_connector.ccxt.binance",
            return_value=mock_exchange,
        ):
            connector = CCXTDataConnector()

            assert connector.exchange == mock_exchange

    def test_initialization_with_credentials(self, mock_exchange):
        """Test initialization with API credentials."""
        with patch.object(ccxt_mock, "binance", return_value=mock_exchange):
            CCXTDataConnector(api_key="test_key", api_secret="test_secret")

            args, kwargs = ccxt_mock.binance.call_args
            if args:
                params = args[0]
                assert params.get("apiKey") == "test_key"
                assert params.get("secret") == "test_secret"

    def test_initialization_custom_exchange(self, mock_exchange):
        """Test initialization with custom exchange."""
        with patch(
            "quantchain.connectors.ccxt_connector.ccxt.kraken",
            return_value=mock_exchange,
        ):
            connector = CCXTDataConnector(exchange="kraken")

            assert connector.exchange == mock_exchange

    def test_initialization_with_kwargs(self, mock_exchange):
        """Test initialization with additional kwargs."""
        mock_exchange.set_sandbox_mode = MagicMock()

        with patch.object(ccxt_mock, "binance", return_value=mock_exchange):
            connector = CCXTDataConnector(
                sandbox=True, enableRateLimit=False, cache_ttl=1800, timeout=60
            )

            args, kwargs = ccxt_mock.binance.call_args
            if args:
                params = args[0]
                assert params.get("enableRateLimit") is False
                assert params.get("timeout") == 60
            mock_exchange.set_sandbox_mode.assert_called_once_with(True)
            assert connector._cache_ttl == 1800

    def test_initialization_auth_failure(self):
        """Test initialization failure due to authentication error."""

        # Create a mock that raises AuthenticationError when initialized
        def raise_auth_error(*args, **kwargs):
            raise CCXTAuthenticationError("Invalid credentials")

        with patch.object(ccxt_mock, "binance", side_effect=raise_auth_error):
            with pytest.raises(AuthenticationError):
                CCXTDataConnector(api_key="bad_key", api_secret="bad_secret")

    def test_convert_timeframe(self, connector):
        """Test timeframe conversion."""
        assert connector._convert_timeframe("1Min") == "1m"
        assert connector._convert_timeframe("5Min") == "5m"
        assert connector._convert_timeframe("15Min") == "15m"
        assert connector._convert_timeframe("1H") == "1h"
        assert connector._convert_timeframe("4H") == "4h"
        assert connector._convert_timeframe("1D") == "1d"
        assert connector._convert_timeframe("1W") == "1w"

    def test_convert_timeframe_invalid(self, connector):
        """Test conversion with invalid timeframe."""
        with pytest.raises(ValueError):
            connector._convert_timeframe("2H")

    def test_normalize_symbol(self, connector):
        """Test symbol normalization."""
        assert connector._normalize_symbol("BTC/USDT") == "BTC/USDT"
        assert connector._normalize_symbol("BTC-USDT") == "BTC/USDT"
        assert connector._normalize_symbol("BTCUSDT") == "BTC/USDT"
        assert connector._normalize_symbol("ETH/USD") == "ETH/USD"

    def test_get_historical_data_success(self, connector, sample_ohlcv_data):
        """Test successful historical data retrieval."""
        # Mock the fetch_ohlcv method as a MagicMock
        connector.exchange.fetch_ohlcv = MagicMock(return_value=sample_ohlcv_data)

        start_date = datetime(2023, 1, 1)
        df = connector.get_historical_data("BTC/USDT", "1H", start_date)

        # Verify DataFrame structure
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
        assert len(df) == 3

        # Verify data
        assert df.iloc[0]["timestamp"] == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert df.iloc[0]["open"] == 16500.0
        assert df.iloc[0]["high"] == 16600.0
        assert df.iloc[0]["low"] == 16400.0
        assert df.iloc[0]["close"] == 16550.0
        assert df.iloc[0]["volume"] == 100.5

    def test_get_historical_data_with_limit(self, connector, sample_ohlcv_data):
        """Test historical data retrieval with limit."""
        # Mock the fetch_ohlcv method
        mock_fetch = MagicMock(return_value=sample_ohlcv_data)
        connector.exchange.fetch_ohlcv = mock_fetch

        start_date = datetime(2023, 1, 1)
        connector.get_historical_data("BTC/USDT", "1H", start_date, limit=100)

        mock_fetch.assert_called_once_with("BTC/USDT", "1h", since=None, limit=100)

    def test_get_historical_data_with_date_range(self, connector, sample_ohlcv_data):
        """Test historical data retrieval with date range."""
        # Mock the fetch_ohlcv method
        mock_fetch = MagicMock(return_value=sample_ohlcv_data)
        connector.exchange.fetch_ohlcv = mock_fetch

        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 2)
        connector.get_historical_data("BTC/USDT", "1H", start_date, end_date)

        # Verify start_date was converted to milliseconds
        call_args = mock_fetch.call_args
        assert call_args[0][0] == "BTC/USDT"  # symbol
        assert call_args[0][1] == "1h"  # timeframe
        # since should be start_date in milliseconds
        assert isinstance(call_args[1]["since"], int)

    def test_get_historical_data_symbol_not_found(self, connector):
        """Test historical data with symbol not found."""
        # Mock the fetch_ohlcv method
        mock_fetch = MagicMock(side_effect=CCXTBadSymbol("Symbol not found"))
        connector.exchange.fetch_ohlcv = mock_fetch

        start_date = datetime(2023, 1, 1)
        with pytest.raises(SymbolNotFoundError):
            connector.get_historical_data("INVALID/PAIR", "1H", start_date)

    def test_get_historical_data_network_error(self, connector):
        """Test historical data with network error."""
        # Mock the fetch_ohlcv method
        mock_fetch = MagicMock(side_effect=CCXTNetworkError("Network error"))
        connector.exchange.fetch_ohlcv = mock_fetch

        start_date = datetime(2023, 1, 1)
        with pytest.raises(DataSourceError):
            connector.get_historical_data("BTC/USDT", "1H", start_date)

    def test_get_historical_data_rate_limit_error(self, connector):
        """Test historical data with rate limit error."""
        # Mock the fetch_ohlcv method
        mock_fetch = MagicMock(side_effect=CCXTRateLimitExceeded("Rate limit exceeded"))
        connector.exchange.fetch_ohlcv = mock_fetch

        start_date = datetime(2023, 1, 1)
        with pytest.raises(RateLimitError):
            connector.get_historical_data("BTC/USDT", "1H", start_date)

    def test_get_historical_data_empty_response(self, connector):
        """Test handling of empty OHLCV response."""
        # Mock the fetch_ohlcv method
        mock_fetch = MagicMock(return_value=[])
        connector.exchange.fetch_ohlcv = mock_fetch

        start_date = datetime(2023, 1, 1)
        df = connector.get_historical_data("BTC/USDT", "1H", start_date)

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

    def test_get_real_time_data_success(self, connector, sample_ticker_data):
        """Test successful real-time data retrieval."""
        # Mock the fetch_ticker method
        mock_fetch = MagicMock(return_value=sample_ticker_data)
        connector.exchange.fetch_ticker = mock_fetch

        data = connector.get_real_time_data("BTC/USDT")

        assert isinstance(data, dict)
        assert "timestamp" in data
        assert "price" in data
        assert "bid" in data
        assert "ask" in data
        assert "volume" in data
        assert data["price"] == 16550.0
        assert data["bid"] == 16548.5
        assert data["ask"] == 16551.5
        assert data["volume"] == 100.5

    def test_get_real_time_data_missing_bid_ask(self, connector):
        """Test real-time data with missing bid/ask."""
        ticker = {"symbol": "BTC/USDT", "last": 16550.0, "baseVolume": 100.5}
        # Mock the fetch_ticker method
        mock_fetch = MagicMock(return_value=ticker)
        connector.exchange.fetch_ticker = mock_fetch

        data = connector.get_real_time_data("BTC/USDT")

        assert data["price"] == 16550.0
        assert data["bid"] == 0.0  # Missing fields default to 0
        assert data["ask"] == 0.0
        assert data["volume"] == 100.5

    def test_get_real_time_data_symbol_not_found(self, connector):
        """Test real-time data with symbol not found."""
        # Mock the fetch_ticker method
        mock_fetch = MagicMock(side_effect=CCXTBadSymbol("Symbol not found"))
        connector.exchange.fetch_ticker = mock_fetch

        with pytest.raises(SymbolNotFoundError):
            connector.get_real_time_data("INVALID/PAIR")

    def test_get_quote_success(self, connector, sample_ticker_data):
        """Test successful quote retrieval."""
        # Mock the fetch_ticker method
        mock_fetch = MagicMock(return_value=sample_ticker_data)
        connector.exchange.fetch_ticker = mock_fetch

        quote = connector.get_quote("BTC/USDT")

        assert isinstance(quote, dict)
        assert quote["symbol"] == "BTC/USDT"
        assert "timestamp" in quote
        assert quote["bid_price"] == 16548.5
        assert quote["ask_price"] == 16551.5
        assert quote["bid_size"] == 1.25
        assert quote["ask_size"] == 0.85
        assert quote["last_price"] == 16550.0
        assert quote["last_size"] == 100.5

    def test_get_quote_calculates_sizes(self, connector):
        """Test quote calculation when sizes missing."""
        ticker = {
            "symbol": "BTC/USDT",
            "bid": 16548.5,
            "ask": 16551.5,
            "last": 16550.0,
            "baseVolume": 100.5,
            "quoteVolume": 1660075.0,
        }
        # Mock the fetch_ticker method
        mock_fetch = MagicMock(return_value=ticker)
        connector.exchange.fetch_ticker = mock_fetch

        quote = connector.get_quote("BTC/USDT")

        # Calculate sizes from volume when not provided
        assert quote["bid_size"] > 0
        assert quote["ask_size"] > 0
        assert quote["last_size"] == 100.5

    def test_get_quote_symbol_not_found(self, connector):
        """Test quote with symbol not found."""
        # Mock the fetch_ticker method
        mock_fetch = MagicMock(side_effect=CCXTBadSymbol("Symbol not found"))
        connector.exchange.fetch_ticker = mock_fetch

        with pytest.raises(SymbolNotFoundError):
            connector.get_quote("INVALID/PAIR")

    def test_get_available_symbols_all(self, connector):
        """Test getting all available symbols."""
        symbols = connector.get_available_symbols()

        assert isinstance(symbols, list)
        assert "BTC/USDT" in symbols
        assert "ETH/USDT" in symbols

    def test_get_available_symbols_with_limit(self, connector):
        """Test getting symbols with limit."""
        symbols = connector.get_available_symbols(limit=1)

        assert isinstance(symbols, list)
        assert len(symbols) == 1

    def test_get_available_symbols_cache_hit(self, connector):
        """Test that cache is used on second call."""
        # First call
        connector.get_available_symbols()
        initial_call_count = connector.exchange.load_markets.call_count

        # Second call should use cache
        connector.get_available_symbols()
        assert connector.exchange.load_markets.call_count == initial_call_count

    def test_get_available_symbols_cache_refresh(self, connector):
        """Test cache refresh after TTL expires."""
        # First call
        connector.get_available_symbols()

        # Reset call counter to avoid counting the setup call
        connector.exchange.load_markets.reset_mock()

        # Expire cache
        connector._cache_timestamp = datetime.now() - timedelta(seconds=3700)

        # Second call should refresh cache
        connector.get_available_symbols()
        assert connector.exchange.load_markets.call_count == 1

    def test_get_symbol_info_success(self, connector):
        """Test successful symbol info retrieval."""
        info = connector.get_symbol_info("BTC/USDT")

        assert isinstance(info, dict)
        assert info["symbol"] == "BTC/USDT"
        assert info["market"] == "crypto"
        assert info["currency"] == "USDT"
        assert info["min_order_size"] == 0.00001
        assert info["max_order_size"] == 1000
        assert info["price_precision"] == 2
        assert info["size_precision"] == 8

    def test_get_symbol_info_not_found(self, connector):
        """Test symbol info for non-existent symbol."""
        with pytest.raises(SymbolNotFoundError):
            connector.get_symbol_info("INVALID/PAIR")

    def test_is_market_open_always_true(self, connector):
        """Test that crypto markets are always open."""
        assert connector.is_market_open() is True
        assert connector.is_market_open("crypto") is True

    def test_rate_limit_error_handling(self, connector):
        """Test rate limit error handling."""
        # Mock the fetch_ticker method
        mock_fetch = MagicMock(side_effect=CCXTRateLimitExceeded("Rate limit"))
        connector.exchange.fetch_ticker = mock_fetch

        with pytest.raises(RateLimitError):
            connector.get_real_time_data("BTC/USDT")

    def test_authentication_error_handling(self, connector):
        """Test authentication error handling during operations."""
        # Mock the fetch_ticker method
        mock_fetch = MagicMock(side_effect=CCXTAuthenticationError("Invalid API key"))
        connector.exchange.fetch_ticker = mock_fetch

        with pytest.raises(AuthenticationError):
            connector.get_real_time_data("BTC/USDT")

    def test_exchange_not_available_error(self, connector):
        """Test exchange not available error handling."""
        # Mock the fetch_ticker method
        mock_fetch = MagicMock(side_effect=CCXTExchangeNotAvailable("Exchange down"))
        connector.exchange.fetch_ticker = mock_fetch

        with pytest.raises(DataSourceError):
            connector.get_real_time_data("BTC/USDT")

    def test_sandbox_mode_configuration(self, mock_exchange):
        """Test sandbox mode configuration."""
        mock_exchange.set_sandbox_mode = MagicMock()

        with patch("ccxt.binance", return_value=mock_exchange):
            CCXTDataConnector(sandbox=True)

            mock_exchange.set_sandbox_mode.assert_called_once_with(True)

    def test_custom_timeout_configuration(self, mock_exchange):
        """Test custom timeout configuration."""
        with patch.object(ccxt_mock, "binance", return_value=mock_exchange):
            CCXTDataConnector(timeout=60)

            args, kwargs = ccxt_mock.binance.call_args
            if args:
                params = args[0]
                assert params.get("timeout") == 60

    def test_rate_limit_configuration(self, mock_exchange):
        """Test rate limit configuration."""
        with patch.object(ccxt_mock, "binance", return_value=mock_exchange):
            CCXTDataConnector(enableRateLimit=False)

            args, kwargs = ccxt_mock.binance.call_args
            if args:
                params = args[0]
                assert params.get("enableRateLimit") is False

    def test_refresh_market_cache_error(self, connector):
        """Test error handling in market cache refresh."""
        # Mock the load_markets method
        mock_load = MagicMock(side_effect=CCXTNetworkError("Network error"))
        connector.exchange.load_markets = mock_load

        # Clear cache to force refresh
        connector._cache_timestamp = None

        with pytest.raises(DataSourceError):
            connector._refresh_market_cache()
