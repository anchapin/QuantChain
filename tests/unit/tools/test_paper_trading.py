"""Tests for paper trading executor."""



import pytest
from quantchain.tools.paper_trading import (
from quantchain.tools.trading_execution import (

    FixedSlippage,
    ImmediateFill,
    NoSlippage,
    PaperTradingExecutor,
    PerformanceMetrics,
    RandomSlippage,
    VolumeSlippage,
)
    ExecutionError,
    OrderNotFoundError,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
    ValidationError,
)


class TestSlippageModels:
    """Test cases for slippage models."""



def test_no_slippage(self) -> None:
        """Test NoSlippage model."""
        slippage = NoSlippage()
        order = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100)

        result = slippage.apply_slippage(order, 150.0)
        assert result == 150.0



def test_fixed_slippage_buy(self) -> None:
        """Test FixedSlippage model for buy orders."""
        slippage = FixedSlippage(slippage_percent=0.1)
        order = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100)

        result = slippage.apply_slippage(order, 150.0)
        # Buy orders get worse price (higher)
        assert result == 150.0 + (150.0 * 0.001)  # 0.1% of 150 = 0.15



def test_fixed_slippage_sell(self) -> None:
        """Test FixedSlippage model for sell orders."""
        slippage = FixedSlippage(slippage_percent=0.1)
        order = OrderRequest("AAPL", OrderSide.SELL, OrderType.MARKET, 100)

        result = slippage.apply_slippage(order, 150.0)
        # Sell orders get worse price (lower)
        assert result == 150.0 - (150.0 * 0.001)



def test_volume_slippage(self) -> None:
        """Test VolumeSlippage model."""
        slippage = VolumeSlippage(base_slippage=0.05, volume_threshold=100000)

        # Small order - minimal slippage
        small_order = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100)
        small_price = 150.0
        small_result = slippage.apply_slippage(small_order, small_price)

        # Large order - more slippage
        large_order = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 1000)
        large_price = 150.0
        large_result = slippage.apply_slippage(large_order, large_price)

        assert large_result > small_result  # Large order has more slippage



def test_random_slippage_range(self) -> None:
        """Test RandomSlippage model produces values in expected range."""
        slippage = RandomSlippage(min_slippage=0.0, max_slippage=0.2)
        order = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100)

        # Test multiple slippage applications
        results: list = [
            slippage.apply_slippage(order, 150.0) for _ in range(100)
        ]

        # Should vary around 150.0
        assert min(results) >= 149.7  # 150 - (150 * 0.002)
        assert max(results) <= 150.3  # 150 + (150 * 0.002)


class TestFillModel:
    """Test cases for fill model."""



def test_immediate_fill_market_order(self) -> None:
        """Test ImmediateFill model for market orders."""
        fill_model = ImmediateFill()
        buy_order = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100)
        sell_order = OrderRequest("AAPL", OrderSide.SELL, OrderType.MARKET, 100)

        # Market orders should always fill
        assert fill_model.should_fill(buy_order, 150.0) is True
        assert fill_model.should_fill(sell_order, 150.0) is True



def test_immediate_fill_limit_order(self) -> None:
        """Test ImmediateFill model for limit orders."""
        fill_model = ImmediateFill()

        # Buy limit order - fill when price <= limit
        buy_order = OrderRequest(
            "AAPL", OrderSide.BUY, OrderType.LIMIT, 100, price=150.0
        )
        assert fill_model.should_fill(buy_order, 149.0) is True  # Below limit
        assert fill_model.should_fill(buy_order, 151.0) is False  # Above limit

        # Sell limit order - fill when price >= limit
        sell_order = OrderRequest(
            "AAPL", OrderSide.SELL, OrderType.LIMIT, 100, price=150.0
        )
        assert fill_model.should_fill(sell_order, 151.0) is True  # Above limit
        assert fill_model.should_fill(sell_order, 149.0) is False  # Below limit



def test_immediate_fill_stop_order(self) -> None:
        """Test ImmediateFill model for stop orders."""
        fill_model = ImmediateFill()

        # Buy stop order - fill when price >= stop
        buy_stop = OrderRequest(
            "AAPL", OrderSide.BUY, OrderType.STOP, 100, stop_price=155.0
        )
        assert fill_model.should_fill(buy_stop, 156.0) is True  # Above stop
        assert fill_model.should_fill(buy_stop, 154.0) is False  # Below stop

        # Sell stop order - fill when price <= stop
        sell_stop = OrderRequest(
            "AAPL", OrderSide.SELL, OrderType.STOP, 100, stop_price=145.0
        )
        assert fill_model.should_fill(sell_stop, 144.0) is True  # Below stop
        assert fill_model.should_fill(sell_stop, 146.0) is False  # Above stop


