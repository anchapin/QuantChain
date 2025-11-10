"""Tests for CCXT data connector."""

import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Import ccxt for creating custom exception classes in test methods
import ccxt

# Import all needed modules at top to avoid E402 errors
from quantchain.connectors.ccxt_connector import CCXTDataConnector
from quantchain.core.exceptions import (
    AuthenticationError,
    DataSourceError,
    RateLimitError,
    SymbolNotFoundError,
)

# Mock ccxt before importing connector
ccxt_mock = MagicMock()
# Add necessary exception classes to mock
ccxt_mock.AuthenticationError = Exception
ccxt_mock.BadSymbol = Exception
ccxt_mock.NetworkError = Exception
ccxt_mock.ExchangeNotAvailable = Exception
ccxt_mock.RateLimitExceeded = Exception
# Set up mock before importing connector
# Remove any existing ccxt module from cache
if "ccxt" in sys.modules:
    del sys.modules["ccxt"]
# Also remove quantchain.connectors.ccxt_connector if already imported
if "quantchain.connectors.ccxt_connector" in sys.modules:
    del sys.modules["quantchain.connectors.ccxt_connector"]
sys.modules["ccxt"] = ccxt_mock


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
        # Mock all methods that tests will try to configure
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
            return CCXTDataConnector(exchange="binance")
