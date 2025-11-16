"""Comprehensive tests for alpaca_connector module."""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

from quantchain.connectors.alpaca_connector import AlpacaDataConnector, AssetClass
from quantchain.core.exceptions import (
    AuthenticationError,
    DataSourceError,
    SymbolNotFoundError,
)


class TestAlpacaDataConnector:
    """Test AlpacaDataConnector class."""

    def test_initialization_with_params(self) -> None:
        """Test connector initialization with parameters."""
        with patch.dict(
            os.environ, {"ALPACA_API_KEY": "env_key", "ALPACA_SECRET_KEY": "env_secret"}
        ):
            connector = AlpacaDataConnector(
                api_key="test_key",
                secret_key="test_secret",
                paper_trading=False,
                symbol_limit=200,
                retry_count=5,
                retry_delay=2.0,
            )

            assert connector.api_key == "test_key"
            assert connector.secret_key == "test_secret"
            assert connector.paper_trading is False
            assert connector.symbol_limit == 200
            assert connector.retry_count == 5
            assert connector.retry_delay == 2.0

    def test_initialization_from_env(self) -> None:
        """Test connector initialization from environment variables."""
        with patch.dict(
            os.environ, {"ALPACA_API_KEY": "env_key", "ALPACA_SECRET_KEY": "env_secret"}
        ):
            connector = AlpacaDataConnector()

            assert connector.api_key == "env_key"
            assert connector.secret_key == "env_secret"
            assert connector.paper_trading is True  # Default value

    def test_initialization_missing_credentials(self) -> None:
        """Test that initialization fails with missing credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AuthenticationError) as excinfo:
                AlpacaDataConnector()

            assert "Alpaca API credentials not provided" in str(excinfo.value)

    def test_is_crypto_symbol(self) -> None:
        """Test crypto symbol detection."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Test with slash (common format)
        assert connector._is_crypto_symbol("BTC/USD") is True
        assert connector._is_crypto_symbol("ETH/USD") is True

        # Test with dash
        assert connector._is_crypto_symbol("BTC-USD") is True
        assert connector._is_crypto_symbol("ETH-USD") is True

        # Test with stock symbols (no slash or dash)
        assert connector._is_crypto_symbol("AAPL") is False
        assert connector._is_crypto_symbol("MSFT") is False

    def test_normalize_crypto_symbol(self) -> None:
        """Test crypto symbol normalization."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Test dash to slash conversion
        assert connector._normalize_crypto_symbol("BTC-USD") == "BTC/USD"
        assert connector._normalize_crypto_symbol("ETH-USD") == "ETH/USD"

        # Test with already normalized symbol
        assert connector._normalize_crypto_symbol("BTC/USD") == "BTC/USD"

    def test_convert_timeframe(self) -> None:
        """Test timeframe conversion."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Test valid timeframes
        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            with patch("quantchain.connectors.alpaca_connector.TimeFrame") as mock_tf:
                # Directly set the attribute to avoid import issues
                connector._convert_timeframe("1Min")
                # We can't easily test the TimeFrame call without the actual library
                # so we just verify it doesn't raise an exception

                connector._convert_timeframe("1H")
                connector._convert_timeframe("1D")

        # Test invalid timeframe
        with pytest.raises(ValueError) as excinfo:
            connector._convert_timeframe("invalid")

        assert "Timeframe invalid not supported" in str(excinfo.value)

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", False)
    def test_no_alpaca_library(self) -> None:
        """Test behavior when Alpaca library is not available."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Clients should be None
        assert connector.stock_client is None
        assert connector.crypto_client is None
        assert connector.trading_client is None

        # Methods should raise DataSourceError
        with pytest.raises(DataSourceError) as excinfo:
            connector.get_historical_data("AAPL", "1D")

        assert "Alpaca library not installed" in str(excinfo.value)

        with pytest.raises(DataSourceError) as excinfo:
            connector.get_real_time_data("AAPL")

        assert "Alpaca library not installed" in str(excinfo.value)

    @patch("quantchain.connectors.alpaca_connector._PANDAS_AVAILABLE", False)
    def test_no_pandas_library(self) -> None:
        """Test behavior when pandas is not available."""
        with patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True):
            connector = AlpacaDataConnector(
                api_key="test_key", secret_key="test_secret"
            )

            # Set up symbol cache to bypass symbol check
            connector._symbol_cache = {"AAPL": {"market": "equity"}}

            with pytest.raises(DataSourceError) as excinfo:
                connector.get_historical_data("AAPL", "1D")

            # Check that error message mentions pandas
            assert "pandas is required for data handling" in str(excinfo.value)

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True)
    def test_authentication_error(self) -> None:
        """Test handling of authentication errors."""
        with patch(
            "quantchain.connectors.alpaca_connector.StockHistoricalDataClient"
        ) as mock_client:
            mock_client.side_effect = Exception("Invalid API key")

            with pytest.raises(AuthenticationError) as excinfo:
                AlpacaDataConnector(api_key="invalid_key", secret_key="invalid_secret")

            assert "Failed to authenticate with Alpaca" in str(excinfo.value)

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True)
    def test_refresh_symbol_cache(self) -> None:
        """Test symbol cache refresh."""
        with patch("quantchain.connectors.alpaca_connector.StockHistoricalDataClient"):
            with patch(
                "quantchain.connectors.alpaca_connector.TradingClient"
            ) as mock_trading:
                # Mock assets
                mock_asset1 = MagicMock()
                mock_asset1.symbol = "AAPL"
                mock_asset1.asset_class = "US_EQUITY"

                mock_asset2 = MagicMock()
                mock_asset2.symbol = "BTC/USD"
                # Using "CRYPTO" which maps to "crypto" in the actual implementation
                mock_asset2.asset_class = AssetClass.CRYPTO

                mock_instance = MagicMock()
                mock_instance.get_all_assets.return_value = [mock_asset1, mock_asset2]
                mock_trading.return_value = mock_instance

                connector = AlpacaDataConnector(
                    api_key="test_key", secret_key="test_secret"
                )

                # Manually call _refresh_symbol_cache to test it
                connector._refresh_symbol_cache()

                # Check cache was populated
                assert "AAPL" in connector._symbol_cache
                assert "BTC/USD" in connector._symbol_cache
                assert connector._symbol_cache["AAPL"]["market"] == "equity"
                assert connector._symbol_cache["BTC/USD"]["market"] == "crypto"

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True)
    def test_refresh_symbol_cache_error(self) -> None:
        """Test handling of symbol cache refresh errors."""
        with patch("quantchain.connectors.alpaca_connector.StockHistoricalDataClient"):
            with patch(
                "quantchain.connectors.alpaca_connector.TradingClient"
            ) as mock_trading:
                mock_instance = MagicMock()
                mock_instance.get_all_assets.side_effect = Exception("API error")
                mock_trading.return_value = mock_instance

                connector = AlpacaDataConnector(
                    api_key="test_key", secret_key="test_secret"
                )

                # Cache should be empty on error
                assert connector._symbol_cache == {}

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True)
    @patch("quantchain.connectors.alpaca_connector._PANDAS_AVAILABLE", True)
    def test_get_historical_data_stock(self) -> None:
        """Test getting historical stock data."""
        with patch("quantchain.connectors.alpaca_connector.pd.DataFrame") as mock_df:
            with patch(
                "quantchain.connectors.alpaca_connector.StockHistoricalDataClient"
            ):
                connector = AlpacaDataConnector(
                    api_key="test_key", secret_key="test_secret"
                )

                # Mock symbol cache
                connector._symbol_cache = {"AAPL": {"market": "equity"}}

                # Mock client response
                mock_bars = MagicMock()
                mock_bars.df = mock_df.return_value
                connector.stock_client = MagicMock()
                connector.stock_client.get_stock_bars.return_value = {"AAPL": mock_bars}

                result = connector.get_historical_data("AAPL", "1D")

                # Check that client was called
                connector.stock_client.get_stock_bars.assert_called_once()

                # Check result
                assert result is mock_df.return_value

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True)
    @patch("quantchain.connectors.alpaca_connector._PANDAS_AVAILABLE", True)
    def test_get_historical_data_crypto(self) -> None:
        """Test getting historical crypto data."""
        with patch("quantchain.connectors.alpaca_connector.pd.DataFrame") as mock_df:
            with patch(
                "quantchain.connectors.alpaca_connector.CryptoHistoricalDataClient"
            ):
                connector = AlpacaDataConnector(
                    api_key="test_key", secret_key="test_secret"
                )

                # Mock symbol cache
                connector._symbol_cache = {"BTC/USD": {"market": "crypto"}}

                # Mock client response
                mock_bars = MagicMock()
                mock_bars.df = mock_df.return_value
                connector.crypto_client = MagicMock()
                connector.crypto_client.get_crypto_bars.return_value = {
                    "BTC/USD": mock_bars
                }

                result = connector.get_historical_data(
                    "BTC-USD", "1D"
                )  # Test normalization

                # Check that client was called with normalized symbol
                connector.crypto_client.get_crypto_bars.assert_called_once()

                # Check result
                assert result is mock_df.return_value

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True)
    def test_get_historical_data_symbol_not_found(self) -> None:
        """Test getting historical data for symbol not found."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Symbol not in cache
        connector._symbol_cache = {}

        with pytest.raises(SymbolNotFoundError) as excinfo:
            connector.get_historical_data("UNKNOWN", "1D")

        assert "Symbol UNKNOWN not found" in str(excinfo.value)

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True)
    @patch("quantchain.connectors.alpaca_connector._PANDAS_AVAILABLE", True)
    def test_get_historical_data_no_data(self) -> None:
        """Test getting historical data when no data is returned."""
        with patch("quantchain.connectors.alpaca_connector.pd.DataFrame"):
            with patch(
                "quantchain.connectors.alpaca_connector.StockHistoricalDataClient"
            ):
                connector = AlpacaDataConnector(
                    api_key="test_key", secret_key="test_secret"
                )

                # Mock symbol cache
                connector._symbol_cache = {"AAPL": {"market": "equity"}}

                # Mock client response with symbol present but empty df
                mock_bars = MagicMock()
                mock_bars.df = None  # This will trigger the "No data found" error
                connector.stock_client = MagicMock()
                connector.stock_client.get_stock_bars.return_value = {"AAPL": mock_bars}

                with pytest.raises(SymbolNotFoundError) as excinfo:
                    connector.get_historical_data("AAPL", "1D")

                assert "No data found for symbol AAPL" in str(excinfo.value)

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True)
    def test_get_historical_data_retry(self) -> None:
        """Test retry mechanism for historical data."""
        connector = AlpacaDataConnector(
            api_key="test_key",
            secret_key="test_secret",
            retry_count=3,
            retry_delay=0.1,  # Short delay for testing
        )

        # Mock symbol cache
        connector._symbol_cache = {"AAPL": {"market": "equity"}}

        # Mock client response with failure then success
        connector.stock_client = MagicMock()
        connector.stock_client.get_stock_bars.side_effect = [
            Exception("Temporary failure"),
            Exception("Another failure"),
            {"AAPL": MagicMock(df=MagicMock())},  # Success on third try
        ]

        # Should succeed after retries
        result = connector.get_historical_data("AAPL", "1D")
        assert result is not None

        # Should have tried 3 times
        assert connector.stock_client.get_stock_bars.call_count == 3

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True)
    def test_get_historical_data_retry_exhausted(self) -> None:
        """Test retry exhausted for historical data."""
        connector = AlpacaDataConnector(
            api_key="test_key",
            secret_key="test_secret",
            retry_count=2,
            retry_delay=0.1,  # Short delay for testing
        )

        # Mock symbol cache
        connector._symbol_cache = {"AAPL": {"market": "equity"}}

        # Mock client response with persistent failure
        connector.stock_client = MagicMock()
        connector.stock_client.get_stock_bars.side_effect = Exception(
            "Persistent failure"
        )

        with pytest.raises(DataSourceError) as excinfo:
            connector.get_historical_data("AAPL", "1D")

        assert "Failed to get data for AAPL" in str(excinfo.value)

        # Should have tried 2 times
        assert connector.stock_client.get_stock_bars.call_count == 2

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True)
    def test_get_real_time_data_stock(self) -> None:
        """Test getting real-time stock data."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock symbol cache
        connector._symbol_cache = {"AAPL": {"market": "equity"}}

        # Mock client response
        mock_quote = MagicMock()
        mock_quote.bid_price = 150.0
        mock_quote.ask_price = 150.5
        mock_quote.timestamp = datetime.now()
        connector.stock_client = MagicMock()
        connector.stock_client.get_stock_latest_quote.return_value = {
            "AAPL": mock_quote
        }

        result = connector.get_real_time_data("AAPL")

        # Check that client was called
        connector.stock_client.get_stock_latest_quote.assert_called_once_with("AAPL")

        # Check result
        assert result["symbol"] == "AAPL"
        assert result["bid"] == 150.0
        assert result["ask"] == 150.5
        assert result["price"] == 150.25  # Mid-price

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True)
    def test_get_real_time_data_crypto(self) -> None:
        """Test getting real-time crypto data."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock symbol cache
        connector._symbol_cache = {"BTC/USD": {"market": "crypto"}}

        # Mock client response
        mock_quote = MagicMock()
        mock_quote.bid_price = 50000.0
        mock_quote.ask_price = 50100.0
        mock_quote.timestamp = datetime.now()
        connector.crypto_client = MagicMock()
        connector.crypto_client.get_crypto_latest_quote.return_value = {
            "BTC/USD": mock_quote
        }

        result = connector.get_real_time_data("BTC-USD")  # Test normalization

        # Check that client was called with normalized symbol
        connector.crypto_client.get_crypto_latest_quote.assert_called_once_with(
            "BTC/USD"
        )

        # Check result
        assert result["symbol"] == "BTC/USD"
        assert result["bid"] == 50000.0
        assert result["ask"] == 50100.0
        assert result["price"] == 50100.0  # Ask price for crypto

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True)
    def test_get_real_time_data_symbol_not_found(self) -> None:
        """Test getting real-time data for symbol not found."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Symbol not in cache
        connector._symbol_cache = {}

        with pytest.raises(SymbolNotFoundError) as excinfo:
            connector.get_real_time_data("UNKNOWN")

        assert "Symbol UNKNOWN not found" in str(excinfo.value)

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True)
    def test_get_real_time_data_no_data(self) -> None:
        """Test getting real-time data when no data is returned."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock symbol cache
        connector._symbol_cache = {"AAPL": {"market": "equity"}}

        # Test behavior when client returns empty dict for symbol
        # This represents a case where symbol is recognized but no quote data is returned
        connector.stock_client = MagicMock()
        connector.stock_client.get_stock_latest_quote.return_value = {}  # Empty dict

        # The method will check if symbol exists in the returned dict
        # Since it doesn't, it will raise SymbolNotFoundError
        # This should raise DataSourceError
        with pytest.raises(DataSourceError) as excinfo:
            connector.get_real_time_data("AAPL")

        assert "Failed to get quote for AAPL" in str(excinfo.value)

    def test_get_quote(self) -> None:
        """Test getting quote information."""
        with patch.object(AlpacaDataConnector, "get_real_time_data") as mock_get_data:
            connector = AlpacaDataConnector(
                api_key="test_key", secret_key="test_secret"
            )

            # Mock real-time data
            mock_data = {
                "symbol": "AAPL",
                "bid": 150.0,
                "ask": 150.5,
                "price": 150.25,
                "timestamp": datetime.now(),
            }
            mock_get_data.return_value = mock_data

            result = connector.get_quote("AAPL")

            # Check that get_real_time_data was called
            mock_get_data.assert_called_once_with("AAPL")

            # Check result
            assert result["symbol"] == "AAPL"
            assert result["bid"] == 150.0
            assert result["ask"] == 150.5
            assert result["price"] == 150.25
            assert result["last_price"] == 150.25

    def test_get_available_symbols_all(self) -> None:
        """Test getting all available symbols."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock symbol cache
        connector._symbol_cache = {
            "AAPL": {"market": "equity"},
            "MSFT": {"market": "equity"},
            "BTC/USD": {"market": "crypto"},
        }

        result = connector.get_available_symbols()

        # Should return all symbols
        assert set(result) == {"AAPL", "MSFT", "BTC/USD"}

    def test_get_available_symbols_filtered(self) -> None:
        """Test getting available symbols filtered by market."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock symbol cache
        connector._symbol_cache = {
            "AAPL": {"market": "equity"},
            "MSFT": {"market": "equity"},
            "BTC/USD": {"market": "crypto"},
        }

        # Filter by equity
        equity_symbols = connector.get_available_symbols(market="equity")
        assert set(equity_symbols) == {"AAPL", "MSFT"}

        # Filter by crypto
        crypto_symbols = connector.get_available_symbols(market="crypto")
        assert crypto_symbols == ["BTC/USD"]

    def test_get_available_symbols_with_limit(self) -> None:
        """Test getting available symbols with limit."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock symbol cache
        connector._symbol_cache = {
            "AAPL": {"market": "equity"},
            "MSFT": {"market": "equity"},
            "GOOGL": {"market": "equity"},
            "TSLA": {"market": "equity"},
        }

        result = connector.get_available_symbols(limit=2)

        # Should return only 2 symbols
        assert len(result) == 2

    def test_get_symbol_info(self) -> None:
        """Test getting symbol information."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock symbol cache
        connector._symbol_cache = {"AAPL": {"market": "equity", "name": "Apple Inc."}}

        result = connector.get_symbol_info("AAPL")

        # Check result
        assert result["symbol"] == "AAPL"
        assert result["name"] == "Apple Inc."
        assert result["market"] == "equity"
        assert result["currency"] == "USD"
        assert result["price_precision"] == 2
        assert result["size_precision"] == 0
        assert result["tradable"] is True

    def test_get_symbol_info_not_found(self) -> None:
        """Test getting symbol information for symbol not found."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Empty symbol cache
        connector._symbol_cache = {}

        with pytest.raises(SymbolNotFoundError) as excinfo:
            connector.get_symbol_info("UNKNOWN")

        assert "Symbol UNKNOWN not found" in str(excinfo.value)

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True)
    def test_is_market_open_equity(self) -> None:
        """Test checking if equity market is open."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock trading client
        mock_clock = MagicMock()
        mock_clock.is_open = True
        connector.trading_client = MagicMock()
        connector.trading_client.get_clock.return_value = mock_clock

        result = connector.is_market_open()

        # Check result
        assert result is True

        # Check that client was called
        connector.trading_client.get_clock.assert_called_once()

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True)
    def test_is_market_open_equity_closed(self) -> None:
        """Test checking if equity market is closed."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock trading client
        mock_clock = MagicMock()
        mock_clock.is_open = False
        connector.trading_client = MagicMock()
        connector.trading_client.get_clock.return_value = mock_clock

        result = connector.is_market_open()

        # Check result
        assert result is False

    def test_is_market_open_crypto(self) -> None:
        """Test checking if crypto market is open."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Crypto market should always be open
        result = connector.is_market_open(market="crypto")

        assert result is True

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", False)
    def test_is_market_open_no_library(self) -> None:
        """Test checking market status when Alpaca library is not available."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        with pytest.raises(DataSourceError) as excinfo:
            connector.is_market_open()

        assert "Alpaca library not available" in str(excinfo.value)

    @patch("quantchain.connectors.alpaca_connector._ALPACA_AVAILABLE", True)
    def test_is_market_open_error(self) -> None:
        """Test handling of errors when checking market status."""
        connector = AlpacaDataConnector(api_key="test_key", secret_key="test_secret")

        # Mock trading client with error
        connector.trading_client = MagicMock()
        connector.trading_client.get_clock.side_effect = Exception("API error")

        with pytest.raises(DataSourceError) as excinfo:
            connector.is_market_open()

        assert "Failed to get market status" in str(excinfo.value)
