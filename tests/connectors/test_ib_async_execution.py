"""
Unit tests for IBAsyncExecutionConnector.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pandas import DataFrame

from ib_async import Contract, Trade
from quantchain.connectors.ib_async_execution import IBAsyncExecutionConnector
from quantchain.tools.execution import OrderRequest, OrderSide, OrderStatus, OrderType


@pytest.mark.asyncio
class TestIBAsyncExecutionConnector:
    """Test cases for IBAsyncExecutionConnector."""

    async def test_connect_disconnect(self):
        """Test connection and disconnection."""
        connector = IBAsyncExecutionConnector()

        # Mock connectAsync on the instance, not the class
        with patch.object(
            connector.ib, "connectAsync", new_callable=AsyncMock
        ) as mock_connect:
            with patch.object(
                connector.ib, "ibkrAccountSummaryAsync", new_callable=AsyncMock
            ) as mock_accounts:
                mock_accounts.return_value = [MagicMock(account="DU12345")]

                # Test connect
                result = await connector._connect_async()
                assert result is True
                assert connector._connected is True
                assert connector.account == "DU12345"
                mock_connect.assert_called_once()

                # Test disconnect
                with patch.object(connector.ib, "disconnect") as mock_disconnect:
                    await connector._disconnect_async()
                    assert connector._connected is False
                    mock_disconnect.assert_called_once()

    async def test_place_order(self):
        """Test placing an order."""
        connector = IBAsyncExecutionConnector(account="DU12345")
        connector._connected = True

        # Mock contract qualification
        with patch.object(
            connector.ib, "qualifyContractsAsync", new_callable=AsyncMock
        ) as mock_qualify:
            mock_contract = Contract(
                symbol="AAPL", secType="STK", currency="USD", exchange="SMART"
            )
            mock_qualify.return_value = [mock_contract]

            # Mock placeOrder
            with patch.object(
                connector.ib, "placeOrderAsync", new_callable=AsyncMock
            ) as mock_place:
                mock_trade = MagicMock(spec=Trade)
                mock_trade.order.permId = 12345
                mock_trade.orderStatus.status = "Submitted"
                mock_trade.orderStatus.filled = 0.0
                mock_trade.orderStatus.avgFillPrice = 0.0
                mock_trade.filled = 0.0
                mock_trade.remaining = 10.0
                mock_trade.avgFillPrice = 0.0
                mock_place.return_value = mock_trade

                order_request = OrderRequest(
                    symbol="AAPL",
                    side=OrderSide.BUY,
                    quantity=10.0,
                    order_type=OrderType.MARKET,
                )

                result = await connector.place_order_async(order_request)

                assert result.order_id == "12345"
                assert result.status == OrderStatus.SUBMITTED
                mock_place.assert_called_once()

    async def test_cancel_order(self):
        """Test cancelling an order."""
        connector = IBAsyncExecutionConnector(account="DU12345")
        connector._connected = True

        # Setup existing order
        mock_trade = MagicMock(spec=Trade)
        mock_trade.order.permId = 12345
        connector._orders["12345"] = mock_trade

        with patch.object(
            connector.ib, "cancelOrderAsync", new_callable=AsyncMock
        ) as mock_cancel:
            result = await connector.cancel_order_async("12345")

            assert result is True
            mock_cancel.assert_called_once_with(mock_trade.order)

    async def test_get_positions(self):
        """Test retrieving positions."""
        connector = IBAsyncExecutionConnector(account="DU12345")
        connector._connected = True

        print(f"DEBUG: connector.ib type: {type(connector.ib)}")
        print(
            f"DEBUG: connector.ib.positionsAsync type: {type(connector.ib.positionsAsync)}"
        )

        with patch.object(
            connector.ib, "positionsAsync", new_callable=AsyncMock
        ) as mock_positions:
            # Mock IB position
            mock_pos = MagicMock()
            mock_pos.contract.symbol = "AAPL"
            mock_pos.position = 100.0
            mock_pos.avgCost = 150.0
            mock_positions.return_value = [mock_pos]

            # Mock current price
            with patch.object(
                connector, "_get_current_price", new_callable=AsyncMock
            ) as mock_price:
                mock_price.return_value = 160.0

                positions = await connector.get_positions_async()

                assert len(positions) == 1
                assert positions[0].symbol == "AAPL"
                assert positions[0].quantity == 100.0
                assert positions[0].unrealized_pl == 1000.0  # (160 - 150) * 100

    async def test_get_account_info(self):
        """Test retrieving account info."""
        connector = IBAsyncExecutionConnector(account="DU12345")
        connector._connected = True

        with patch.object(
            connector.ib, "accountSummaryAsync", new_callable=AsyncMock
        ) as mock_summary:
            # Mock summary items
            mock_cash = MagicMock(tag="TotalCashValue", value="10000.0")
            mock_value = MagicMock(tag="NetLiquidation", value="20000.0")
            mock_power = MagicMock(tag="BuyingPower", value="40000.0")
            mock_summary.return_value = [mock_cash, mock_value, mock_power]

            info = await connector.get_account_info()

            assert info.cash == 10000.0
            assert info.portfolio_value == 20000.0
            assert info.buying_power == 40000.0

    async def test_get_market_data(self):
        """Test retrieving market data."""
        connector = IBAsyncExecutionConnector(account="DU12345")
        connector._connected = True

        with patch.object(
            connector.ib, "reqMktDataAsync", new_callable=AsyncMock
        ) as mock_mkt:
            # Mock ticker
            mock_ticker = MagicMock()
            mock_ticker.bid = 149.0
            mock_ticker.ask = 151.0
            mock_ticker.last = 150.0
            mock_ticker.close = 148.0
            mock_ticker.volume = 1000000
            mock_ticker.midpoint.return_value = 150.0
            mock_mkt.return_value = mock_ticker

            # Test bid
            data_bid = await connector.get_market_data("AAPL", tick_type="bid")
            assert data_bid["bid"] == 149.0

            # Test ask
            data_ask = await connector.get_market_data("AAPL", tick_type="ask")
            assert data_ask["ask"] == 151.0

            # Test mid
            data_mid = await connector.get_market_data("AAPL", tick_type="mid")
            assert data_mid["mid"] == 150.0

    async def test_get_historical_data(self):
        """Test retrieving historical data."""
        connector = IBAsyncExecutionConnector(account="DU12345")
        connector._connected = True

        with patch.object(
            connector.ib, "reqHistoricalDataAsync", new_callable=AsyncMock
        ) as mock_hist:
            # Mock bars
            mock_bar = MagicMock()
            mock_bar.date = "2023-01-01"
            mock_bar.open = 100.0
            mock_bar.high = 110.0
            mock_bar.low = 90.0
            mock_bar.close = 105.0
            mock_bar.volume = 1000
            mock_hist.return_value = [mock_bar]

            df = await connector.get_historical_data("AAPL", "1 D", "1 day")

            assert isinstance(df, DataFrame)
            assert not df.empty
            assert df.iloc[0]["close"] == 105.0

    def test_create_ib_order(self):
        """Test IB order creation logic."""
        connector = IBAsyncExecutionConnector()

        # Test Market Order
        req_market = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10.0,
            order_type=OrderType.MARKET,
        )
        order_market = connector._create_ib_order(req_market)
        assert order_market.orderType == "MKT"
        assert order_market.action == "BUY"
        assert order_market.totalQuantity == 10.0

        # Test Limit Order
        req_limit = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            quantity=5.0,
            order_type=OrderType.LIMIT,
            price=150.0,
        )
        order_limit = connector._create_ib_order(req_limit)
        assert order_limit.orderType == "LMT"
        assert order_limit.action == "SELL"
        assert order_limit.lmtPrice == 150.0
