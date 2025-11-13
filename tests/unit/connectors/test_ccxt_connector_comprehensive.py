"""Comprehensive tests for CCXT data connector."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, Mock
import sys

import pandas as pd
import pytest

# Handle optional CCXT import
try:
    from quantchain.connectors.ccxt_connector import CCXTDataConnector, CCXT_AVAILABLE
    from quantchain.core.exceptions import (
        AuthenticationError,
        DataSourceError,
        RateLimitError,
        SymbolNotFoundError,
    )
    CCXT_IMPORT_AVAILABLE = True
except ImportError as e:
    CCXT_IMPORT_AVAILABLE = False
    CCXTDataConnector = None
    CCXT_AVAILABLE = False

# Skip all tests if CCXT is not available
pytestmark = pytest.mark.skipif(
    not CCXT_AVAILABLE or not CCXT_IMPORT_AVAILABLE, 
    reason="CCXT library not available or import failed"
)


@pytest.mark.unit
class TestCCXTDataConnector:
    """Test suite for CCXTDataConnector."""

    @pytest.fixture
    def mock_ccxt(self):
        """Mock ccxt module for testing."""
        mock_module = MagicMock()
        
        # Create mock exchange class
        mock_exchange = MagicMock()
        mock_exchange.id = "binance"
        mock_exchange.name = "Binance"
        mock_exchange.has = {
            'fetchOHLCV': True,
            'fetchTicker': True,
            'fetchOrderBook': True,
            'fetchTrades': True,
        }
        
        # Set up mock methods
        mock_exchange.fetch_ohlcv.return_value = [
            [1640995200000, 47000.0, 47500.0, 46800.0, 47200.0, 1000.0],
            [1641081600000, 47200.0, 48000.0, 47000.0, 47800.0, 1200.0],
        ]
        
        mock_exchange.fetch_ticker.return_value = {
            'symbol': 'BTC/USDT',
            'last': 47800.0,
            'bid': 47750.0,
            'ask': 47850.0,
            'high': 48000.0,
            'low': 46800.0,
            'volume': 2200.0,
            'timestamp': 1641081600000,
            'datetime': datetime(2022, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        }
        
        mock_exchange.fetch_order_book.return_value = {
            'bids': [[47750.0, 1.5], [47740.0, 2.0]],
            'asks': [[47850.0, 1.2], [47860.0, 1.8]],
            'timestamp': 1641081600000,
            'datetime': datetime(2022, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        }
        
        mock_exchange.fetch_trades.return_value = [
            {
                'info': {'id': '12345'},
                'id': '12345',
                'timestamp': 1641081600000,
                'datetime': datetime(2022, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                'symbol': 'BTC/USDT',
                'order': None,
                'type': 'market',
                'side': 'buy',
                'price': 47800.0,
                'amount': 0.5,
                'cost': 23900.0,
            }
        ]
        
        mock_module.binance = lambda: mock_exchange
        mock_module.exchange.__getitem__.return_value = mock_exchange
        
        # Add exception classes
        mock_module.AuthenticationError = Exception
        mock_module.BadSymbol = Exception
        mock_module.NetworkError = Exception
        mock_module.ExchangeNotAvailable = Exception
        mock_module.RateLimitExceeded = Exception
        
        return mock_module

    @pytest.fixture
    def connector(self, mock_ccxt):
        """Create a CCXT connector with mocked dependencies."""
        with patch.dict(sys.modules, {'ccxt': mock_ccxt}):
            return CCXTDataConnector(api_key="test_key", api_secret="test_secret")

    def test_initialization_with_credentials(self, mock_ccxt):
        """Test connector initialization with credentials."""
        with patch.dict(sys.modules, {'ccxt': mock_ccxt}):
            connector = CCXTDataConnector(
                api_key="test_key",
                api_secret="test_secret",
                exchange="binance"
            )
            
            assert connector.api_key == "test_key"
            assert connector.api_secret == "test_secret"
            assert connector.exchange_name == "binance"
            assert connector.timeout == 30000  # Default timeout

    def test_initialization_without_credentials(self, mock_ccxt):
        """Test connector initialization without credentials."""
        with patch.dict(sys.modules, {'ccxt': mock_ccxt}):
            connector = CCXTDataConnector(exchange="coinbase")
            
            assert connector.api_key is None
            assert connector.api_secret is None
            assert connector.exchange_name == "coinbase"

    def test_initialization_with_config(self, mock_ccxt):
        """Test connector initialization with additional config."""
        with patch.dict(sys.modules, {'ccxt': mock_ccxt}):
            connector = CCXTDataConnector(
                api_key="test_key",
                exchange="binance",
                enableRateLimit=True,
                timeout=5000,
                options={'defaultType': 'spot'}
            )
            
            assert connector.timeout == 5000
            assert hasattr(connector, 'options')

    def test_get_historical_data(self, connector):
        """Test fetching historical OHLCV data."""
        start_date = datetime(2022, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2022, 1, 2, tzinfo=timezone.utc)
        
        data = connector.get_historical_data(
            symbol="BTC/USDT",
            start_date=start_date,
            end_date=end_date,
            timeframe="1H"
        )
        
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 2
        assert list(data.columns) == ['open', 'high', 'low', 'close', 'volume']
        assert data.iloc[0]['close'] == 47200.0
        assert data.iloc[1]['close'] == 47800.0

    def test_get_latest_price(self, connector):
        """Test fetching latest price."""
        price = connector.get_latest_price("BTC/USDT")
        
        assert price == 47800.0

    def test_get_market_data(self, connector):
        """Test fetching comprehensive market data."""
        data = connector.get_market_data("BTC/USDT")
        
        assert data['symbol'] == "BTC/USDT"
        assert data['last'] == 47800.0
        assert data['bid'] == 47750.0
        assert data['ask'] == 47850.0
        assert data['high'] == 48000.0
        assert data['low'] == 46800.0

    def test_get_order_book(self, connector):
        """Test fetching order book."""
        order_book = connector.get_order_book("BTC/USDT", limit=10)
        
        assert 'bids' in order_book
        assert 'asks' in order_book
        assert len(order_book['bids']) == 2
        assert len(order_book['asks']) == 2

    def test_get_recent_trades(self, connector):
        """Test fetching recent trades."""
        trades = connector.get_recent_trades("BTC/USDT", limit=10)
        
        assert isinstance(trades, list)
        assert len(trades) == 1
        assert trades[0]['price'] == 47800.0
        assert trades[0]['amount'] == 0.5
        assert trades[0]['side'] == 'buy'

    def test_get_available_symbols(self, connector):
        """Test fetching available symbols."""
        symbols = connector.get_available_symbols()
        
        assert isinstance(symbols, list)
        # Note: This would depend on the actual mock implementation

    def test_timeframe_mapping(self, connector):
        """Test timeframe mapping conversion."""
        assert connector._convert_timeframe("1Min") == "1m"
        assert connector._convert_timeframe("5Min") == "5m"
        assert connector._convert_timeframe("15Min") == "15m"
        assert connector._convert_timeframe("1H") == "1h"
        assert connector._convert_timeframe("4H") == "4h"
        assert connector._convert_timeframe("1D") == "1d"
        assert connector._convert_timeframe("1W") == "1w"

    def test_authentication_error(self, mock_ccxt):
        """Test handling of authentication errors."""
        mock_ccxt.binance.side_effect = mock_ccxt.AuthenticationError("Invalid API key")
        
        with patch.dict(sys.modules, {'ccxt': mock_ccxt}):
            connector = CCXTDataConnector(api_key="invalid", api_secret="invalid")
            
            with pytest.raises(AuthenticationError):
                connector.get_latest_price("BTC/USDT")

    def test_symbol_not_found_error(self, mock_ccxt):
        """Test handling of symbol not found errors."""
        mock_exchange = mock_ccxt.binance()
        mock_exchange.fetch_ticker.side_effect = mock_ccxt.BadSymbol("Invalid symbol")
        
        with patch.dict(sys.modules, {'ccxt': mock_ccxt}):
            connector = CCXTDataConnector(api_key="test_key", api_secret="test_secret")
            
            with pytest.raises(SymbolNotFoundError):
                connector.get_latest_price("INVALID/PAIR")

    def test_network_error(self, mock_ccxt):
        """Test handling of network errors."""
        mock_exchange = mock_ccxt.binance()
        mock_exchange.fetch_ticker.side_effect = mock_ccxt.NetworkError("Network error")
        
        with patch.dict(sys.modules, {'ccxt': mock_ccxt}):
            connector = CCXTDataConnector(api_key="test_key", api_secret="test_secret")
            
            with pytest.raises(DataSourceError):
                connector.get_latest_price("BTC/USDT")

    def test_rate_limit_error(self, mock_ccxt):
        """Test handling of rate limit errors."""
        mock_exchange = mock_ccxt.binance()
        mock_exchange.fetch_ticker.side_effect = mock_ccxt.RateLimitExceeded("Rate limit exceeded")
        
        with patch.dict(sys.modules, {'ccxt': mock_ccxt}):
            connector = CCXTDataConnector(api_key="test_key", api_secret="test_secret")
            
            with pytest.raises(RateLimitError):
                connector.get_latest_price("BTC/USDT")

    def test_exchange_not_available(self, mock_ccxt):
        """Test handling of exchange not available errors."""
        mock_ccxt.binance.side_effect = mock_ccxt.ExchangeNotAvailable("Exchange maintenance")
        
        with patch.dict(sys.modules, {'ccxt': mock_ccxt}):
            with pytest.raises(DataSourceError):
                CCXTDataConnector(api_key="test_key", api_secret="test_secret", exchange="binance")

    def test_unsupported_timeframe(self, connector):
        """Test handling of unsupported timeframes."""
        with pytest.raises(ValueError, match="Unsupported timeframe"):
            connector.get_historical_data(
                "BTC/USDT",
                datetime(2022, 1, 1, tzinfo=timezone.utc),
                datetime(2022, 1, 2, tzinfo=timezone.utc),
                timeframe="unsupported"
            )

    def test_empty_historical_data(self, connector):
        """Test handling of empty historical data response."""
        mock_exchange = connector.exchange
        mock_exchange.fetch_ohlcv.return_value = []
        
        data = connector.get_historical_data(
            "BTC/USDT",
            datetime(2022, 1, 1, tzinfo=timezone.utc),
            datetime(2022, 1, 2, tzinfo=timezone.utc),
            timeframe="1H"
        )
        
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 0

    def test_pagination(self, connector):
        """Test handling of paginated data."""
        mock_exchange = connector.exchange
        mock_exchange.fetch_ohlcv.side_effect = [
            [[1640995200000, 47000.0, 47500.0, 46800.0, 47200.0, 1000.0]],
            [[1641081600000, 47200.0, 48000.0, 47000.0, 47800.0, 1200.0]],
            []  # End of pagination
        ]
        
        data = connector.get_historical_data(
            "BTC/USDT",
            datetime(2022, 1, 1, tzinfo=timezone.utc),
            datetime(2022, 1, 2, tzinfo=timezone.utc),
            timeframe="1H"
        )
        
        assert len(data) == 2

    def test_symbol_format_validation(self, connector):
        """Test symbol format validation."""
        # Valid symbols
        valid_symbols = ["BTC/USDT", "ETH/USD", "XRP/BTC"]
        
        for symbol in valid_symbols:
            # Should not raise
            connector._validate_symbol(symbol)
        
        # Invalid symbols
        invalid_symbols = ["BTCUSDT", "BTC-USDT", "BTC"]
        
        for symbol in invalid_symbols:
            with pytest.raises(ValueError, match="Invalid symbol format"):
                connector._validate_symbol(symbol)

    def test_get_supported_timeframes(self, connector):
        """Test getting supported timeframes."""
        timeframes = connector.get_supported_timeframes()
        
        assert "1Min" in timeframes
        assert "5Min" in timeframes
        assert "15Min" in timeframes
        assert "1H" in timeframes
        assert "4H" in timeframes
        assert "1D" in timeframes
        assert "1W" in timeframes

    def test_get_exchange_info(self, connector):
        """Test getting exchange information."""
        info = connector.get_exchange_info()
        
        assert info['name'] == "Binance"
        assert info['id'] == "binance"
        assert 'has' in info
        assert info['has']['fetchOHLCV'] is True

    def test_custom_exchange_init(self, mock_ccxt):
        """Test initialization with custom exchange."""
        mock_exchange = MagicMock()
        mock_exchange.id = "custom"
        mock_ccxt.exchange.__getitem__.return_value = mock_exchange
        
        with patch.dict(sys.modules, {'ccxt': mock_ccxt}):
            connector = CCXTDataConnector(exchange="custom")
            
            assert connector.exchange_name == "custom"
            assert connector.exchange.id == "custom"


@pytest.mark.skipif(not CCXT_AVAILABLE, reason="CCXT library not available")
class TestCCXTIntegration:
    """Integration tests for CCXT (only run when CCXT is actually available)."""

    def test_ccxt_availability(self):
        """Test that CCXT is available for integration tests."""
        try:
            import ccxt
            assert hasattr(ccxt, 'binance')
        except ImportError:
            pytest.skip("CCXT not available for integration tests")

    def test_real_exchange_list(self):
        """Test that we can get real exchange list."""
        try:
            import ccxt
            exchanges = list(ccxt.exchanges)
            assert len(exchanges) > 0
            assert 'binance' in exchanges
        except ImportError:
            pytest.skip("CCXT not available for integration tests")


@pytest.mark.unit
class TestCCXTDataConnectorStatic:
    """Test static methods and properties."""

    def test_timeframe_mapping_constant(self):
        """Test that TIMEFRAME_MAPPING is properly defined."""
        if CCXTDataConnector:
            mapping = CCXTDataConnector.TIMEFRAME_MAPPING
            assert isinstance(mapping, dict)
            assert "1Min" in mapping
            assert mapping["1Min"] == "1m"

    def test_default_exchange_constant(self):
        """Test that DEFAULT_EXCHANGE is properly defined."""
        if CCXTDataConnector:
            assert hasattr(CCXTDataConnector, 'DEFAULT_EXCHANGE')
            assert CCXTDataConnector.DEFAULT_EXCHANGE == "binance"
