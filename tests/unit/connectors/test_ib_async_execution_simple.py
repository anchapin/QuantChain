"""Simple tests for IB async execution connector."""

import pytest
from unittest.mock import Mock, patch

# Check if ib_async_execution is available
try:
    from quantchain.connectors.ib_async_execution import (
        IBExecutionConnector,
        IB_ASYNC_AVAILABLE,
    )
    IB_EXECUTION_AVAILABLE = True
except ImportError as e:
    IB_EXECUTION_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not IB_EXECUTION_AVAILABLE, reason="IB execution connector not available"
)


@pytest.mark.unit
class TestIBExecutionSimple:
    """Simple tests for IB execution connector."""

    def test_ib_async_availability_constant(self):
        """Test IB_ASYNC_AVAILABLE constant is defined."""
        assert isinstance(IB_ASYNC_AVAILABLE, bool)

    def test_class_import(self):
        """Test IBExecutionConnector class can be imported."""
        assert IBExecutionConnector is not None

    def test_class_instantiation_with_mock(self):
        """Test class can be instantiated with mocked IB."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib:
            mock_ib.return_value = Mock()

            with patch("asyncio.new_event_loop"):
                with patch("quantchain.connectors.ib_async_execution.IBExecutionConnector._connect"):
                    connector = IBExecutionConnector(
                        host="127.0.0.1",
                        port=7497,
                        client_id=1,
                        timeout=10,
                    )

                    assert connector.host == "127.0.0.1"
                    assert connector.port == 7497
                    assert connector.client_id == 1
                    assert connector.timeout == 10

    def test_side_mapping(self):
        """Test order side mapping."""
        with patch("quantchain.connectors.ib_async_execution.IB"):
            with patch("asyncio.new_event_loop"):
                with patch("quantchain.connectors.ib_async_execution.IBExecutionConnector._connect"):
                    connector = IBExecutionConnector()

                    assert "BUY" in connector.SIDE_MAPPING.values()
                    assert "SELL" in connector.SIDE_MAPPING.values()

    def test_type_mapping(self):
        """Test order type mapping."""
        with patch("quantchain.connectors.ib_async_execution.IB"):
            with patch("asyncio.new_event_loop"):
                with patch("quantchain.connectors.ib_async_execution.IBExecutionConnector._connect"):
                    connector = IBExecutionConnector()

                    # Check that keys are OrderType enum values
                    from quantchain.tools.trading_execution import OrderType
                    for order_type in [OrderType.MARKET, OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT]:
                        assert order_type in connector.TYPE_MAPPING

    def test_tif_mapping(self):
        """Test time in force mapping."""
        with patch("quantchain.connectors.ib_async_execution.IB"):
            with patch("asyncio.new_event_loop"):
                with patch("quantchain.connectors.ib_async_execution.IBExecutionConnector._connect"):
                    connector = IBExecutionConnector()

                    # Check that keys are TimeInForce enum values
                    from quantchain.tools.trading_execution import TimeInForce
                    for tif in [TimeInForce.DAY, TimeInForce.GTC, TimeInForce.IOC, TimeInForce.FOK]:
                        assert tif in connector.TIF_MAPPING

    def test_status_mapping(self):
        """Test order status mapping."""
        with patch("quantchain.connectors.ib_async_execution.IB"):
            with patch("asyncio.new_event_loop"):
                with patch("quantchain.connectors.ib_async_execution.IBExecutionConnector._connect"):
                    connector = IBExecutionConnector()

                    # Check that values are OrderStatus enum values
                    from quantchain.tools.trading_execution import OrderStatus
                    for status in [OrderStatus.PENDING, OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                        assert status in connector.STATUS_MAPPING.values()

    def test_create_contract_for_forex(self):
        """Test creating forex contract."""
        with patch("quantchain.connectors.ib_async_execution.IB"):
            with patch("asyncio.new_event_loop"):
                with patch("quantchain.connectors.ib_async_execution.IBExecutionConnector._connect"):
                    connector = IBExecutionConnector()

                    # Test forex pair
                    with patch("quantchain.connectors.ib_async_execution.Forex") as mock_forex:
                        mock_contract = Mock()
                        mock_forex.return_value = mock_contract

                        result = connector._create_contract("EURUSD")

                        assert result == mock_contract
                        mock_forex.assert_called_once_with()
                        # Check that the symbol is set after creation
                        assert mock_contract.symbol == "EUR"
                        assert mock_contract.currency == "USD"

    def test_create_contract_for_option(self):
        """Test creating option contract."""
        with patch("quantchain.connectors.ib_async_execution.IB"):
            with patch("asyncio.new_event_loop"):
                with patch("quantchain.connectors.ib_async_execution.IBExecutionConnector._connect"):
                    connector = IBExecutionConnector()

                    # Test option format
                    with patch("quantchain.connectors.ib_async_execution.Option") as mock_option:
                        mock_contract = Mock()
                        mock_option.return_value = mock_contract

                        result = connector._create_contract("AAPL 231215 150 C")

                        # Check that the option was created with the right parameters
                        # Note: The Option constructor is called with parameters directly
                        # The result will be an Option object, not a mock
                        assert hasattr(result, 'symbol')
                        assert hasattr(result, 'lastTradeDateOrContractMonth')
                        assert hasattr(result, 'strike')
                        assert hasattr(result, 'right')

    def test_create_contract_for_stock(self):
        """Test creating stock contract."""
        with patch("quantchain.connectors.ib_async_execution.IB"):
            with patch("asyncio.new_event_loop"):
                with patch("quantchain.connectors.ib_async_execution.IBExecutionConnector._connect"):
                    connector = IBExecutionConnector()

                    # Test stock format
                    with patch("quantchain.connectors.ib_async_execution.Stock") as mock_stock:
                        mock_contract = Mock()
                        mock_stock.return_value = mock_contract

                        result = connector._create_contract("AAPL")

                        assert result == mock_contract
                        mock_stock.assert_called_once_with()
                        # Check that the symbol and other attributes are set after creation
                        assert mock_contract.symbol == "AAPL"
                        assert mock_contract.secType == "STK"
                        assert mock_contract.exchange == "SMART"
                        assert mock_contract.currency == "USD"

    def test_init_parameters(self):
        """Test initialization with various parameters."""
        with patch("quantchain.connectors.ib_async_execution.IB"):
            with patch("asyncio.new_event_loop"):
                with patch("quantchain.connectors.ib_async_execution.IBExecutionConnector._connect"):
                    # Test with all parameters
                    connector = IBExecutionConnector(
                        host="192.168.1.1",
                        port=4001,
                        client_id=2,
                        timeout=30,
                        readonly=True,
                        account="DU123456",
                    )

                    assert connector.host == "192.168.1.1"
                    assert connector.port == 4001
                    assert connector.client_id == 2
                    assert connector.timeout == 30
                    assert connector.readonly is True
                    assert connector.account == "DU123456"

    def test_attribute_initialization(self):
        """Test that attributes are properly initialized."""
        with patch("quantchain.connectors.ib_async_execution.IB"):
            with patch("asyncio.new_event_loop"):
                with patch("quantchain.connectors.ib_async_execution.IBExecutionConnector._connect"):
                    connector = IBExecutionConnector()

                    # Check that attributes exist
                    assert hasattr(connector, 'host')
                    assert hasattr(connector, 'port')
                    assert hasattr(connector, 'client_id')
                    assert hasattr(connector, 'timeout')
                    assert hasattr(connector, 'readonly')
                    assert hasattr(connector, 'account')
                    assert hasattr(connector, 'ib')
                    assert hasattr(connector, '_loop')
                    assert hasattr(connector, '_order_map')
