"""Tests for Alpaca execution connector."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from alpaca.trading.enums import (
    OrderSide as AlpacaOrderSide,
    OrderType as AlpacaOrderType,
)

from quantchain.connectors.alpaca_execution import AlpacaExecutionConnector
from quantchain.tools.trading_execution import (
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderType,
    OrderStatus,
    Position,
    AccountInfo,
    ValidationError,
    InsufficientFundsError,
    OrderNotFoundError,
)


@pytest.mark.unit
class TestAlpacaExecutionConnector:
    """Test cases for AlpacaExecutionConnector."""

    @pytest.fixture
    def mock_client(self) -> None:
        """Mock Alpaca trading client."""
        with patch(
            "quantchain.connectors.alpaca_execution.TradingClient"
        ) as mock_trading_client:
            client_instance = Mock()
            mock_trading_client.return_value = client_instance
            yield client_instance

    @pytest.fixture
    def connector(self, mock_client):
        """Create Alpaca execution connector with mocked client."""
        return AlpacaExecutionConnector(
            api_key="test-key", api_secret="test-secret", use_paper=True
        )

    def test_initialization(self) -> None:
        """Test connector initialization."""
        with patch(
            "quantchain.connectors.alpaca_execution.TradingClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            connector = AlpacaExecutionConnector(
                api_key="test-key",
                api_secret="test-secret",
                use_paper=True,
                base_url="https://test.api.com",
            )

            mock_client_class.assert_called_once_with(
                "test-key",
                "test-secret",
                paper=True,
                url_override="https://test.api.com",
            )

            assert connector.api_key == "test-key"
            assert connector.api_secret == "test-secret"
            assert connector.use_paper is True
            assert connector.base_url == "https://test.api.com"

    def test_authentication_error(self) -> None:
        """Test authentication error handling."""
        with patch(
            "quantchain.connectors.alpaca_execution.TradingClient"
        ) as mock_client_class:
            mock_client_class.side_effect = Exception("Authentication failed")

            with pytest.raises(Exception) as exc_info:
                AlpacaExecutionConnector("bad-key", "bad-secret")

            assert "Failed to authenticate with Alpaca" in str(exc_info.value)

    def test_is_crypto_symbol(self, connector) -> None:
        """Test crypto symbol detection."""
        assert connector._is_crypto_symbol("BTC/USD") is True
        assert connector._is_crypto_symbol("BTC-USD") is True
        assert connector._is_crypto_symbol("ETH/USD") is True
        assert connector._is_crypto_symbol("AAPL") is False
        assert connector._is_crypto_symbol("MSFT") is False

    def test_normalize_symbol(self, connector) -> None:
        """Test symbol normalization."""
        assert connector._normalize_symbol("BTC-USD") == "BTC/USD"
        assert connector._normalize_symbol("BTC/USD") == "BTC/USD"
        assert connector._normalize_symbol("AAPL") == "AAPL"
        assert connector._normalize_symbol("MSFT") == "MSFT"

    def test_get_asset_class(self, connector) -> None:
        """Test asset class determination."""
        assert connector._get_asset_class("BTC/USD") == "crypto"
        assert connector._get_asset_class("BTC-USD") == "crypto"
        assert connector._get_asset_class("AAPL") == "equity"
        assert connector._get_asset_class("MSFT") == "equity"

    def test_convert_order_status(self, connector) -> None:
        """Test order status conversion."""
        assert connector._convert_order_status("new") == OrderStatus.PENDING
        assert connector._convert_order_status("filled") == OrderStatus.FILLED
        assert (
            connector._convert_order_status("partially_filled")
            == OrderStatus.PARTIALLY_FILLED
        )
        assert connector._convert_order_status("canceled") == OrderStatus.CANCELLED
        assert connector._convert_order_status("rejected") == OrderStatus.REJECTED
        assert connector._convert_order_status("unknown") == OrderStatus.PENDING

    def test_place_equity_market_order(self, connector, mock_client) -> None:
        """Test placing an equity market order."""
        # Setup mock order response
        mock_alpaca_order = Mock()
        mock_alpaca_order.id = "order-123"
        mock_alpaca_order.symbol = "AAPL"
        mock_alpaca_order.side = AlpacaOrderSide.BUY
        mock_alpaca_order.order_type = AlpacaOrderType.MARKET
        mock_alpaca_order.qty = "100"
        mock_alpaca_order.filled_qty = "100"
        mock_alpaca_order.limit_price = None
        mock_alpaca_order.stop_price = None
        mock_alpaca_order.filled_avg_price = "150.50"
        mock_alpaca_order.status = "filled"
        mock_alpaca_order.submitted_at = datetime.now(timezone.utc)
        mock_alpaca_order.updated_at = datetime.now(timezone.utc)
        mock_alpaca_order.client_order_id = "client-456"

        mock_client.submit_order.return_value = mock_alpaca_order

        # Mock asset info
        with patch.object(connector, "_get_symbol_info") as mock_get_info:
            mock_get_info.return_value = {
                "symbol": "AAPL",
                "tradable": True,
                "min_order_size": 1,
                "asset_class": "equity",
            }

            # Place order
            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=100,
                client_order_id="client-456",
            )

            result = connector.place_order(order)

            # Verify result
            assert result.order_id == "order-123"
            assert result.client_order_id == "client-456"
            assert result.symbol == "AAPL"
            assert result.side == OrderSide.BUY
            assert result.order_type == OrderType.MARKET
            assert result.quantity == 100
            assert result.filled_quantity == 100
            assert result.status == OrderStatus.FILLED
            assert result.avg_fill_price == 150.50

            # Verify Alpaca client was called correctly
            mock_client.submit_order.assert_called_once()

    def test_place_crypto_limit_order(self, connector, mock_client) -> None:
        """Test placing a crypto limit order."""
        # Setup mock order response
        mock_alpaca_order = Mock()
        mock_alpaca_order.id = "order-456"
        mock_alpaca_order.symbol = "BTC/USD"
        mock_alpaca_order.side = AlpacaOrderSide.BUY
        mock_alpaca_order.order_type = AlpacaOrderType.LIMIT
        mock_alpaca_order.qty = "0.001"
        mock_alpaca_order.filled_qty = "0"
        mock_alpaca_order.limit_price = "45000.00"
        mock_alpaca_order.stop_price = None
        mock_alpaca_order.filled_avg_price = None
        mock_alpaca_order.status = "new"
        mock_alpaca_order.submitted_at = datetime.now(timezone.utc)
        mock_alpaca_order.updated_at = None
        mock_alpaca_order.client_order_id = None

        mock_client.submit_order.return_value = mock_alpaca_order

        # Mock asset info
        with patch.object(connector, "_get_symbol_info") as mock_get_info:
            mock_get_info.return_value = {
                "symbol": "BTC/USD",
                "tradable": True,
                "min_order_size": 1e-8,
                "asset_class": "crypto",
            }

            # Place order
            order = OrderRequest(
                symbol="BTC/USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.001,
                price=45000.0,
            )

            result = connector.place_order(order)

            # Verify result
            assert result.order_id == "order-456"
            assert result.symbol == "BTC/USD"
            assert result.side == OrderSide.BUY
            assert result.order_type == OrderType.LIMIT
            assert result.quantity == 0.001
            assert result.filled_quantity == 0
            assert result.price == 45000.0
            assert result.status == OrderStatus.PENDING

    def test_place_order_insufficient_funds(self, connector, mock_client) -> None:
        """Test order placement with insufficient funds."""
        mock_client.submit_order.side_effect = Exception("Insufficient funds")

        with patch.object(connector, "_get_symbol_info") as mock_get_info:
            mock_get_info.return_value = {
                "symbol": "AAPL",
                "tradable": True,
                "min_order_size": 1,
                "asset_class": "equity",
            }

            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=100,
            )

            with pytest.raises(InsufficientFundsError) as exc_info:
                connector.place_order(order)

            assert "Insufficient funds" in str(exc_info.value)

    def test_place_order_validation_error(self, connector, mock_client) -> None:
        """Test order placement with validation error."""
        mock_client.submit_order.side_effect = Exception("Invalid order quantity")

        with patch.object(connector, "_get_symbol_info") as mock_get_info:
            mock_get_info.return_value = {
                "symbol": "AAPL",
                "tradable": True,
                "min_order_size": 1,
                "asset_class": "equity",
            }

            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=100,
            )

            with pytest.raises(ValidationError) as exc_info:
                connector.place_order(order)

            assert "Invalid order" in str(exc_info.value)

    def test_cancel_order(self, connector, mock_client) -> None:
        """Test order cancellation."""
        # Setup mock order
        mock_alpaca_order = Mock()
        mock_alpaca_order.configure_mock(
            id="order-123",
            symbol="AAPL",
            side=AlpacaOrderSide.BUY,
            order_type=AlpacaOrderType.MARKET,
            qty="100",
            filled_qty="50",
            limit_price=None,
            stop_price=None,
            filled_avg_price="150.00",
            status="canceled",
            submitted_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            client_order_id=None,
        )

        mock_client.cancel_order_by_id.return_value = None
        mock_client.get_order_by_id.return_value = mock_alpaca_order

        result = connector.cancel_order("order-123")

        assert result.order_id == "order-123"
        assert result.status == OrderStatus.CANCELLED
        mock_client.cancel_order_by_id.assert_called_once_with("order-123")
        mock_client.get_order_by_id.assert_called_once_with("order-123")

    def test_cancel_order_not_found(self, connector, mock_client) -> None:
        """Test canceling non-existent order."""
        mock_client.cancel_order_by_id.side_effect = Exception("Order not found")

        with pytest.raises(OrderNotFoundError):
            connector.cancel_order(order_id="non-existent")

    def test_get_order(self, connector, mock_client) -> None:
        """Test getting order details."""
        # Setup mock order
        mock_alpaca_order = Mock()
        mock_alpaca_order.configure_mock(
            id="order-123",
            symbol="AAPL",
            side=AlpacaOrderSide.BUY,
            order_type=AlpacaOrderType.MARKET,
            qty="100",
            filled_qty="100",
            limit_price=None,
            stop_price=None,
            filled_avg_price="150.50",
            status="filled",
            submitted_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            client_order_id=None,
        )

        mock_client.get_order_by_id.return_value = mock_alpaca_order

        result = connector.get_order("order-123")

        assert result.order_id == "order-123"
        assert result.symbol == "AAPL"
        assert result.status == OrderStatus.FILLED
        assert result.filled_quantity == 100
        assert result.avg_fill_price == 150.50
        mock_client.get_order_by_id.assert_called_once_with("order-123")

    def test_get_order_not_found(self, connector, mock_client) -> None:
        """Test getting non-existent order."""
        mock_client.get_order_by_id.side_effect = Exception("Order not found")

        with pytest.raises(OrderNotFoundError):
            connector.get_order("non-existent")

    def test_get_account(self, connector, mock_client) -> None:
        """Test getting account information."""
        # Setup mock account
        mock_account = Mock()
        mock_account.id = "account-123"
        mock_account.buying_power = "50000.00"
        mock_account.cash = "30000.00"
        mock_account.portfolio_value = "80000.00"
        mock_account.daytrading_buying_power = "60000.00"

        # Setup mock positions
        mock_position = Mock()
        mock_position.symbol = "AAPL"
        mock_position.qty = "100"
        mock_position.avg_entry_price = "150.00"
        mock_position.current_price = "155.00"
        mock_position.market_value = "15500.00"

        mock_client.get_account.return_value = mock_account
        mock_client.get_all_positions.return_value: list[float] = [mock_position]

        with patch.object(connector, "get_positions") as mock_get_positions:
            mock_get_positions.return_value = [
                Position(
                    symbol="AAPL",
                    quantity=100,
                    avg_entry_price=150.0,
                    current_price=155.0,
                    market_value=15500.0,
                    unrealized_pnl=500.0,
                    unrealized_pnl_percent=3.33,
                )
            ]

            account = connector.get_account()

            # Verify the return type is correct
            assert isinstance(account, AccountInfo)

            assert account.account_id == "account-123"
            assert account.buying_power == 50000.0
            assert account.cash == 30000.0
            assert account.portfolio_value == 80000.0
            assert account.margin_available == 60000.0
            assert len(account.positions) == 1
            assert account.positions[0].symbol == "AAPL"

    def test_get_positions(self, connector, mock_client) -> None:
        """Test getting current positions."""
        # Setup mock positions
        mock_position1 = Mock()
        mock_position1.symbol = "AAPL"
        mock_position1.qty = "100"
        mock_position1.avg_entry_price = "150.00"
        mock_position1.current_price = "155.00"
        mock_position1.market_value = "15500.00"

        mock_position2 = Mock()
        mock_position2.symbol = "MSFT"
        mock_position2.qty = "50"
        mock_position2.avg_entry_price = "300.00"
        mock_position2.current_price = "290.00"
        mock_position2.market_value = "14500.00"

        mock_client.get_all_positions.return_value: list[float] = [
            mock_position1,
            mock_position2,
        ]

        positions = connector.get_positions()

        assert len(positions) == 2

        # Check AAPL position
        aapl = positions[0]
        assert aapl.symbol == "AAPL"
        assert aapl.quantity == 100
        assert aapl.avg_entry_price == 150.0
        assert aapl.current_price == 155.0
        assert aapl.market_value == 15500.0
        assert aapl.unrealized_pnl == 500.0
        assert abs(aapl.unrealized_pnl_percent - 3.33) < 0.1

        # Check MSFT position (loss)
        msft = positions[1]
        assert msft.symbol == "MSFT"
        assert msft.quantity == 50
        assert msft.unrealized_pnl == -500.0
        assert abs(msft.unrealized_pnl_percent + 3.33) < 0.1

    def test_get_order_history(self, connector, mock_client) -> None:
        """Test getting order history."""
        # Setup mock orders
        mock_order1 = Mock()
        mock_order1.id = "order-1"
        mock_order1.symbol = "AAPL"
        mock_order1.status = "filled"

        mock_order2 = Mock()
        mock_order2.id = "order-2"
        mock_order2.symbol = "MSFT"
        mock_order2.status = "canceled"

        mock_client.get_orders.return_value: list[float] = [mock_order1, mock_order2]

        with patch.object(connector, "_convert_alpaca_order") as mock_convert:
            mock_convert.side_effect = [
                OrderResult(
                    order_id="order-1",
                    client_order_id=None,
                    symbol="AAPL",
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=100,
                    filled_quantity=100,
                    price=None,
                    stop_price=None,
                    avg_fill_price=150.0,
                    status=OrderStatus.FILLED,
                    timestamp=datetime.now(),
                ),
                OrderResult(
                    order_id="order-2",
                    client_order_id=None,
                    symbol="MSFT",
                    side=OrderSide.SELL,
                    order_type=OrderType.LIMIT,
                    quantity=50,
                    filled_quantity=0,
                    price=300.0,
                    stop_price=None,
                    avg_fill_price=None,
                    status=OrderStatus.CANCELLED,
                    timestamp=datetime.now(),
                ),
            ]

            history = connector.get_order_history(symbol="AAPL", limit=10)

            assert len(history) == 2
            mock_client.get_orders.assert_called_once()

    def test_is_market_open_equity(self, connector, mock_client) -> None:
        """Test market status for equities."""
        mock_clock = Mock()
        mock_clock.is_open = True
        mock_client.get_clock.return_value = mock_clock

        assert connector.is_market_open("AAPL") is True
        mock_client.get_clock.assert_called_once()

    def test_is_market_open_crypto(self, connector) -> None:
        """Test market status for crypto (always open)."""
        assert connector.is_market_open("BTC/USD") is True
        assert connector.is_market_open("BTC-USD") is True

    def test_is_market_open_no_symbol(self, connector, mock_client) -> None:
        """Test market status without symbol (equity default)."""
        mock_clock = Mock()
        mock_clock.is_open = False
        mock_client.get_clock.return_value = mock_clock

        assert connector.is_market_open() is False
        mock_client.get_clock.assert_called_once()

    def test_get_symbol_info(self, connector) -> None:
        """Test getting symbol information."""
        with patch.object(connector, "_get_symbol_info") as mock_get_info:
            mock_get_info.return_value = {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "asset_class": "equity",
                "tradable": True,
                "fractionable": True,
                "min_order_size": 0.01,
                "price_precision": 2,
                "size_precision": 0,
            }

            info = connector.get_symbol_info("AAPL")

            assert info["symbol"] == "AAPL"
            assert info["tradable"] is True
            assert info["min_order_size"] == 0.01

    def test_get_market_hours(self, connector, mock_client) -> None:
        """Test getting market hours."""
        mock_clock = Mock()
        mock_clock.is_open = True
        mock_clock.next_open = datetime.now(timezone.utc)
        mock_clock.next_close = datetime.now(timezone.utc)
        mock_clock.timestamp = datetime.now(timezone.utc)

        mock_client.get_clock.return_value = mock_clock

        hours = connector.get_market_hours("AAPL")

        assert hours["is_open"] is True
        assert hours["market_type"] == "equity"
        assert "next_open" in hours
        assert "next_close" in hours

        # Test crypto market hours
        crypto_hours = connector.get_market_hours("BTC/USD")
        assert crypto_hours["market_type"] == "crypto"

    def test_close_position(self, connector, mock_client) -> None:
        """Test closing a position."""
        mock_order = Mock()
        mock_order.id = "close-order"
        mock_order.symbol = "AAPL"
        mock_order.status = "filled"

        mock_client.close_position.return_value = mock_order

        with patch.object(connector, "_convert_alpaca_order") as mock_convert:
            mock_convert.return_value = OrderResult(
                order_id="close-order",
                client_order_id=None,
                symbol="AAPL",
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=100,
                filled_quantity=100,
                price=None,
                stop_price=None,
                avg_fill_price=155.0,
                status=OrderStatus.FILLED,
                timestamp=datetime.now(),
            )

            result = connector.close_position("AAPL")

            assert result.order_id == "close-order"
            assert result.symbol == "AAPL"
            mock_client.close_position.assert_called_once()

    def test_validate_order_invalid_symbol(self, connector) -> None:
        """Test order validation for non-tradable symbol."""
        with patch.object(connector, "_get_symbol_info") as mock_get_info:
            mock_get_info.return_value = {
                "symbol": "INVALID",
                "tradable": False,
                "min_order_size": 1,
                "asset_class": "equity",
            }

            order = OrderRequest(
                symbol="INVALID",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=100,
            )

            with pytest.raises(ValidationError) as exc_info:
                connector.validate_order(order)

            assert "not tradable" in str(exc_info.value)

    def test_validate_order_below_minimum(self, connector) -> None:
        """Test order validation for quantity below minimum."""
        with patch.object(connector, "_get_symbol_info") as mock_get_info:
            mock_get_info.return_value = {
                "symbol": "AAPL",
                "tradable": True,
                "min_order_size": 10,
                "asset_class": "equity",
            }

            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=5,  # Below minimum
            )

            with pytest.raises(ValidationError) as exc_info:
                connector.validate_order(order)

            assert "below minimum" in str(exc_info.value)

    def test_validate_order_crypto_too_small(self, connector) -> None:
        """Test order validation for crypto quantity too small."""
        with patch.object(connector, "_get_symbol_info") as mock_get_info:
            mock_get_info.return_value = {
                "symbol": "BTC/USD",
                "tradable": True,
                "min_order_size": 1e-8,
                "asset_class": "crypto",
            }

            order = OrderRequest(
                symbol="BTC/USD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=1e-10,  # Too small
            )

            with pytest.raises(ValidationError) as exc_info:
                connector.validate_order(order)

            assert "below minimum" in str(exc_info.value)

    def test_validate_order_equity_stop_limit(self, connector) -> None:
        """Test order validation for equity stop limit orders."""
        with patch.object(connector, "_get_symbol_info") as mock_get_info:
            mock_get_info.return_value = {
                "symbol": "AAPL",
                "tradable": True,
                "min_order_size": 1,
                "asset_class": "equity",
            }

            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.STOP_LIMIT,
                quantity=100,
                price=150.0,
                stop_price=145.0,
            )

            with pytest.raises(ValidationError) as exc_info:
                connector.validate_order(order)

            assert "Stop limit orders not supported for equities" in str(exc_info.value)
