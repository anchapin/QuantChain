"""Comprehensive tests for alpaca_connector module."""

import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from quantchain.connectors.alpaca_connector import AlpacaDataConnector
from quantchain.core.exceptions import (
    AuthenticationError,
    DataSourceError,
    SymbolNotFoundError,
)


class TestAlpacaDataConnector:
    """Test AlpacaDataConnector functionality."""

    @pytest.mark.unit
    def test_connector_init_with_credentials(self):
        """Test connector initialization with provided credentials."""
        connector = AlpacaDataConnector(
            api_key="test_key", secret_key="test_secret", paper_trading=True
        )

        assert connector.api_key == "test_key"
        assert connector.secret_key == "test_secret"
        assert connector.paper_trading is True
        assert connector.symbol_limit == 100
        assert connector.retry_count == 3
        assert connector.retry_delay == 1.0

    @pytest.mark.unit
    def test_connector_init_env_credentials(self):
        """Test connector initialization with environment credentials."""
        with patch.dict(
            os.environ, {"ALPACA_API_KEY": "env_key", "ALPACA_SECRET_KEY": "env_secret"}
        ):
            connector = AlpacaDataConnector()

            assert connector.api_key == "env_key"
            assert connector.secret_key == "env_secret"

    @pytest.mark.unit
    def test_connector_init_missing_credentials(self):
        """Test connector initialization with missing credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                AuthenticationError, match="Alpaca API credentials not provided"
            ):
                AlpacaDataConnector()

    @pytest.mark.unit
    def test_connector_init_custom_params(self):
        """Test connector initialization with custom parameters."""
        connector = AlpacaDataConnector(
            api_key="test_key",
            secret_key="test_secret",
            paper_trading=False,
            symbol_limit=500,
            retry_count=5,
            retry_delay=2.0,
        )

        assert connector.paper_trading is False
        assert connector.symbol_limit == 500
        assert connector.retry_count == 5
        assert connector.retry_delay == 2.0

    @pytest.mark.unit
    def test_initialize_clients_success(self):
        """Test successful client initialization."""
        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            with patch(
                "quantchain.connectors.alpaca_connector.StockHistoricalDataClient"
            ) as mock_stock, patch(
                "quantchain.connectors.alpaca_connector.CryptoHistoricalDataClient"
            ) as mock_crypto, patch(
                "quantchain.connectors.alpaca_connector.TradingClient"
            ) as mock_trading:

                connector = AlpacaDataConnector(
                    api_key="test_key", secret_key="test_secret"
                )
                # _initialize_clients is called in __init__

                mock_stock.assert_called_once_with("test_key", "test_secret")
                mock_crypto.assert_called_once_with("test_key", "test_secret")
                mock_trading.assert_called_once_with(
                    "test_key", "test_secret", paper=True
                )

    @pytest.mark.unit
    def test_initialize_clients_failure(self):
        """Test client initialization failure."""
        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            with patch(
                "quantchain.connectors.alpaca_connector.StockHistoricalDataClient"
            ) as mock_stock:
                mock_stock.side_effect = Exception("Authentication failed")

                with pytest.raises(
                    AuthenticationError, match="Failed to authenticate with Alpaca"
                ):
                    connector = AlpacaDataConnector(
                        api_key="invalid_key", secret_key="invalid_secret"
                    )

    @pytest.mark.unit
    def test_is_crypto_symbol(self):
        """Test crypto symbol detection."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Crypto symbols with slash
        assert connector._is_crypto_symbol("BTC/USD") is True
        assert connector._is_crypto_symbol("ETH/USDT") is True

        # Crypto symbols with dash
        assert connector._is_crypto_symbol("BTC-USD") is True
        assert connector._is_crypto_symbol("ETH-USDT") is True

        # Stock symbols (no slash or dash)
        assert connector._is_crypto_symbol("AAPL") is False
        assert connector._is_crypto_symbol("GOOGL") is False

    @pytest.mark.unit
    def test_normalize_crypto_symbol(self):
        """Test crypto symbol normalization."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Should replace dash with slash
        assert connector._normalize_crypto_symbol("BTC-USD") == "BTC/USD"
        assert connector._normalize_crypto_symbol("ETH-USDT") == "ETH/USDT"

        # Should leave slash unchanged
        assert connector._normalize_crypto_symbol("BTC/USD") == "BTC/USD"

    @pytest.mark.unit
    def test_convert_timeframe_valid(self):
        """Test timeframe conversion for valid timeframes."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector.TimeFrame") as mock_tf:
            mock_tf.Minute = "1Min"
            mock_tf.Hour = "1H"
            mock_tf.Day = "1D"

            assert connector._convert_timeframe("1Min") == "1Min"
            assert connector._convert_timeframe("1H") == "1H"
            assert connector._convert_timeframe("1D") == "1D"

    @pytest.mark.unit
    def test_convert_timeframe_invalid(self):
        """Test timeframe conversion for invalid timeframes."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector.TimeFrame") as mock_tf:
            # Mock TimeFrame attributes if needed or rely on default mock behavior
            pass

        with pytest.raises(ValueError):
            connector._convert_timeframe("invalid")

    @pytest.mark.unit
    def test_refresh_symbol_cache_success(self):
        """Test successful symbol cache refresh."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            # Mock trading client and assets
            mock_asset1 = Mock()
            mock_asset1.symbol = "AAPL"
            mock_asset1.asset_class = "us_equity"

            mock_asset2 = Mock()
            mock_asset2.symbol = "BTC/USD"
            mock_asset2.asset_class = "crypto"

            mock_trading_client = Mock()
            mock_trading_client.get_all_assets.return_value = [mock_asset1, mock_asset2]
            connector.trading_client = mock_trading_client

            with patch(
                "quantchain.connectors.alpaca_connector.AssetClass"
            ) as mock_asset_class:
                mock_asset_class.US_EQUITY = "us_equity"

                connector._refresh_symbol_cache()

                assert "AAPL" in connector._symbol_cache
                assert connector._symbol_cache["AAPL"]["market"] == "equity"
                assert "BTC/USD" in connector._symbol_cache
                assert connector._symbol_cache["BTC/USD"]["market"] == "crypto"

    @pytest.mark.unit
    def test_refresh_symbol_cache_failure(self):
        """Test symbol cache refresh failure."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            mock_trading_client = Mock()
            mock_trading_client.get_all_assets.side_effect = Exception("API Error")
            connector.trading_client = mock_trading_client

            connector._refresh_symbol_cache()

            # Cache should be empty after failure
            assert connector._symbol_cache == {}

    @pytest.mark.unit
    def test_refresh_symbol_cache_unavailable(self):
        """Test symbol cache refresh when Alpaca not available."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", False):
            connector._refresh_symbol_cache()

            assert connector._symbol_cache == {}

    @pytest.mark.unit
    def test_get_historical_data_library_unavailable(self):
        """Test historical data retrieval when library unavailable."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", False):
            with pytest.raises(DataSourceError, match="Alpaca library not installed"):
                connector.get_historical_data("AAPL", "1D")

    @pytest.mark.unit
    def test_get_historical_data_crypto_symbol(self):
        """Test historical data retrieval for crypto symbol."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            with patch(
                "quantchain.connectors.alpaca_connector._PANDAS_AVAILABLE", True
            ):
                # Mock crypto client
                mock_crypto_client = Mock()
                mock_bars = Mock()
                mock_bars.df = Mock()
                mock_bars.__contains__ = Mock(return_value=True)
                mock_crypto_client.get_crypto_bars.return_value = mock_bars
                connector.crypto_client = mock_crypto_client

                # Mock cache
                connector._symbol_cache = {"BTC/USD": {"market": "crypto"}}

                result = connector.get_historical_data("BTC-USD", "1D")

                mock_crypto_client.get_crypto_bars.assert_called_once()
                assert result == mock_bars.df

    @pytest.mark.unit
    def test_get_historical_data_stock_symbol(self):
        """Test historical data retrieval for stock symbol."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            with patch(
                "quantchain.connectors.alpaca_connector._PANDAS_AVAILABLE", True
            ):
                # Mock stock client
                mock_stock_client = Mock()
                mock_bars = Mock()
                mock_bars.df = Mock()
                mock_bars.__contains__ = Mock(return_value=True)
                mock_stock_client.get_stock_bars.return_value = mock_bars
                connector.stock_client = mock_stock_client

                # Mock cache
                connector._symbol_cache = {"AAPL": {"market": "equity"}}

                result = connector.get_historical_data("AAPL", "1D")

                mock_stock_client.get_stock_bars.assert_called_once()
                assert result == mock_bars.df

    @pytest.mark.unit
    def test_get_historical_data_symbol_not_found(self):
        """Test historical data retrieval for unknown symbol."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            # Mock empty cache
            connector._symbol_cache = {}

            with pytest.raises(SymbolNotFoundError, match="Symbol UNKNOWN not found"):
                connector.get_historical_data("UNKNOWN", "1D")

    @pytest.mark.unit
    def test_get_historical_data_default_dates(self):
        """Test historical data retrieval with default date ranges."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            with patch(
                "quantchain.connectors.alpaca_connector._PANDAS_AVAILABLE", True
            ):
                # Mock stock client
                mock_stock_client = Mock()
                mock_bars = Mock()
                mock_bars.df = Mock()
                mock_bars.__contains__ = Mock(return_value=True)
                mock_stock_client.get_stock_bars.return_value = mock_bars
                connector.stock_client = mock_stock_client

                # Mock cache
                connector._symbol_cache = {"AAPL": {"market": "equity"}}

                # Test with default parameters (no dates provided)
                result = connector.get_historical_data("AAPL", "1Min")

                # Should call with date range
                args, kwargs = mock_stock_client.get_stock_bars.call_args
                assert "start" in kwargs
                assert "end" in kwargs

    @pytest.mark.unit
    def test_get_historical_data_retry_mechanism(self):
        """Test retry mechanism for historical data retrieval."""
        connector = AlpacaDataConnector(
            api_key="test_key", secret_key="test_secret", retry_count=3, retry_delay=0.1
        )

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            # Mock stock client that fails then succeeds
            mock_stock_client = Mock()
            mock_stock_client.get_stock_bars.side_effect = [
                Exception("Network error"),
                Exception("Network error"),
                Mock(df=Mock(), __contains__=Mock(return_value=True)),
            ]
            connector.stock_client = mock_stock_client

            # Mock cache
            connector._symbol_cache = {"AAPL": {"market": "equity"}}

            with patch("time.sleep"):  # Skip sleep for faster tests
                result = connector.get_historical_data("AAPL", "1D")

            # Should have retried 3 times
            assert mock_stock_client.get_stock_bars.call_count == 3

    @pytest.mark.unit
    def test_get_historical_data_retry_exhausted(self):
        """Test retry exhausted for historical data retrieval."""
        connector = AlpacaDataConnector(
            api_key="test_key", secret_key="test_secret", retry_count=3, retry_delay=0.1
        )

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            # Mock stock client that always fails
            mock_stock_client = Mock()
            mock_stock_client.get_stock_bars.side_effect = Exception("Persistent error")
            connector.stock_client = mock_stock_client

            # Mock cache
            connector._symbol_cache = {"AAPL": {"market": "equity"}}

            with patch("time.sleep"):  # Skip sleep for faster tests
                with pytest.raises(
                    DataSourceError, match="Failed to get data for AAPL"
                ):
                    connector.get_historical_data("AAPL", "1D")

            # Should have retried 3 times
            assert mock_stock_client.get_stock_bars.call_count == 3

    @pytest.mark.unit
    def test_get_real_time_data_library_unavailable(self):
        """Test real-time data retrieval when library unavailable."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", False):
            with pytest.raises(DataSourceError, match="Alpaca library not installed"):
                connector.get_real_time_data("AAPL")

    @pytest.mark.unit
    def test_get_real_time_data_crypto(self):
        """Test real-time data retrieval for crypto."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            # Mock crypto client
            mock_crypto_client = Mock()
            mock_quote = Mock()
            mock_quote.bid_price = 50000.0
            mock_quote.ask_price = 50100.0
            mock_quote.timestamp = datetime.now()

            mock_quotes = {"BTC/USD": mock_quote}
            mock_crypto_client.get_crypto_latest_quote.return_value = mock_quotes
            connector.crypto_client = mock_crypto_client

            # Mock cache
            connector._symbol_cache = {"BTC/USD": {"market": "crypto"}}

            result = connector.get_real_time_data("BTC/USD")

            assert result["symbol"] == "BTC/USD"
            assert result["bid"] == 50000.0
            assert result["ask"] == 50100.0
            # For crypto, price should be ask price
            assert result["price"] == 50100.0

    @pytest.mark.unit
    def test_get_real_time_data_stock(self):
        """Test real-time data retrieval for stock."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            # Mock stock client
            mock_stock_client = Mock()
            mock_quote = Mock()
            mock_quote.bid_price = 150.0
            mock_quote.ask_price = 151.0
            mock_quote.timestamp = datetime.now()

            mock_quotes = {"AAPL": mock_quote}
            mock_stock_client.get_stock_latest_quote.return_value = mock_quotes
            connector.stock_client = mock_stock_client

            # Mock cache
            connector._symbol_cache = {"AAPL": {"market": "equity"}}

            result = connector.get_real_time_data("AAPL")

            assert result["symbol"] == "AAPL"
            assert result["bid"] == 150.0
            assert result["ask"] == 151.0
            # For stocks, price should be mid-price
            assert result["price"] == 150.5

    @pytest.mark.unit
    def test_get_real_time_data_symbol_not_found(self):
        """Test real-time data retrieval for unknown symbol."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            # Mock empty cache
            connector._symbol_cache = {}

            with pytest.raises(SymbolNotFoundError, match="Symbol UNKNOWN not found"):
                connector.get_real_time_data("UNKNOWN")

    @pytest.mark.unit
    def test_get_real_time_data_no_data(self):
        """Test real-time data retrieval when no data available."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            # Mock stock client that returns empty quotes
            mock_stock_client = Mock()
            mock_stock_client.get_stock_latest_quote.return_value = {}
            connector.stock_client = mock_stock_client

            # Mock cache
            connector._symbol_cache = {"AAPL": {"market": "equity"}}

            with pytest.raises(
                DataSourceError, match="Failed to get quote for AAPL"
            ):
                connector.get_real_time_data("AAPL")

    @pytest.mark.unit
    def test_get_quote(self):
        """Test getting detailed quote information."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock get_real_time_data
        mock_real_time_data = {
            "symbol": "AAPL",
            "price": 150.5,
            "bid": 150.0,
            "ask": 151.0,
            "timestamp": datetime.now(),
        }

        with patch.object(
            connector, "get_real_time_data", return_value=mock_real_time_data
        ):
            result = connector.get_quote("AAPL")

            assert result["symbol"] == "AAPL"
            assert result["price"] == 150.5
            assert result["bid"] == 150.0
            assert result["ask"] == 151.0
            assert result["last_price"] == 150.5
            assert result["bid_size"] == 0
            assert result["ask_size"] == 0

    @pytest.mark.unit
    def test_get_available_symbols_all(self):
        """Test getting all available symbols."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock cache
        connector._symbol_cache = {
            "AAPL": {"market": "equity"},
            "GOOGL": {"market": "equity"},
            "BTC/USD": {"market": "crypto"},
            "ETH/USD": {"market": "crypto"},
        }

        result = connector.get_available_symbols()

        assert set(result) == {"AAPL", "GOOGL", "BTC/USD", "ETH/USD"}

    @pytest.mark.unit
    def test_get_available_symbols_filtered(self):
        """Test getting symbols filtered by market."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock cache
        connector._symbol_cache = {
            "AAPL": {"market": "equity"},
            "GOOGL": {"market": "equity"},
            "BTC/USD": {"market": "crypto"},
            "ETH/USD": {"market": "crypto"},
        }

        # Test equity market filter
        equity_symbols = connector.get_available_symbols(market="equity")
        assert set(equity_symbols) == {"AAPL", "GOOGL"}

        # Test crypto market filter
        crypto_symbols = connector.get_available_symbols(market="crypto")
        assert set(crypto_symbols) == {"BTC/USD", "ETH/USD"}

    @pytest.mark.unit
    def test_get_available_symbols_with_limit(self):
        """Test getting symbols with limit."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock cache
        connector._symbol_cache = {
            "AAPL": {"market": "equity"},
            "GOOGL": {"market": "equity"},
            "MSFT": {"market": "equity"},
            "TSLA": {"market": "equity"},
        }

        result = connector.get_available_symbols(limit=2)

        assert len(result) == 2
        assert result[0] in ["AAPL", "GOOGL", "MSFT", "TSLA"]
        assert result[1] in ["AAPL", "GOOGL", "MSFT", "TSLA"]

    @pytest.mark.unit
    def test_get_symbol_info_success(self):
        """Test getting symbol information successfully."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock cache
        connector._symbol_cache = {
            "AAPL": {"market": "equity", "name": "Apple Inc.", "fractionable": True}
        }

        result = connector.get_symbol_info("AAPL")

        assert result["symbol"] == "AAPL"
        assert result["market"] == "equity"
        assert result["name"] == "Apple Inc."
        assert result["currency"] == "USD"
        assert result["price_precision"] == 2
        assert result["size_precision"] == 0
        assert result["tradable"] is True
        assert result["fractionable"] is True

    @pytest.mark.unit
    def test_get_symbol_info_not_found(self):
        """Test getting symbol info for unknown symbol."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock empty cache
        connector._symbol_cache = {}

        with pytest.raises(SymbolNotFoundError, match="Symbol UNKNOWN not found"):
            connector.get_symbol_info("UNKNOWN")

    @pytest.mark.unit
    def test_get_symbol_info_defaults(self):
        """Test getting symbol info with default values."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock cache with minimal info
        connector._symbol_cache = {"AAPL": {"market": "equity"}}

        result = connector.get_symbol_info("AAPL")

        assert result["symbol"] == "AAPL"
        assert result["name"] == "AAPL"  # Defaults to symbol
        assert result["market"] == "equity"
        assert result["currency"] == "USD"
        assert result["fractionable"] is False  # Default

    @pytest.mark.unit
    def test_is_market_open_crypto(self):
        """Test market status check for crypto (always open)."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        result = connector.is_market_open(market="crypto")
        assert result is True

    @pytest.mark.unit
    def test_is_market_open_equity_unavailable(self):
        """Test market status check when Alpaca unavailable."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", False):
            with pytest.raises(DataSourceError, match="Alpaca library not available"):
                connector.is_market_open(market="equity")

    @pytest.mark.unit
    def test_is_market_open_equity_success(self):
        """Test successful market status check for equity."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            # Mock trading client
            mock_clock = Mock()
            mock_clock.is_open = True
            mock_trading_client = Mock()
            mock_trading_client.get_clock.return_value = mock_clock
            connector.trading_client = mock_trading_client

            result = connector.is_market_open(market="equity")
            assert result is True

    @pytest.mark.unit
    def test_is_market_open_equity_failure(self):
        """Test market status check failure for equity."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            # Mock trading client that raises exception
            mock_trading_client = Mock()
            mock_trading_client.get_clock.side_effect = Exception("Clock API error")
            connector.trading_client = mock_trading_client

            with pytest.raises(DataSourceError, match="Failed to get market status"):
                connector.is_market_open(market="equity")

    @pytest.mark.unit
    def test_is_market_open_equity_no_is_open_attribute(self):
        """Test market status check when clock has no is_open attribute."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            # Mock trading client with clock lacking is_open
            mock_clock = Mock(spec=[])  # No attributes
            mock_trading_client = Mock()
            mock_trading_client.get_clock.return_value = mock_clock
            connector.trading_client = mock_trading_client

            result = connector.is_market_open(market="equity")
            assert result is True  # Should default to True

    @pytest.mark.unit
    def test_is_market_open_default_equity(self):
        """Test market status check with default equity market."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            # Mock trading client
            mock_clock = Mock()
            mock_clock.is_open = False
            mock_trading_client = Mock()
            mock_trading_client.get_clock.return_value = mock_clock
            connector.trading_client = mock_trading_client

            result = (
                connector.is_market_open()
            )  # No market specified, defaults to equity
            assert result is False
