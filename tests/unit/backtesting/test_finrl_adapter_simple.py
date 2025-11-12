"""Tests for FinRL adapter."""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

try:
    from quantchain.backtesting.finrl_adapter import (
        FinRLAdapter,
        get_connector,
        FinRLAdapterError,
        FinRLConnectionError,
        FinRLDataError,
    )
    FINRL_ADAPTER_AVAILABLE = True
except ImportError as e:
    FINRL_ADAPTER_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not FINRL_ADAPTER_AVAILABLE, 
    reason="FinRL adapter not available"
)


class TestGetConnector:
    """Test cases for get_connector function."""

    def test_get_alpaca_connector(self):
        """Test getting Alpaca connector."""
        with patch('quantchain.backtesting.finrl_adapter.AlpacaDataConnector') as mock_connector:
            connector = get_connector("alpaca", api_key="test", secret="test")
            mock_connector.assert_called_once_with(api_key="test", secret="test")
    
    def test_get_polygon_connector(self):
        """Test getting Polygon connector."""
        with patch('quantchain.backtesting.finrl_adapter.PolygonDataConnector') as mock_connector:
            connector = get_connector("polygon", api_key="test")
            mock_connector.assert_called_once_with(api_key="test")
    
    def test_get_ccxt_connector(self):
        """Test getting CCXT connector."""
        with patch('quantchain.backtesting.finrl_adapter.CCXTDataConnector') as mock_connector:
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
        # Mock historical data
        connector.get_historical_data.return_value = pd.DataFrame({
            'timestamp': pd.date_range('2023-01-01', periods=100, freq='1D'),
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 102,
            'low': np.random.randn(100).cumsum() + 98,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000000, 5000000, 100),
        })
        return connector

    @pytest.fixture
    def adapter(self, mock_data_connector):
        """Create test adapter."""
        return FinRLAdapter(
            data_connector=mock_data_connector,
            symbol='AAPL',
            initial_balance=100000,
            lookback_window=10,
        )

    def test_initialization(self, adapter):
        """Test adapter initialization."""
        assert adapter.initial_balance == 100000
        assert adapter.lookback_window == 10
        assert adapter.symbol == 'AAPL'

    def test_validate_parameters_valid(self):
        """Test parameter validation with valid parameters."""
        adapter = FinRLAdapter(
            data_connector=Mock(),
            symbol='AAPL',
            initial_balance=100000,
            lookback_window=10,
        )
        # Should not raise
        adapter._validate_parameters()

    def test_validate_parameters_invalid_symbol(self, mock_data_connector):
        """Test parameter validation with invalid symbol."""
        with pytest.raises(FinRLDataError):
            FinRLAdapter(
                data_connector=mock_data_connector,
                symbol='',  # Invalid symbol
                initial_balance=100000,
                lookback_window=10,
            )

    def test_validate_parameters_invalid_balance(self, mock_data_connector):
        """Test parameter validation with invalid balance."""
        with pytest.raises(FinRLDataError):
            FinRLAdapter(
                data_connector=mock_data_connector,
                symbol='AAPL',
                initial_balance=-1000,  # Invalid balance
                lookback_window=10,
            )

    def test_validate_parameters_invalid_lookback(self, mock_data_connector):
        """Test parameter validation with invalid lookback window."""
        with pytest.raises(FinRLDataError):
            FinRLAdapter(
                data_connector=mock_data_connector,
                symbol='AAPL',
                initial_balance=100000,
                lookback_window=0,  # Invalid lookback
            )
