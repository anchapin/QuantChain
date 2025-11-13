"""Tests for FinRL adapter."""

from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

try:
    from quantchain.backtesting.finrl_adapter import (
        FinRLAdapter,
        FinRLAdapterError,
        FinRLConnectionError,
        FinRLDataError,
        get_connector,
    )

    FINRL_ADAPTER_AVAILABLE = True
except ImportError as e:
    FINRL_ADAPTER_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not FINRL_ADAPTER_AVAILABLE, reason="FinRL adapter not available"
)


class TestGetConnector:
    """Test cases for get_connector function."""

    def test_get_alpaca_connector(self):
        """Test getting Alpaca connector."""
        with patch(
            "quantchain.backtesting.finrl_adapter.AlpacaDataConnector"
        ) as mock_connector:
            connector = get_connector("alpaca", api_key="test", secret="test")
            mock_connector.assert_called_once_with(api_key="test", secret="test")

    def test_get_polygon_connector(self):
        """Test getting Polygon connector."""
        with patch(
            "quantchain.backtesting.finrl_adapter.PolygonDataConnector"
        ) as mock_connector:
            connector = get_connector("polygon", api_key="test")
            mock_connector.assert_called_once_with(api_key="test")

    def test_get_ccxt_connector(self):
        """Test getting CCXT connector."""
        with patch(
            "quantchain.backtesting.finrl_adapter.CCXTDataConnector"
        ) as mock_connector:
            connector = get_connector("ccxt", exchange="binance")
            mock_connector.assert_called_once_with(exchange="binance")

    def test_get_invalid_connector(self):
        """Test getting invalid connector."""
        with pytest.raises(ValueError):
            get_connector("invalid")


class TestFinRLAdapterErrors:
    """Test cases for FinRL adapter errors."""

    def test_finrl_adapter_error(self):
        """Test FinRLAdapterError."""
        error = FinRLAdapterError("Test error")
        assert str(error) == "Test error"

    def test_finrl_connection_error(self):
        """Test FinRLConnectionError."""
        error = FinRLConnectionError("Connection failed")
        assert str(error) == "Connection failed"

    def test_finrl_data_error(self):
        """Test FinRLDataError."""
        error = FinRLDataError("Data error")
        assert str(error) == "Data error"

    def test_error_inheritance(self):
        """Test error inheritance."""
        assert issubclass(FinRLConnectionError, FinRLAdapterError)
        assert issubclass(FinRLDataError, FinRLAdapterError)


@pytest.mark.skipif(not FINRL_ADAPTER_AVAILABLE, reason="FinRL adapter not available")
class TestFinRLAdapter:
    """Test cases for FinRLAdapter class."""

    @pytest.fixture
    def mock_data_connector(self):
        """Mock data connector."""
        connector = Mock()
        # Mock historical data with deterministic values
        dates = pd.date_range("2023-01-01", periods=100, freq="1D")
        prices = [100 + i * 0.1 for i in range(100)]
        volumes = [1000000 + i * 10000 for i in range(100)]
        
        data = pd.DataFrame(
            {
                "timestamp": dates,
                "open": prices,
                "high": [p * 1.02 for p in prices],
                "low": [p * 0.98 for p in prices],
                "close": prices,
                "volume": volumes,
            }
        )
        # Set timestamp as index for proper pandas operations
        data = data.set_index('timestamp')
        connector.get_historical_data.return_value = data
        return connector

    @pytest.fixture
    def adapter(self, mock_data_connector):
        """Create test adapter."""
        with patch("quantchain.backtesting.finrl_adapter.get_connector", return_value=mock_data_connector):
            return FinRLAdapter(
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-04-10",
                initial_balance=100000,
                data_connector="alpaca",
            )

    def test_initialization(self, adapter):
        """Test adapter initialization."""
        assert adapter.initial_balance == 100000
        assert adapter.symbol == "AAPL"
        assert adapter.start_date.strftime("%Y-%m-%d") == "2023-01-01"
        assert adapter.end_date.strftime("%Y-%m-%d") == "2023-04-10"

    