class TestPerformanceMetrics:
    """Test cases for PerformanceMetrics."""



def test_initial_metrics(self) -> None:
        """Test initial performance metrics."""
        metrics = PerformanceMetrics()

        assert metrics.total_return == 0.0
        assert metrics.win_rate == 0.0
        assert metrics.total_trades == 0
        assert metrics.winning_trades == 0
        assert metrics.losing_trades == 0
        assert metrics.gross_profit == 0.0
        assert metrics.gross_loss == 0.0
        assert metrics.max_drawdown == 0.0
        assert metrics.sharpe_ratio is None
        assert metrics.profit_factor is None



def test_update_metrics_winning_trade(self) -> None:
        """Test updating metrics with a winning trade."""
        metrics = PerformanceMetrics()
        equity_curve: list = [100000, 105000]

        metrics.update_metrics(500.0, equity_curve)

        assert metrics.total_trades == 1
        assert metrics.winning_trades == 1
        assert metrics.losing_trades == 0
        assert metrics.win_rate == 100.0
        assert metrics.gross_profit == 500.0
        assert metrics.gross_loss == 0.0
        assert metrics.total_return == 5.0  # (105000 - 100000) / 100000 * 100
        assert metrics.profit_factor is None  # No losses yet



def test_update_metrics_losing_trade(self) -> None:
        """Test updating metrics with a losing trade."""
        metrics = PerformanceMetrics()
        equity_curve: list = [100000, 95000]

        metrics.update_metrics(-500.0, equity_curve)

        assert metrics.total_trades == 1
        assert metrics.winning_trades == 0
        assert metrics.losing_trades == 1
        assert metrics.win_rate == 0.0
        assert metrics.gross_profit == 0.0
        assert metrics.gross_loss == 500.0
        assert metrics.total_return == -5.0
        assert metrics.profit_factor == 0.0  # No profits yet



def test_update_metrics_multiple_trades(self) -> None:
        """Test updating metrics with multiple trades."""
        metrics = PerformanceMetrics()
        equity_curve: list = [100000, 105000, 98000, 102000]

        # Winning trade
        metrics.update_metrics(500.0, [100000, 105000])
        # Losing trade
        metrics.update_metrics(-700.0, [100000, 105000, 98000])
        # Winning trade
        metrics.update_metrics(400.0, equity_curve)

        assert metrics.total_trades == 3
        assert metrics.winning_trades == 2
        assert metrics.losing_trades == 1
        assert metrics.win_rate == pytest.approx(66.67, rel=0.01)  # 2/3 * 100
        assert metrics.gross_profit == 900.0  # 500 + 400
        assert metrics.gross_loss == 700.0
        assert metrics.profit_factor == pytest.approx(1.29, rel=0.01)  # 900/700


class TestPaperTradingExecutor:
    """Test cases for PaperTradingExecutor."""

    @pytest.fixture


def executor(self) -> PaperTradingExecutor:
        """Create a paper trading executor."""
        return PaperTradingExecutor(
            initial_cash=100000.0,
            commission_per_trade=1.0,
            commission_per_share=0.01,
            slippage_model=FixedSlippage(
                slippage_percent=0.1
            ),  # Use fixed slippage for predictable tests
            fill_model=ImmediateFill(),
        )



def test_initialization(self) -> None:
        """Test executor initialization."""
        executor = PaperTradingExecutor(
            initial_cash=50000.0, commission_per_trade=2.5, commission_per_share=0.005
        )

        assert executor.initial_cash == 50000.0
        assert executor.cash == 50000.0
        assert executor.commission_per_trade == 2.5
        assert executor.commission_per_share == 0.005
        assert len(executor.positions) == 0
        assert len(executor.orders) == 0
        assert executor.equity_curve == [50000.0]



def test_place_buy_order(self, executor: PaperTradingExecutor) -> None:
        """Test placing a buy order."""
        executor.set_market_price("AAPL", 150.0)

        order = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        result = executor.place_order(order)

        assert result.status == OrderStatus.FILLED
        assert result.symbol == "AAPL"
        assert result.quantity == 100
        assert result.filled_quantity == 100
        assert result.avg_fill_price > 150.0  # Slippage for buy order

        # Check cash deduction
        expected_cost = (
            result.avg_fill_price * 100 + 1.0 + (0.01 * 100)
        )  # price + commission
        assert pytest.approx(executor.cash, rel=0.001) == (100000.0 - expected_cost)

        # Check position
        assert "AAPL" in executor.positions
        position = executor.positions["AAPL"]
        assert position.quantity == 100
        assert position.avg_entry_price == result.avg_fill_price



