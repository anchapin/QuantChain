"""Tests for Alpaca data connector."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import pandas as pd

from quantchain.connectors.alpaca_connector import AlpacaDataConnector
from quantchain.core.exceptions import (
    DataSourceError,
    SymbolNotFoundError,
    AuthenticationError,
)
from alpaca.trading.enums import AssetClass


class TestAlpacaDataConnector:
    """Test suite for AlpacaDataConnector."""

    @pytest.fixture
    def connector(self) -> None:
        """Create a test connector instance."""
        return AlpacaDataConnector("test_key", "test_secret")

    @pytest.fixture
    def sample_stock_bar(self) -> None:
        """Sample stock bar data."""
        return MagicMock(
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            open=150.0,
            high=155.0,
            low=149.0,
            close=153.0,
            volume=1000000,
        )

    @pytest.fixture
    def sample_crypto_bar(self) -> None:
        """Sample crypto bar data."""
        return MagicMock(
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            open=50000.0,
            high=51000.0,
            low=49500.0,
            close=50500.0,
            volume=100.0,
        )

    @pytest.fixture
    def sample_quote(self) -> None:
        """Sample quote data."""
        return MagicMock(
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            bid_price=152.0,
            ask_price=153.0,
            bid_size=100,
            ask_size=200,
        )

    def test_initialization_success(self) -> None:
        """Test successful initialization."""
        with patch(
            "quantchain.connectors.alpaca_connector.StockHistoricalDataClient"
        ), patch(
            "quantchain.connectors.alpaca_connector.CryptoHistoricalDataClient"
        ), patch(
            "quantchain.connectors.alpaca_connector.TradingClient"
        ):
            connector = AlpacaDataConnector("key", "secret")
            assert connector.api_key == "key"
            assert connector.api_secret == "secret"

    def test_initialization_auth_failure(self) -> None:
        """Test initialization failure due to auth error."""
        with patch(
            "quantchain.connectors.alpaca_connector.StockHistoricalDataClient",
            side_effect=Exception("Auth failed"),
        ):
            with pytest.raises(AuthenticationError):
                AlpacaDataConnector("bad_key", "bad_secret")

    def test_is_crypto_symbol(self, connector: AlpacaDataConnector) -> None:
        """Test crypto symbol detection."""
        assert connector._is_crypto_symbol("BTC/USD") is True
        assert connector._is_crypto_symbol("BTC-USD") is True
        assert connector._is_crypto_symbol("AAPL") is False

    def test_normalize_crypto_symbol(self, connector: AlpacaDataConnector) -> None:
        """Test crypto symbol normalization."""
        assert connector._normalize_crypto_symbol("BTC/USD") == "BTC/USD"
        assert connector._normalize_crypto_symbol("BTC-USD") == "BTC/USD"

    def test_convert_timeframe(self, connector: AlpacaDataConnector) -> None:
        """Test timeframe conversion."""
        from alpaca.data import TimeFrame

        timeframe_1min = connector._convert_timeframe("1Min")
        timeframe_1d = connector._convert_timeframe("1D")

        assert timeframe_1min.amount == TimeFrame.Minute.amount
        assert timeframe_1min.unit == TimeFrame.Minute.unit
        assert timeframe_1d.amount == TimeFrame.Day.amount
        assert timeframe_1d.unit == TimeFrame.Day.unit

        with pytest.raises(ValueError):
            connector._convert_timeframe("invalid")

    def test_refresh_symbol_cache(self, connector: AlpacaDataConnector) -> None:
        """Test symbol cache refresh."""
        with patch.object(
            connector.trading_client, "get_all_assets"
        ) as mock_get_assets:
            mock_asset = MagicMock()
            mock_asset.symbol = "AAPL"
            mock_asset.name = "Apple Inc"
            mock_asset.asset_class = AssetClass.US_EQUITY
            mock_asset.min_order_size = 1
            mock_asset.max_order_size = None
            mock_asset.tradable = True
            mock_asset.fractionable = True

            mock_get_assets.return_value = [mock_asset]

            connector._refresh_symbol_cache()

            assert "AAPL" in connector._symbol_cache
            assert connector._symbol_cache["AAPL"]["market"] == "equity"

    def test_get_historical_data_stock(
        self, connector: AlpacaDataConnector, sample_stock_bar
    ) -> None:
        """Test historical data retrieval for stocks."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, tzinfo=timezone.utc)

        with patch.object(connector.stock_client, "get_stock_bars") as mock_get_bars:
            mock_bars = MagicMock()
            mock_bars.__contains__ = MagicMock(
                return_value=True
            )  # Mock __contains__ for "AAPL" in bars
            mock_bars.__getitem__.return_value = [sample_stock_bar]
            mock_get_bars.return_value = mock_bars

            df = connector.get_historical_data("AAPL", "1D", start_date, end_date)

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 1
            assert df.iloc[0]["close"] == 153.0
            assert df.iloc[0]["volume"] == 1000000

    def test_get_historical_data_crypto(
        self, connector: AlpacaDataConnector, sample_crypto_bar
    ) -> None:
        """Test historical data retrieval for crypto."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, tzinfo=timezone.utc)

        with patch.object(connector.crypto_client, "get_crypto_bars") as mock_get_bars:
            mock_bars = MagicMock()
            mock_bars.__contains__ = MagicMock(
                return_value=True
            )  # Mock __contains__ for "BTC/USD" in bars
            mock_bars.__getitem__.return_value = [sample_crypto_bar]
            mock_get_bars.return_value = mock_bars

            df = connector.get_historical_data("BTC/USD", "1D", start_date, end_date)

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 1
            assert df.iloc[0]["close"] == 50500.0

    def test_get_historical_data_symbol_not_found(
        self, connector: AlpacaDataConnector
    ) -> None:
        """Test historical data retrieval for non-existent symbol."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

        with patch.object(connector.stock_client, "get_stock_bars") as mock_get_bars:
            mock_bars = MagicMock()
            mock_bars.__getitem__.return_value = []
            mock_get_bars.return_value = mock_bars

            with pytest.raises(SymbolNotFoundError):
                connector.get_historical_data("INVALID", "1D", start_date)

    def test_get_real_time_data_stock(self, connector: AlpacaDataConnector) -> None:
        """Test real-time data retrieval for stocks."""
        with patch.object(
            connector.stock_client, "get_stock_latest_quote"
        ) as mock_get_quote:
            mock_quotes = MagicMock()
            mock_quote = MagicMock()
            mock_quote.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_quote.bid_price = 152.0
            mock_quote.ask_price = 153.0
            mock_quotes.__getitem__.return_value = mock_quote
            mock_get_quote.return_value = mock_quotes

            data = connector.get_real_time_data("AAPL")

            assert data["price"] == 152.5  # Average of bid/ask
            assert data["bid"] == 152.0
            assert data["ask"] == 153.0

    def test_get_real_time_data_crypto(self, connector: AlpacaDataConnector) -> None:
        """Test real-time data retrieval for crypto."""
        with patch.object(
            connector.crypto_client, "get_crypto_latest_quote"
        ) as mock_get_quote:
            mock_quotes = MagicMock()
            mock_quote = MagicMock()
            mock_quote.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_quote.bid_price = 50000.0
            mock_quote.ask_price = 50100.0
            mock_quotes.__getitem__.return_value = mock_quote
            mock_get_quote.return_value = mock_quotes

            data = connector.get_real_time_data("BTC/USD")

            assert data["price"] == 50100.0  # Uses ask price for crypto
            assert data["bid"] == 50000.0
            assert data["ask"] == 50100.0

    def test_get_quote_stock(self, connector: AlpacaDataConnector) -> None:
        """Test quote retrieval for stocks."""
        with patch.object(
            connector.stock_client, "get_stock_latest_quote"
        ) as mock_get_quote:
            mock_quotes = MagicMock()
            mock_quote = MagicMock()
            mock_quote.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_quote.bid_price = 152.0
            mock_quote.ask_price = 153.0
            mock_quote.bid_size = 100
            mock_quote.ask_size = 200
            mock_quotes.__getitem__.return_value = mock_quote
            mock_get_quote.return_value = mock_quotes

            quote = connector.get_quote("AAPL")

            assert quote["symbol"] == "AAPL"
            assert quote["bid_price"] == 152.0
            assert quote["ask_price"] == 153.0
            assert quote["last_price"] == 152.5

    def test_get_available_symbols(self, connector: AlpacaDataConnector) -> None:
        """Test getting available symbols."""
        with patch.object(connector, "_refresh_symbol_cache"):
            connector._symbol_cache = {
                "AAPL": {"market": "equity"},
                "BTC/USD": {"market": "crypto"},
                "ETH/USD": {"market": "crypto"},
            }

            # Test all symbols
            symbols = connector.get_available_symbols()
            assert len(symbols) == 3

            # Test equity filter
            equity_symbols = connector.get_available_symbols("equity")
            assert "AAPL" in equity_symbols
            assert len(equity_symbols) == 1

            # Test crypto filter
            crypto_symbols = connector.get_available_symbols("crypto")
            assert "BTC/USD" in crypto_symbols
            assert len(crypto_symbols) == 2

    def test_get_symbol_info(self, connector: AlpacaDataConnector) -> None:
        """Test getting symbol information."""
        with patch.object(connector, "_refresh_symbol_cache"):
            connector._symbol_cache = {
                "AAPL": {
                    "symbol": "AAPL",
                    "name": "Apple Inc",
                    "market": "equity",
                    "currency": "USD",
                    "min_order_size": 1,
                    "max_order_size": None,
                    "price_precision": 2,
                    "size_precision": 0,
                    "tradable": True,
                    "fractionable": True,
                }
            }

            info = connector.get_symbol_info("AAPL")

            assert info["symbol"] == "AAPL"
            assert info["name"] == "Apple Inc"
            assert info["market"] == "equity"
            assert info["price_precision"] == 2

    def test_get_symbol_info_not_found(self, connector: AlpacaDataConnector) -> None:
        """Test getting symbol info for non-existent symbol."""
        with patch.object(connector, "_refresh_symbol_cache"):
            connector._symbol_cache = {}

            with pytest.raises(SymbolNotFoundError):
                connector.get_symbol_info("INVALID")

    def test_is_market_open_equity(self, connector: AlpacaDataConnector) -> None:
        """Test market open check for equity."""
        with patch.object(connector.trading_client, "get_clock") as mock_get_clock:
            mock_clock = MagicMock()
            mock_clock.is_open = True
            mock_get_clock.return_value = mock_clock

            assert connector.is_market_open() is True
            assert connector.is_market_open("equity") is True

    def test_is_market_open_crypto(self, connector: AlpacaDataConnector) -> None:
        """Test market open check for crypto."""
        # Crypto markets are always open without making API calls
        # Check the logic directly in the implementation
        assert connector.is_market_open("crypto") is True

    def test_is_market_open_error(self, connector: AlpacaDataConnector) -> None:
        """Test market open check error handling."""
        with patch.object(
            connector.trading_client, "get_clock", side_effect=Exception("API Error")
        ):
            with pytest.raises(DataSourceError):
                connector.is_market_open()

    @patch("quantchain.connectors.alpaca_connector.StockHistoricalDataClient")
    @patch("quantchain.connectors.alpaca_connector.CryptoHistoricalDataClient")
    @patch("quantchain.connectors.alpaca_connector.TradingClient")
    def test_paper_trading_config(
        self, mock_trading, mock_stock_client, mock_crypto_client
    ) -> None:
        """Test paper trading configuration."""
        connector = AlpacaDataConnector("key", "secret", use_paper=True)
        assert connector.use_paper is True

        # Check that TradingClient was called with paper=True
        mock_trading.assert_called_with("key", "secret", paper=True)
