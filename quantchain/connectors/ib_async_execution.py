"""Interactive Brokers execution connector using ib_async library."""

import asyncio
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Import QuantChain components
from ..tools.trading_execution import (
    AccountInfo,
    ExecutionError,
    InsufficientFundsError,
    OrderNotFoundError,
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    TimeInForce,
    TradingExecutionInterface,
    ValidationError,
)

# IB Async compatibility guard
IB_ASYNC_AVAILABLE = False
try:
    from ib_async import (
        IB,
        Contract,
        Forex,
        Future,
        LimitOrder,
        MarketOrder,
        Option,
        Order,
        RequestError,
        Stock,
        StopLimitOrder,
        StopOrder,
        Trade,
    )

    IB_ASYNC_AVAILABLE = True
except ImportError:
    # Set all ib_async imports to None for mock testing
    IB = None
    Contract = None
    Forex = None
    Future = None
    LimitOrder = None
    MarketOrder = None
    Option = None
    Order = None
    RequestError = None
    Stock = None
    StopLimitOrder = None
    StopOrder = None
    Trade = None
    IB_ASYNC_AVAILABLE = False


class IBExecutionConnector(TradingExecutionInterface):
    """Interactive Brokers execution connector using ib_async library."""

    # Enum mappings
    SIDE_MAPPING = {
        OrderSide.BUY: "BUY",
        OrderSide.SELL: "SELL",
    }

    TYPE_MAPPING = {
        OrderType.MARKET: MarketOrder,
        OrderType.LIMIT: LimitOrder,
        OrderType.STOP: StopOrder,
        OrderType.STOP_LIMIT: StopLimitOrder,
    }

    TIF_MAPPING = {
        TimeInForce.DAY: "DAY",
        TimeInForce.GTC: "GTC",
        TimeInForce.IOC: "IOC",
        TimeInForce.FOK: "FOK",
    }

    STATUS_MAPPING = {
        "Submitted": OrderStatus.PENDING,
        "PreSubmitted": OrderStatus.PENDING,
        "Filled": OrderStatus.FILLED,
        "PartiallyFilled": OrderStatus.PARTIALLY_FILLED,
        "Cancelled": OrderStatus.CANCELLED,
        "Inactive": OrderStatus.REJECTED,
        "ApiCancelled": OrderStatus.CANCELLED,
        "PendingSubmit": OrderStatus.PENDING,
        "PendingCancel": OrderStatus.PENDING,
    }

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 1,
        timeout: int = 10,
        readonly: bool = False,
        account: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize IB execution connector.

        Args:
            host: IB Gateway/TWS host address
            port: Connection port (7497 for TWS paper, 7496 for TWS live,
                 4002 for Gateway paper, 4001 for Gateway live)
            client_id: Unique client identifier (1-32)
            timeout: Connection timeout in seconds
            readonly: Read-only mode, no order placement
            account: Specific account for multi-account setups
            **kwargs: Additional configuration parameters

        Raises:
            ImportError: If ib_async library is not installed
        """
        if not IB_ASYNC_AVAILABLE:
            raise ImportError(
                "ib_async library is required. Install with: pip install ib_async>=1.0.0"
            )

        self.host = host
        self.port = port
        self.client_id = client_id
        self.timeout = timeout
        self.readonly = readonly
        self.account = account

        # Initialize IB client
        self.ib = IB()

        # Handle event loop creation - don't create a new loop if one is already running
        try:
            self._loop = asyncio.get_running_loop()
            self._own_loop = False
        except RuntimeError:
            # No running loop, create our own
            self._loop = asyncio.new_event_loop()
            self._own_loop = True

        self._order_map: Dict[str, Trade] = {}

        # Connect to IB Gateway/TWS
        self._connect()

    def _connect(self) -> None:
        """Establish connection to IB Gateway/TWS."""
        try:
            # Enable exception-based error handling
            self.ib.RaiseRequestErrors = True

            # Connect to IB
            self._run_async(
                self.ib.connectAsync(
                    host=self.host,
                    port=self.port,
                    clientId=self.client_id,
                    timeout=self.timeout,
                    readonly=self.readonly,
                    account=self.account,
                )
            )
        except ConnectionRefusedError as e:
            raise ExecutionError(
                "Cannot connect to IB Gateway/TWS. Ensure Gateway/TWS is running."
            ) from e
        except asyncio.TimeoutError as e:
            raise ExecutionError(
                f"Connection timeout after {self.timeout} seconds"
            ) from e
        except Exception as e:
            raise ExecutionError(f"Failed to connect to IB: {str(e)}") from e

    def _run_async(self, coro: Any, timeout: Optional[float] = None) -> Any:
        """Run async coroutine synchronously."""
        try:
            if timeout:
                # Wrap the coroutine with wait_for
                wrapped_coro = asyncio.wait_for(coro, timeout=timeout)

                # Handle execution based on whether we own the loop
                if self._own_loop:
                    return self._loop.run_until_complete(wrapped_coro)
                else:
                    # Create a task in the running loop and wait for it
                    return asyncio.run_coroutine_threadsafe(
                        wrapped_coro, self._loop
                    ).result(
                        timeout=timeout + 1
                    )  # Add buffer to the timeout
            else:
                # Handle execution based on whether we own the loop
                if self._own_loop:
                    return self._loop.run_until_complete(coro)
                else:
                    # Create a task in the running loop and wait for it
                    return asyncio.run_coroutine_threadsafe(coro, self._loop).result()
        except asyncio.TimeoutError as e:
            raise ExecutionError(f"Operation timed out: {str(e)}") from e
        except Exception as e:
            raise ExecutionError(f"Async operation failed: {str(e)}") from e

    def _create_contract(self, symbol: str) -> Contract:
        """Create appropriate IB Contract based on symbol format."""
        symbol = symbol.upper().strip()

        # Check for forex pair (e.g., EURUSD)
        if re.match(r"^[A-Z]{3}[A-Z]{3}$", symbol) and len(symbol) == 6:
            base = symbol[:3]
            quote = symbol[3:]
            contract = Forex()
            contract.symbol = base
            contract.currency = quote
            contract.secType = "CASH"
            return contract

        # Check for option format (e.g., AAPL 20231215 150 C)
        # Parse manually to avoid regex issues
        parts = symbol.split()
        if len(parts) >= 4:
            ticker = parts[0]
            date_str = parts[1]
            strike_str = parts[2]
            right = parts[3]

            # Validate components
            ticker_valid = ticker.isalpha()
            date_valid = len(date_str) == 6 and date_str.isdigit()
            strike_valid = (
                strike_str.replace(".", "", 1).isdigit()
                if "." in strike_str
                else strike_str.isdigit()
            )
            right_valid = right in ["C", "P"]

            if ticker_valid and date_valid and strike_valid and right_valid:

                # Convert YYMMDD to YYYYMMDD
                date = f"20{date_str[:2]}{date_str[2:4]}{date_str[4:]}"
                strike = float(strike_str)
                right = "CALL" if right.upper() == "C" else "PUT"
                return Option(ticker, date, strike, right, "")

        option_match = None

        if option_match:
            ticker, date_str, strike_str, right = option_match.groups()
            # Convert YYMMDD to YYYYMMDD
            date = f"20{date_str[:2]}{date_str[2:4]}{date_str[4:]}"
            strike = float(strike_str)
            right = "CALL" if right.upper() == "C" else "PUT"
            return Option(ticker, date, strike, right, "")

        # Check for futures format (e.g., ESZ3)
        futures_match = re.match(r"^([A-Z]+)([A-Z])(\d)$", symbol)
        if futures_match:
            root, month_code, year_code = futures_match.groups()
            # Simple mapping for month codes
            month_map = {
                "F": "01",
                "G": "02",
                "H": "03",
                "J": "04",
                "K": "05",
                "M": "06",
                "N": "07",
                "Q": "08",
                "U": "09",
                "V": "10",
                "X": "11",
                "Z": "12",
            }
            month = month_map.get(month_code.upper(), "01")
            # Handle year code - single digit maps to current decade
            # For simplicity, map 0-9 to 2020-2029
            year_code_num = int(year_code)
            current_year = 2023  # Should be dynamic, using 2023 for now
            decade = (current_year // 10) * 10
            year = decade + year_code_num
            if year < current_year:
                year += 10  # Add decade if year is in past
            expiry = f"{year}{month}"

            contract = Future()
            contract.symbol = root
            contract.lastTradeDateOrContractMonth = expiry
            contract.secType = "FUT"
            return contract

        # Default to stock
        contract = Stock()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    def _qualify_contract(self, contract: Contract) -> Contract:
        """Qualify contract with IB to get complete details."""
        try:
            qualified = self._run_async(self.ib.qualifyContractsAsync(contract))
            if not qualified:
                raise ValidationError(f"Contract could not be qualified: {contract}")
            return qualified[0]
        except RequestError as e:
            if e.code == 321:  # Invalid contract
                raise ValidationError(f"Invalid contract: {str(e)}") from e
            raise ExecutionError(f"Failed to qualify contract: {str(e)}") from e

    def _convert_order_to_ib(self, order: OrderRequest) -> Order:
        """Convert OrderRequest to IB Order object."""
        # Create order based on type
        order_class = self.TYPE_MAPPING.get(order.order_type)
        if not order_class:
            raise ValidationError(f"Unsupported order type: {order.order_type}")

        # Map side and create order
        action = self.SIDE_MAPPING[order.side]

        if order.order_type == OrderType.MARKET:
            ib_order = order_class()
            ib_order.action = action
            ib_order.totalQuantity = order.quantity
        elif order.order_type == OrderType.LIMIT:
            ib_order = order_class()
            ib_order.action = action
            ib_order.totalQuantity = order.quantity
            ib_order.lmtPrice = order.price
        elif order.order_type == OrderType.STOP:
            ib_order = order_class()
            ib_order.action = action
            ib_order.totalQuantity = order.quantity
            ib_order.auxPrice = order.stop_price
        elif order.order_type == OrderType.STOP_LIMIT:
            ib_order = order_class()
            ib_order.action = action
            ib_order.totalQuantity = order.quantity
            ib_order.lmtPrice = order.price
            ib_order.auxPrice = order.stop_price
        else:
            raise ValidationError(f"Unsupported order type: {order.order_type}")

        # Set time in force
        ib_order.tif = self.TIF_MAPPING.get(order.time_in_force, "DAY")

        # Set client order ID if provided
        if order.client_order_id:
            ib_order.clientId = order.client_order_id

        return ib_order

    def _convert_ib_order_to_result(self, trade: Trade) -> OrderResult:
        """Convert IB Trade object to OrderResult."""
        status = self._convert_order_status(trade.orderStatus.status)

        # Calculate average fill price from fills if available
        avg_fill_price = None
        if trade.orderStatus.filled > 0:
            avg_fill_price = trade.orderStatus.avgFillPrice

        return OrderResult(
            order_id=str(trade.orderId),
            client_order_id=trade.clientId if hasattr(trade, "clientId") else None,
            symbol=trade.contract.symbol,
            side=OrderSide.BUY if trade.action == "BUY" else OrderSide.SELL,
            order_type=self._convert_ib_order_type(trade.order.orderType),
            quantity=trade.totalQuantity,
            filled_quantity=trade.orderStatus.filled,
            price=getattr(trade.order, "lmtPrice", None),
            stop_price=getattr(trade.order, "auxPrice", None),
            avg_fill_price=avg_fill_price,
            status=status,
            timestamp=trade.log[0].time if trade.log else datetime.now(timezone.utc),
            updated_at=trade.log[-1].time if trade.log else datetime.now(timezone.utc),
        )

    def _convert_order_status(self, status: str) -> OrderStatus:
        """Map IB order status to OrderStatus enum."""
        return self.STATUS_MAPPING.get(status, OrderStatus.PENDING)

    def get_order_status(self, order_id: str) -> OrderResult:
        """Get the status of a specific order.

        Args:
            order_id: The IB order ID

        Returns:
            OrderResult: The order status and details

        Raises:
            OrderNotFoundError: If the order is not found
            ExecutionError: If there's an error fetching the order
        """
        if not self.is_connected():
            raise ExecutionError("Not connected to IB")

        try:
            # Get the order from IB
            # Try multiple approaches based on IB API version
            if hasattr(self.ib, "orders"):
                # For newer ib_async versions
                for order in self.ib.orders:
                    if str(order.orderId) == str(order_id):
                        return self._convert_ib_order_to_result(order)
                raise OrderNotFoundError(f"Order {order_id} not found")
            else:
                # For older versions or as fallback
                trade = self._run_async(self.ib.reqOpenOrderAsync(order_id))
                if not trade:
                    raise OrderNotFoundError(f"Order {order_id} not found")
                return self._convert_ib_order_to_result(trade)

            return self._convert_ib_order_to_result(trade)
        except Exception as e:
            raise ExecutionError(f"Failed to get order status: {str(e)}") from e

    def _convert_ib_order_type(self, order_type) -> OrderType:
        """Map IB order type to OrderType enum."""
        # Handle class objects
        if hasattr(order_type, "__name__"):
            class_name = order_type.__name__
        else:
            # Handle string input
            class_name = str(order_type)

        type_mapping = {
            "MarketOrder": OrderType.MARKET,
            "LimitOrder": OrderType.LIMIT,
            "StopOrder": OrderType.STOP,
            "StopLimitOrder": OrderType.STOP_LIMIT,
            "MKT": OrderType.MARKET,
            "LMT": OrderType.LIMIT,
            "STP": OrderType.STOP,
            "STP LMT": OrderType.STOP_LIMIT,
        }
        return type_mapping.get(class_name, OrderType.MARKET)

    def place_order(self, order: OrderRequest) -> OrderResult:
        """Place a trading order and return the result."""
        # Check if in readonly mode
        if self.readonly:
            raise ExecutionError("Cannot place orders in read-only mode")

        # Validate order
        self.validate_order(order)

        try:
            # Create and qualify contract
            contract = self._create_contract(order.symbol)
            qualified_contract = self._qualify_contract(contract)

            # Convert order to IB format
            ib_order = self._convert_order_to_ib(order)

            # Place order
            trade = self._run_async(self.ib.placeOrder(qualified_contract, ib_order))

            # Store trade for tracking
            self._order_map[str(trade.orderId)] = trade

            # Convert and return result
            return self._convert_ib_order_to_result(trade)

        except RequestError as e:
            if e.code == 201:  # Order not found
                raise OrderNotFoundError(f"Order not found: {str(e)}") from e
            elif e.code == 321:  # Invalid contract
                raise ValidationError(f"Invalid contract: {str(e)}") from e
            elif e.code == 10147:  # Insufficient funds
                raise InsufficientFundsError(f"Insufficient funds: {str(e)}") from e
            else:
                raise ExecutionError(f"Failed to place order: {str(e)}") from e
        except Exception as e:
            raise ExecutionError(f"Unexpected error placing order: {str(e)}") from e

    def cancel_order(self, order_id: str) -> OrderResult:
        """Cancel an existing order."""
        # Find the trade
        # Find trade
        trade = self._order_map.get(order_id)
        if not trade:
            # Search in active trades
            trades = self.ib.trades()
            for t in trades:
                if str(t.orderId) == order_id:
                    trade = t
                    break

        if not trade:
            raise OrderNotFoundError(f"Order not found: {order_id}")

        try:
            # Cancel the order
            self.ib.cancelOrder(trade.order)

            # Update and return result
            return self._convert_ib_order_to_result(trade)
        except RequestError as e:
            if e.code == 201:  # Order not found
                raise OrderNotFoundError(f"Order not found: {str(e)}") from e
            else:
                raise ExecutionError(f"Failed to cancel order: {str(e)}") from e

    def get_order(self, order_id: str) -> OrderResult:
        """Retrieve order status and details."""
        # Find the trade
        trade = self._order_map.get(order_id)
        if not trade:
            # Search in all trades and orders
            for t in self.ib.trades():
                if str(t.orderId) == order_id:
                    trade = t
                    break

            if not trade:
                for o in self.ib.openOrders():
                    if str(o.orderId) == order_id:
                        # Create a mock trade object
                        from unittest.mock import Mock

                        trade = Mock()
                        trade.orderId = o.orderId
                        trade.clientId = o.clientId
                        trade.action = o.action
                        trade.totalQuantity = o.totalQuantity
                        trade.contract = o.contract
                        trade.orderStatus = Mock()
                        trade.orderStatus.status = o.orderStatus
                        trade.orderStatus.filled = o.filledQuantity
                        trade.orderStatus.avgFillPrice = o.avgFillPrice
                        trade.order = o
                        trade.log = []
                        break

        if not trade:
            raise OrderNotFoundError(f"Order not found: {order_id}")

        return self._convert_ib_order_to_result(trade)

    def get_account(self) -> AccountInfo:
        """Retrieve account information."""
        try:
            # Get account summary using async API
            summary = self._run_async(self.ib.accountSummaryAsync(account=self.account))

            # Extract key values
            net_liquidation = 0.0
            available_funds = 0.0
            buying_power = 0.0
            total_cash = (
                0.0  # Default value in case TotalCashValue/TotalCash not returned
            )

            for item in summary:
                if item.tag == "NetLiquidation":
                    net_liquidation = float(item.value)
                elif item.tag == "AvailableFunds":
                    available_funds = float(item.value)
                elif item.tag == "BuyingPower":
                    buying_power = float(item.value)
                elif item.tag == "TotalCashValue":
                    total_cash = float(item.value)
                # Also handle "TotalCash" tag which may be returned by IB
                elif item.tag == "TotalCash":
                    total_cash = float(item.value)

            # Get positions
            positions = self.get_positions()

            return AccountInfo(
                account_id=self.account or str(self.ib.clientId),
                buying_power=buying_power,
                cash=total_cash,
                portfolio_value=net_liquidation,
                positions=positions,
                margin_available=available_funds,
            )
        except RequestError as e:
            raise ExecutionError(f"Failed to get account info: {str(e)}") from e

    def get_positions(self) -> List[Position]:
        """Retrieve current open positions."""
        try:
            # Use async method to get positions
            ib_positions = self._run_async(self.ib.positionsAsync())

            positions = []
            for pos in ib_positions:
                if pos.position != 0:  # Only include non-zero positions
                    symbol = pos.contract.symbol
                    quantity = pos.position
                    avg_cost = pos.avgCost

                    # Get current price (use avg cost if market data not available)
                    try:
                        # Try to get current price from market data
                        ticker = self.ib.reqMktData(pos.contract, "", False, False)
                        current_price = (
                            ticker.last
                            if hasattr(ticker, "last") and ticker.last
                            else avg_cost
                        )
                    except Exception:
                        current_price = avg_cost

                    # Calculate position metrics
                    market_value = quantity * current_price
                    unrealized_pnl = market_value - (quantity * avg_cost)
                    unrealized_pnl_percent = (
                        (unrealized_pnl / (quantity * avg_cost)) * 100
                        if quantity * avg_cost != 0
                        else 0
                    )

                    positions.append(
                        Position(
                            symbol=symbol,
                            quantity=quantity,
                            avg_entry_price=avg_cost,
                            current_price=current_price,
                            market_value=market_value,
                            unrealized_pnl=unrealized_pnl,
                            unrealized_pnl_percent=unrealized_pnl_percent,
                        )
                    )

            return positions
        except RequestError as e:
            raise ExecutionError(f"Failed to get positions: {str(e)}") from e

    def get_order_history(
        self,
        symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[OrderResult]:
        """Retrieve historical orders with optional filtering."""
        try:
            # Get all trades and fills
            trades = self.ib.trades()
            fills = self.ib.fills()

            # Combine and convert to OrderResult
            orders = []

            # Process trades
            for trade in trades:
                result = self._convert_ib_order_to_result(trade)

                # Apply filters
                if symbol and result.symbol != symbol:
                    continue
                if status and result.status != status:
                    continue
                if start_date and result.timestamp < start_date:
                    continue
                if end_date and result.timestamp > end_date:
                    continue

                orders.append(result)

            # Process fills (for fully executed orders not in trades)
            for fill in fills:
                # Skip if already processed
                if any(o.order_id == str(fill.orderId) for o in orders):
                    continue

                # Create OrderResult from fill
                result = OrderResult(
                    order_id=str(fill.orderId),
                    client_order_id=(
                        fill.clientId if hasattr(fill, "clientId") else None
                    ),
                    symbol=fill.contract.symbol,
                    side=OrderSide.BUY if fill.side == "BOT" else OrderSide.SELL,
                    order_type=OrderType.MARKET,  # Fills are typically market orders
                    quantity=fill.shares,
                    filled_quantity=fill.shares,
                    price=None,
                    stop_price=None,
                    avg_fill_price=fill.price,
                    status=OrderStatus.FILLED,
                    timestamp=fill.time,
                )

                # Apply filters
                if symbol and result.symbol != symbol:
                    continue
                if status and result.status != status:
                    continue
                if start_date and result.timestamp < start_date:
                    continue
                if end_date and result.timestamp > end_date:
                    continue

                orders.append(result)

            # Sort by timestamp descending
            orders.sort(key=lambda x: x.timestamp, reverse=True)

            # Apply limit
            if limit:
                orders = orders[:limit]

            return orders
        except RequestError as e:
            raise ExecutionError(f"Failed to get order history: {str(e)}") from e

    def is_market_open(self, symbol: Optional[str] = None) -> bool:
        """Check if the market is open for trading."""
        if not symbol:
            # Check general market status
            return True  # Default to true for simplicity

        # Check if forex (always open 24/5)
        if re.match(r"^[A-Z]{3}[A-Z]{3}$", symbol.upper()):
            return True

        try:
            # Create contract to check trading hours
            contract = self._create_contract(symbol)
            qualified_contract = self._qualify_contract(contract)

            # Get contract details
            details = self.ib.reqContractDetails(qualified_contract)
            if details:
                trading_hours = details[0].tradingHours
                if trading_hours:
                    # Parse trading hours (simplified)
                    # This is a complex topic involving timezone conversions
                    # For now, assume market is open if trading hours are set
                    return "CLOSED" not in trading_hours.upper()

            return True  # Default to open
        except Exception:
            return True  # Default to open on error

    def validate_order(self, order: OrderRequest) -> None:
        """Validate order parameters."""
        # Call parent validation
        super().validate_order(order)

        # IB-specific validation
        if not order.symbol or len(order.symbol.strip()) == 0:
            raise ValidationError("Symbol is required")

        # Try to create contract to validate symbol
        try:
            self._create_contract(order.symbol)
        except Exception as e:
            raise ValidationError(f"Invalid symbol format: {str(e)}") from e

        # Check quantity for fractional shares (if stock)
        if re.match(r"^[A-Z]+$", order.symbol.upper()):
            # For stocks, check if quantity meets minimum (typically 1)
            if order.quantity < 1:
                raise ValidationError("Stock order quantity must be at least 1")

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed information about a symbol."""
        try:
            # Create and qualify contract
            contract = self._create_contract(symbol)
            qualified_contract = self._qualify_contract(contract)

            # Get contract details
            details = self.ib.reqContractDetails(qualified_contract)
            if details:
                detail = details[0]
                return {
                    "symbol": symbol,
                    "name": detail.longName or symbol,
                    "security_type": detail.secType,
                    "exchange": detail.exchange,
                    "currency": detail.currency,
                    "min_tick": detail.minTick,
                    "price_precision": (
                        len(str(detail.minTick).split(".")[1])
                        if "." in str(detail.minTick)
                        else 0
                    ),
                    "multiplier": detail.multiplier,
                }

            return {"symbol": symbol}
        except RequestError as e:
            raise ExecutionError(f"Failed to get symbol info: {str(e)}") from e

    def disconnect(self) -> None:
        """Disconnect from IB Gateway/TWS."""
        try:
            self.ib.disconnect()
            if self._loop and not self._loop.is_closed():
                self._loop.close()
            self._order_map.clear()
        except Exception:
            pass  # Ignore errors during disconnection

    def is_connected(self) -> bool:
        """Check if connected to IB Gateway/TWS."""
        try:
            return self.ib.isConnected()
        except Exception:
            return False

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.disconnect()