def test_place_sell_order(self, executor: PaperTradingExecutor) -> None:
        """Test placing a sell order."""
        # First create a position
        executor.set_market_price("AAPL", 150.0)
        buy_order = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100)
        executor.place_order(buy_order)

        # Update price for sale
        executor.set_market_price("AAPL", 160.0)

        # Place sell order
        sell_order = OrderRequest("AAPL", OrderSide.SELL, OrderType.MARKET, 100)
        result = executor.place_order(sell_order)

        assert result.status == OrderStatus.FILLED
        assert result.avg_fill_price < 160.0  # Slippage for sell order

        # Position should be closed
        assert "AAPL" not in executor.positions

        # Check cash increase
        assert executor.cash > 95000  # Should have more cash than after initial buy



def test_insufficient_funds(self, executor: PaperTradingExecutor) -> None:
        """Test order with insufficient funds."""
        executor.set_market_price("AAPL", 150.0)

        # Order larger than available cash
        large_order = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 10000)

        with pytest.raises(ExecutionError) as exc_info:
            executor.place_order(large_order)

        assert "Insufficient funds" in str(exc_info.value)



def test_insufficient_position(self, executor: PaperTradingExecutor) -> None:
        """Test sell order larger than position."""
        executor.set_market_price("AAPL", 150.0)

        # Try to sell without having position
        sell_order = OrderRequest("AAPL", OrderSide.SELL, OrderType.MARKET, 100)

        with pytest.raises(ExecutionError) as exc_info:
            executor.place_order(sell_order)

        assert "Insufficient position" in str(exc_info.value)



def test_limit_order(self, executor: PaperTradingExecutor) -> None:
        """Test limit order behavior."""
        executor.set_market_price("AAPL", 150.0)

        # Limit buy below market - should fill
        buy_order = OrderRequest(
            "AAPL", OrderSide.BUY, OrderType.LIMIT, 100, price=151.0
        )
        result = executor.place_order(buy_order)
        assert result.status == OrderStatus.FILLED

        # Limit buy above market - should not fill
        executor.set_market_price("AAPL", 150.0)
        buy_order2 = OrderRequest(
            "AAPL", OrderSide.BUY, OrderType.LIMIT, 100, price=149.0
        )
        result2 = executor.place_order(buy_order2)
        assert result2.status == OrderStatus.PENDING



def test_stop_order(self, executor: PaperTradingExecutor) -> None:
        """Test stop order behavior."""
        executor.set_market_price("AAPL", 150.0)

        # Stop buy above current price - should not fill yet
        buy_stop = OrderRequest(
            "AAPL", OrderSide.BUY, OrderType.STOP, 100, stop_price=155.0
        )
        result = executor.place_order(buy_stop)
        assert result.status == OrderStatus.PENDING

        # Update price to trigger stop
        executor.set_market_price("AAPL", 156.0)
        # In current implementation, stop orders are checked at order placement
        # This is a limitation of the simple fill model



def test_cancel_order(self, executor: PaperTradingExecutor) -> None:
        """Test order cancellation."""
        executor.set_market_price("AAPL", 150.0)

        # Create a pending order
        limit_order = OrderRequest(
            "AAPL", OrderSide.BUY, OrderType.LIMIT, 100, price=140.0
        )
        result = executor.place_order(limit_order)

        assert result.status == OrderStatus.PENDING

        # Cancel the order
        cancelled = executor.cancel_order(result.order_id)
        assert cancelled.status == OrderStatus.CANCELLED



def test_cancel_nonexistent_order(self, executor: PaperTradingExecutor) -> None:
        """Test canceling non-existent order."""
        with pytest.raises(OrderNotFoundError):
            executor.cancel_order("non-existent")



def test_get_account(self, executor: PaperTradingExecutor) -> None:
        """Test getting account information."""
        # Place some trades
        executor.set_market_price("AAPL", 150.0)
        buy_order = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100)
        executor.place_order(buy_order)

        account = executor.get_account()

        assert account.account_id == "PAPER_TRADING"
        assert account.cash < 100000.0  # Cash reduced by trade and commission
        assert (
            account.portfolio_value >= 99000.0
        )  # Portfolio includes position value (accounting for commissions)
        assert len(account.positions) == 1
        assert account.positions[0].symbol == "AAPL"



