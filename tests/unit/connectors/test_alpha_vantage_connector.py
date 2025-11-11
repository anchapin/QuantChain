"""Tests for Alpha Vantage data connector."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from quantchain.connectors.alpha_vantage_connector import AlphaVantageDataConnector
from quantchain.core.exceptions import (
    AuthenticationError,
    DataSourceError,
    RateLimitError,
    SymbolNotFoundError,
)


@pytest.mark.unit
class TestAlphaVantageDataConnector:
    """Test suite for AlphaVantageDataConnector."""

    @pytest.fixture
    def connector(self) -> AlphaVantageDataConnector:
        """Create a test connector instance."""
        return AlphaVantageDataConnector("TEST123456789ABC")

    @pytest.fixture
    def sample_intraday_response(self) -> dict:
        """Sample Alpha Vantage TIME_SERIES_INTRADAY response."""
        return {
            "Meta Data": {
                "1. Information": "Intraday (1min) open, high, low, close prices",
                "2. Symbol": "AAPL",
                "3. Last Refreshed": "2024-01-01 16:00:00",
                "4. Interval": "1min",
                "5. Output Size": "Compact",
                "6. Time Zone": "US/Eastern",
            },
            "Time Series (1min)": {
                "2024-01-01 16:00:00": {
                    "1. open": "150.00",
                    "2. high": "151.00",
                    "3. low": "149.50",
                    "4. close": "150.75",
                    "5. volume": "1000",
                },
                "2024-01-01 15:59:00": {
                    "1. open": "149.50",
                    "2. high": "150.25",
                    "3. low": "149.25",
                    "4. close": "149.95",
                    "5. volume": "800",
                },
            },
        }

    @pytest.fixture
    def sample_daily_response(self) -> dict:
        """Sample Alpha Vantage TIME_SERIES_DAILY response."""
        return {
            "Meta Data": {
                "1. Information": "Daily Prices and Volumes",
                "2. Symbol": "AAPL",
                "3. Last Refreshed": "2024-01-01",
                "4. Output Size": "Compact",
                "5. Time Zone": "US/Eastern",
            },
            "Time Series (Daily)": {
                "2024-01-01": {
                    "1. open": "150.00",
                    "2. high": "152.00",
                    "3. low": "148.50",
                    "4. close": "151.75",
                    "5. volume": "50000",
                },
                "2023-12-29": {
                    "1. open": "148.00",
                    "2. high": "150.50",
                    "3. low": "147.75",
                    "4. close": "149.95",
                    "5. volume": "45000",
                },
            },
        }

    @pytest.fixture
    def sample_quote_response(self) -> dict:
        """Sample Alpha Vantage GLOBAL_QUOTE response."""
        return {
            "Global Quote": {
                "01. symbol": "AAPL",
                "02. price": "150.75",
                "03. change": "+1.25",
                "04. change_percent": "+0.84%",
                "05. volume": "100000",
                "06. last_trade_day": "2024-01-01",
                "07. previous_close": "149.50",
                "08. change": "1.25",
            }
        }

    @pytest.fixture
    def sample_fx_response(self) -> dict:
        """Sample Alpha Vantage CURRENCY_EXCHANGE_RATE response."""
        return {
            "Realtime Currency Exchange Rate": {
                "1. From_Currency Code": "EUR",
                "2. From_Currency Name": "Euro",
                "3. To_Currency Code": "USD",
                "4. To_Currency Name": "United States Dollar",
                "5. Exchange Rate": "1.0950",
                "6. Last Refreshed": "2024-01-01 12:00:00",
                "7. Time Zone": "UTC",
            }
        }

    @pytest.fixture
    def sample_symbol_search_response(self) -> dict:
        """Sample Alpha Vantage SYMBOL_SEARCH response."""
        return {
            "bestMatches": [
                {
                    "1. symbol": "AAPL",
                    "2. name": "Apple Inc.",
                    "3. type": "Equity",
                    "4. region": "United States",
                    "5. marketOpen": "09:30",
                    "6. marketClose": "16:00",
                    "7. timezone": "UTC-04",
                    "8. currency": "USD",
                    "9. matchScore": "1.0000",
                }
            ]
        }

    @pytest.fixture
    def sample_market_status_response(self) -> dict:
        """Sample Alpha Vantage MARKET_STATUS response."""
        return {
            "market_status": [
                {
                    "market": "Equity",
                    "region": "United States",
                    "current_status": "open",
                    "notes": "Market is open",
                }
            ]
        }

    def test_initialization_success(self) -> None:
        """Test successful initialization."""
        connector = AlphaVantageDataConnector("TEST123456789ABC")
        assert connector.api_key == "TEST123456789ABC"
        assert connector.timeout == 30
        assert connector.max_retries == 3
        assert connector.cache_ttl == 3600

    def test_initialization_with_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        connector = AlphaVantageDataConnector(
            "TEST123456789ABC",
            timeout=60,
            max_retries=5,
            cache_ttl=7200,
            symbol_limit=200,
        )
        assert connector.timeout == 60
        assert connector.max_retries == 5
        assert connector.cache_ttl == 7200
        assert connector.symbol_limit == 200

    def test_initialization_invalid_key_format(self) -> None:
        """Test initialization with invalid API key format."""
        with pytest.raises(ValueError):
            AlphaVantageDataConnector("invalid_key")

    def test_is_forex_symbol(self, connector: AlphaVantageDataConnector) -> None:
        """Test forex symbol detection."""
        assert connector._is_forex_symbol("EUR/USD") is True
        assert connector._is_forex_symbol("GBP/JPY") is True
        assert connector._is_forex_symbol("AAPL") is False
        assert connector._is_forex_symbol("BTC-USD") is False

    def test_parse_forex_symbol(self, connector: AlphaVantageDataConnector) -> None:
        """Test forex symbol parsing."""
        base, quote = connector._parse_forex_symbol("EUR/USD")
        assert base == "EUR"
        assert quote == "USD"

        base, quote = connector._parse_forex_symbol("GBP/JPY")
        assert base == "GBP"
        assert quote == "JPY"

    def test_parse_forex_symbol_invalid(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test parsing invalid forex symbol."""
        with pytest.raises(ValueError):
            connector._parse_forex_symbol("INVALID")

        with pytest.raises(ValueError):
            connector._parse_forex_symbol("EUR/USD/JPY")

    def test_convert_timeframe_intraday(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test timeframe conversion for intraday."""
        function, interval = connector._convert_timeframe("1Min", False)
        assert function == "TIME_SERIES_INTRADAY"
        assert interval == "1min"

        function, interval = connector._convert_timeframe("5Min", False)
        assert function == "TIME_SERIES_INTRADAY"
        assert interval == "5min"

        function, interval = connector._convert_timeframe("1H", False)
        assert function == "TIME_SERIES_INTRADAY"
        assert interval == "60min"

    def test_convert_timeframe_daily(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test timeframe conversion for daily."""
        function, interval = connector._convert_timeframe("1D", False)
        assert function == "TIME_SERIES_DAILY"
        assert interval is None

        function, interval = connector._convert_timeframe("1W", False)
        assert function == "TIME_SERIES_WEEKLY"
        assert interval is None

        function, interval = connector._convert_timeframe("1M", False)
        assert function == "TIME_SERIES_MONTHLY"
        assert interval is None

    def test_convert_timeframe_forex(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test timeframe conversion for forex."""
        function, interval = connector._convert_timeframe("1D", True)
        assert function == "FX_DAILY"
        assert interval is None

        function, interval = connector._convert_timeframe("1H", True)
        assert function == "FX_INTRADAY"
        assert interval == "60min"

    def test_convert_timeframe_invalid(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test invalid timeframe conversion."""
        with pytest.raises(ValueError):
            connector._convert_timeframe("1Y", False)

        with pytest.raises(ValueError):
            connector._convert_timeframe("invalid", False)

    def test_make_request_success(self, connector: AlphaVantageDataConnector) -> None:
        """Test successful API request."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"test": "data"}

        with patch.object(connector.session, "get", return_value=mock_response):
            result = connector._make_request({"function": "TEST"})
            assert result == {"test": "data"}

    def test_make_request_auth_error(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test request with authentication error."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"Error Message": "Invalid API key"}

        with patch.object(connector.session, "get", return_value=mock_response):
            with pytest.raises(AuthenticationError):
                connector._make_request({"function": "TEST"})

    def test_make_request_rate_limit(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test request with rate limit error."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"Note": "API call frequency is too high"}

        with patch.object(connector.session, "get", return_value=mock_response):
            with pytest.raises(RateLimitError):
                connector._make_request({"function": "TEST"})

    def test_parse_time_series_data(self, connector: AlphaVantageDataConnector) -> None:
        """Test parsing time series data."""
        data = {
            "Time Series (1min)": {
                "2024-01-01 16:00:00": {
                    "1. open": "150.00",
                    "2. high": "151.00",
                    "3. low": "149.50",
                    "4. close": "150.75",
                    "5. volume": "1000",
                },
                "2024-01-01 15:59:00": {
                    "1. open": "149.50",
                    "2. high": "150.25",
                    "3. low": "149.25",
                    "4. close": "149.95",
                    "5. volume": "800",
                },
            }
        }

        df = connector._parse_time_series_data(data, "Time Series (1min)")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
        # Check that data is sorted by timestamp (earlier first)
        assert df.iloc[0]["open"] == 149.50  # 15:59:00 data (earlier)
        assert df.iloc[1]["open"] == 150.00  # 16:00:00 data (later)
        assert df.iloc[1]["close"] == 150.75
        assert df.iloc[1]["volume"] == 1000

    def test_get_historical_data_equity_intraday(
        self, connector: AlphaVantageDataConnector, sample_intraday_response
    ) -> None:
        """Test getting historical equity intraday data."""
        start_date = datetime(2024, 1, 1)

        with patch.object(
            connector, "_make_request", return_value=sample_intraday_response
        ):
            df = connector.get_historical_data("AAPL", "1Min", start_date)

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
            assert list(df.columns) == [
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]

    def test_get_historical_data_equity_daily(
        self, connector: AlphaVantageDataConnector, sample_daily_response
    ) -> None:
        """Test getting historical equity daily data."""
        start_date = datetime(2024, 1, 1)

        with patch.object(
            connector, "_make_request", return_value=sample_daily_response
        ):
            df = connector.get_historical_data("AAPL", "1D", start_date)

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
            # Data sorted by timestamp (earlier first)
            assert df.iloc[0]["open"] == 148.00  # 2023-12-29
            assert df.iloc[1]["open"] == 150.00  # 2024-01-01
            assert df.iloc[1]["close"] == 151.75

    def test_get_historical_data_forex_daily(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test getting historical forex daily data."""
        start_date = datetime(2024, 1, 1)
        fx_response = {
            "Time Series FX (Daily)": {
                "2024-01-01": {
                    "1. open": "1.0900",
                    "2. high": "1.1000",
                    "3. low": "1.0850",
                    "4. close": "1.0950",
                },
                "2023-12-29": {
                    "1. open": "1.0850",
                    "2. high": "1.0950",
                    "3. low": "1.0800",
                    "4. close": "1.0900",
                },
            }
        }

        with patch.object(connector, "_make_request", return_value=fx_response):
            df = connector.get_historical_data("EUR/USD", "1D", start_date)

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
            # Data sorted by timestamp (earlier first)
            assert df.iloc[0]["open"] == 1.085  # 2023-12-29
            assert df.iloc[1]["open"] == 1.090  # 2024-01-010
            assert df.iloc[1]["close"] == 1.0950  # 2024-01-01

    def test_get_historical_data_symbol_not_found(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test historical data with symbol not found."""
        start_date = datetime(2024, 1, 1)

        with patch.object(
            connector, "_make_request", return_value={"Error Message": "Invalid symbol"}
        ):
            with pytest.raises(SymbolNotFoundError):
                connector.get_historical_data("INVALID", "1D", start_date)

    def test_get_historical_data_rate_limit(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test historical data with rate limit."""
        start_date = datetime(2024, 1, 1)

        with patch.object(
            connector,
            "_make_request",
            side_effect=RateLimitError("Rate limit exceeded"),
        ):
            with pytest.raises(RateLimitError):
                connector.get_historical_data("AAPL", "1D", start_date)

    def test_get_historical_data_invalid_timeframe(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test historical data with invalid timeframe."""
        start_date = datetime(2024, 1, 1)

        with pytest.raises(ValueError):
            connector.get_historical_data("AAPL", "invalid", start_date)

    def test_get_real_time_data_equity(
        self, connector: AlphaVantageDataConnector, sample_quote_response
    ) -> None:
        """Test getting real-time equity data."""
        with patch.object(
            connector, "_make_request", return_value=sample_quote_response
        ):
            data = connector.get_real_time_data("AAPL")

            assert data["price"] == 150.75
            assert "timestamp" in data

    def test_get_real_time_data_forex(
        self, connector: AlphaVantageDataConnector, sample_fx_response
    ) -> None:
        """Test getting real-time forex data."""
        with patch.object(connector, "_make_request", return_value=sample_fx_response):
            data = connector.get_real_time_data("EUR/USD")

            assert data["price"] == 1.0950
            assert "timestamp" in data

    def test_get_real_time_data_symbol_not_found(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test real-time data with symbol not found."""
        with patch.object(
            connector, "_make_request", return_value={"Error Message": "Invalid symbol"}
        ):
            with pytest.raises(SymbolNotFoundError):
                connector.get_real_time_data("INVALID")

    def test_get_real_time_data_api_error(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test real-time data with API error."""
        with patch.object(
            connector, "_make_request", side_effect=DataSourceError("API error")
        ):
            with pytest.raises(DataSourceError):
                connector.get_real_time_data("AAPL")

    def test_get_quote_equity(
        self, connector: AlphaVantageDataConnector, sample_quote_response
    ) -> None:
        """Test getting equity quote."""
        with patch.object(
            connector, "_make_request", return_value=sample_quote_response
        ):
            quote = connector.get_quote("AAPL")

            assert quote["symbol"] == "AAPL"
            assert quote["last_price"] == 150.75
            assert "timestamp" in quote
            assert "bid_price" in quote
            assert "ask_price" in quote

    def test_get_quote_forex(
        self, connector: AlphaVantageDataConnector, sample_fx_response
    ) -> None:
        """Test getting forex quote."""
        with patch.object(connector, "_make_request", return_value=sample_fx_response):
            quote = connector.get_quote("EUR/USD")

            assert quote["symbol"] == "EUR/USD"
            assert quote["last_price"] == 1.0950
            assert "timestamp" in quote

    def test_get_quote_missing_symbol(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test getting quote for missing symbol."""
        with patch.object(
            connector, "_make_request", return_value={"Error Message": "Invalid symbol"}
        ):
            with pytest.raises(SymbolNotFoundError):
                connector.get_quote("INVALID")

    def test_get_available_symbols_all(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test getting all available symbols."""
        connector._symbol_cache: list[float] = ["AAPL", "GOOGL", "EUR/USD", "GBP/JPY"]
        connector._cache_timestamp = datetime.now().timestamp()

        symbols = connector.get_available_symbols()

        assert len(symbols) == 4
        assert "AAPL" in symbols
        assert "EUR/USD" in symbols

    def test_get_available_symbols_equity_filter(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test getting available equity symbols."""
        connector._symbol_cache: list[float] = ["AAPL", "GOOGL", "EUR/USD", "GBP/JPY"]
        connector._cache_timestamp = datetime.now().timestamp()

        symbols = connector.get_available_symbols(market="equity")

        assert "AAPL" in symbols
        assert "GOOGL" in symbols
        assert "EUR/USD" not in symbols
        assert "GBP/JPY" not in symbols

    def test_get_available_symbols_forex_filter(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test getting available forex symbols."""
        connector._symbol_cache: list[float] = ["AAPL", "GOOGL", "EUR/USD", "GBP/JPY"]
        connector._cache_timestamp = datetime.now().timestamp()

        symbols = connector.get_available_symbols(market="forex")

        assert "AAPL" not in symbols
        assert "GOOGL" not in symbols
        assert "EUR/USD" in symbols
        assert "GBP/JPY" in symbols

    def test_get_available_symbols_with_limit(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test getting available symbols with limit."""
        connector._symbol_cache: list[float] = [
            "AAPL",
            "GOOGL",
            "MSFT",
            "EUR/USD",
            "GBP/JPY",
        ]
        connector._cache_timestamp = datetime.now().timestamp()
        connector.symbol_limit = 3

        symbols = connector.get_available_symbols()

        assert len(symbols) == 3

    def test_get_available_symbols_cache_refresh(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test cache refresh in get_available_symbols."""
        # Set expired cache
        connector._cache_timestamp = (
            datetime.now().timestamp() - connector.cache_ttl - 100
        )

        with patch.object(connector, "_refresh_symbol_cache") as mock_refresh:
            connector.get_available_symbols()
            mock_refresh.assert_called_once()

    def test_get_symbol_info_equity(
        self, connector: AlphaVantageDataConnector, sample_symbol_search_response
    ) -> None:
        """Test getting equity symbol info."""
        with patch.object(
            connector, "_make_request", return_value=sample_symbol_search_response
        ):
            info = connector.get_symbol_info("AAPL")

            assert info["symbol"] == "AAPL"
            assert info["name"] == "Apple Inc."
            assert info["market"] == "equity"
            assert info["currency"] == "USD"
            assert info["price_precision"] == 2
            assert info["size_precision"] == 0

    def test_get_symbol_info_forex(self, connector: AlphaVantageDataConnector) -> None:
        """Test getting forex symbol info."""
        fx_response = {
            "bestMatches": [
                {
                    "1. symbol": "EUR/USD",
                    "2. name": "EUR/USD",
                    "3. type": "Digital Currency",
                    "4. region": "Global",
                    "9. matchScore": "1.0000",
                }
            ]
        }

        with patch.object(connector, "_make_request", return_value=fx_response):
            info = connector.get_symbol_info("EUR/USD")

            assert info["symbol"] == "EUR/USD"
            assert info["market"] == "forex"
            assert info["price_precision"] == 4
            assert info["size_precision"] == 8

    def test_get_symbol_info_not_found(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test getting symbol info for non-existent symbol."""
        with patch.object(connector, "_make_request", return_value={"bestMatches": []}):
            with pytest.raises(SymbolNotFoundError):
                connector.get_symbol_info("INVALID")

    def test_get_symbol_info_cache_hit(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test cached symbol info retrieval."""
        cached_info = {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "market": "equity",
            "currency": "USD",
            "min_order_size": 1,
            "max_order_size": None,
            "price_precision": 2,
            "size_precision": 0,
        }
        connector._symbol_info_cache = {"AAPL": cached_info}
        connector._cache_timestamp = datetime.now().timestamp()

        info = connector.get_symbol_info("AAPL")

        assert info == cached_info

    def test_is_market_open_equity_open(
        self, connector: AlphaVantageDataConnector, sample_market_status_response
    ) -> None:
        """Test checking if equity market is open."""
        with patch.object(
            connector, "_make_request", return_value=sample_market_status_response
        ):
            is_open = connector.is_market_open("equity")
            assert is_open is True

    def test_is_market_open_equity_closed(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test checking if equity market is closed."""
        closed_response = {
            "market_status": [
                {
                    "market": "Equity",
                    "region": "United States",
                    "current_status": "closed",
                }
            ]
        }

        with patch.object(connector, "_make_request", return_value=closed_response):
            is_open = connector.is_market_open("equity")
            assert is_open is False

    def test_is_market_open_forex(self, connector: AlphaVantageDataConnector) -> None:
        """Test checking if forex market is open (always returns True)."""
        is_open = connector.is_market_open("forex")
        assert is_open is True

    def test_is_market_open_api_error(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test market status check with API error."""
        with patch.object(
            connector, "_make_request", side_effect=DataSourceError("API error")
        ):
            with pytest.raises(DataSourceError):
                connector.is_market_open("equity")

    def test_authentication_error(self, connector: AlphaVantageDataConnector) -> None:
        """Test authentication error handling."""
        with patch.object(connector.session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"Error Message": "Invalid API key"}
            mock_get.return_value = mock_response

            with pytest.raises(AuthenticationError):
                connector._make_request({"function": "TEST"})

    def test_rate_limit_error_detection(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test rate limit error detection."""
        with patch.object(connector.session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"Note": "API call frequency is too high"}
            mock_get.return_value = mock_response

            with pytest.raises(RateLimitError):
                connector._make_request({"function": "TEST"})

    def test_network_error_retry(self, connector: AlphaVantageDataConnector) -> None:
        """Test retry logic on network error."""
        with patch.object(connector.session, "get") as mock_get:
            mock_get.side_effect = [
                requests.exceptions.RequestException("Network error"),
                requests.exceptions.RequestException("Network error"),
                MagicMock(json=lambda: {"test": "data"}),
            ]

            with patch.object(
                connector.retry_handler,
                "execute",
                side_effect=DataSourceError("Failed"),
            ):
                with pytest.raises(DataSourceError):
                    connector._make_request({"function": "TEST"})

    def test_malformed_response_handling(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test handling of malformed response."""
        with patch.object(connector.session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response

            with pytest.raises(DataSourceError):
                connector._make_request({"function": "TEST"})

    def test_make_request_timeout(self, connector: AlphaVantageDataConnector) -> None:
        """Test request timeout handling."""
        with patch.object(connector.session, "get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

            with pytest.raises(DataSourceError):
                connector._make_request({"function": "TEST"})

    def test_refresh_symbol_cache_success(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test successful symbol cache refresh."""
        search_response = {
            "bestMatches": [
                {"1. symbol": "AAPL", "2. name": "Apple Inc.", "3. type": "Equity"},
                {"1. symbol": "GOOGL", "2. name": "Alphabet Inc.", "3. type": "Equity"},
            ]
        }

        with patch.object(connector, "_make_request", return_value=search_response):
            connector._refresh_symbol_cache()

            assert "AAPL" in connector._symbol_cache
            assert "GOOGL" in connector._symbol_cache

    def test_refresh_symbol_cache_error(
        self, connector: AlphaVantageDataConnector
    ) -> None:
        """Test symbol cache refresh error handling."""
        # Set expired cache and empty initial cache to trigger refresh
        connector._cache_timestamp = 0
        connector._symbol_cache: list[float] = []

        # Mock the logger to avoid actual logging
        with patch.object(connector.logger, "warning"):
            # Should not raise exception, just log warning
            connector._refresh_symbol_cache()
            # Should still have the default symbols even on "error"
            assert len(connector._symbol_cache) > 0