def test_get_positions(self, executor: PaperTradingExecutor) -> None:
        """Test getting positions."""
        # Create a position
        executor.set_market_price("AAPL", 150.0)
        buy_order = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100)
        executor.place_order(buy_order)

        # Update market price
        executor.set_market_price("AAPL", 160.0)

        positions = executor.get_positions()

        assert len(positions) == 1
        position = positions[0]
        assert position.symbol == "AAPL"
        assert position.quantity == 100
        assert position.current_price == 160.0
        assert position.unrealized_pnl > 0  # Profit
        assert position.unrealized_pnl_percent > 0



def test_get_order_history(self, executor: PaperTradingExecutor) -> None:
        """Test getting order history."""
        # Place multiple orders
        executor.set_market_price("AAPL", 150.0)
        order1 = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100)
        executor.place_order(order1)

        executor.set_market_price("MSFT", 300.0)
        order2 = OrderRequest("MSFT", OrderSide.BUY, OrderType.MARKET, 50)
        executor.place_order(order2)

        # Get all history
        all_history = executor.get_order_history()
        assert len(all_history) == 2

        # Filter by symbol
        aapl_history = executor.get_order_history(symbol="AAPL")
        assert len(aapl_history) == 1
        assert aapl_history[0].symbol == "AAPL"

        # Filter by status
        filled_orders = executor.get_order_history(status=OrderStatus.FILLED)
        assert len(filled_orders) == 2

        # Limit results
        limited_history = executor.get_order_history(limit=1)
        assert len(limited_history) == 1



def test_performance_metrics_tracking(self, executor: PaperTradingExecutor) -> None:
        """Test performance metrics are tracked correctly."""
        # Simulate some trades
        executor.set_market_price("AAPL", 150.0)
        buy_order = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100)
        executor.place_order(buy_order)

        executor.set_market_price("AAPL", 160.0)
        sell_order = OrderRequest("AAPL", OrderSide.SELL, OrderType.MARKET, 100)
        executor.place_order(sell_order)

        metrics = executor.get_performance_metrics()

        assert metrics.total_trades == 1
        assert metrics.total_return > 0  # Should be profitable
        assert len(executor.equity_curve) > 1



def test_set_market_price(self, executor: PaperTradingExecutor) -> None:
        """Test setting market prices."""
        executor.set_market_price("AAPL", 150.0)
        assert executor._get_market_price("AAPL") == 150.0

        # Test invalid price
        with pytest.raises(ValidationError):
            executor.set_market_price("AAPL", -10.0)



def test_update_market_data(self, executor: PaperTradingExecutor) -> None:
        """Test updating market data for multiple symbols."""
        symbols: list = ["AAPL", "MSFT", "GOOGL"]
        executor.update_market_data(symbols)

        # Should have prices for all symbols
        assert all(symbol in executor.market_prices for symbol in symbols)
        assert all(executor.market_prices[symbol] > 0 for symbol in symbols)



def test_reset(self, executor: PaperTradingExecutor) -> None:
        """Test resetting the executor state."""
        # Make some trades
        executor.set_market_price("AAPL", 150.0)
        buy_order = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100)
        executor.place_order(buy_order)

        # Reset
        executor.reset()

        assert executor.cash == executor.initial_cash
        assert len(executor.positions) == 0
        assert len(executor.orders) == 0
        assert executor.equity_curve == [executor.initial_cash]
        assert len(executor.market_prices) == 0



def test_export_trade_history(self, executor: PaperTradingExecutor) -> None:
        """Test exporting trade history."""
        executor.set_market_price("AAPL", 150.0)
        order = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100)
        executor.place_order(order)

        df = executor.export_trade_history()

        assert len(df) == 1
        assert df.iloc[0]["symbol"] == "AAPL"
        assert df.iloc[0]["side"] == "buy"
        assert df.iloc[0]["order_type"] == "market"
        assert df.iloc[0]["quantity"] == 100
        assert df.iloc[0]["status"] == "filled"



def test_is_market_open(self, executor: PaperTradingExecutor) -> None:
        """Test market is always open for paper trading."""
        assert executor.is_market_open() is True
        assert executor.is_market_open("AAPL") is True
        assert executor.is_market_open("BTC/USD") is True
