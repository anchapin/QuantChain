"""Interactive Brokers execution connector using ibapi library."""

import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Import QuantChain components
from ..tools.trading_execution import (
    AccountInfo,
    ExecutionError,
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

# Import ibapi components
try:
    from ibapi.client import EClient
    from ibapi.contract import Contract as IBContract
    from ibapi.order import Order as IBOrder
    from ibapi.order_state import OrderState
    from ibapi.wrapper import EWrapper
    from ibapi.common import OrderId, TickerId
    from ibapi.execution import ExecutionFilter
except ImportError as e:
    raise ImportError(
        "ibapi library is required. Install with: pip install ibapi>=9.81.1.post1"
    ) from e


class IBWrapper(EWrapper):
    """Wrapper class for IB API callbacks."""

    def __init__(self):
        super().__init__()
        self._order_statuses = {}
        self._account_summary = {}
        self._positions = []
        self._executions = []
        self._contracts = {}
        self._error_codes = {}
        self._next_order_id = None
        self._lock = threading.Lock()
        self._events = {}
        self._connected = False

    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        """Handle error messages from IB."""
        super().error(reqId, errorCode, errorString)

        # Store error code for later use
        self._error_codes[reqId] = (errorCode, errorString)

        # Signal waiting threads if this is a request-related error
        with self._lock:
            if reqId in self._events:
                self._events[reqId].set()

    def nextValidId(self, orderId: int):
        """Receive next valid order ID."""
        super().nextValidId(orderId)
        with self._lock:
            self._next_order_id = orderId

    def managedAccounts(self, accountsList: str):
        """Receive list of managed accounts."""
        super().managedAccounts(accountsList)

    def orderStatus(
        self,
        orderId: OrderId,
        status: str,
        filled: float,
        remaining: float,
        avgFillPrice: float,
        permId: int,
        parentId: int,
        lastFillPrice: float,
        clientId: int,
        whyHeld: str,
        mktCapPrice: float,
    ):
        """Receive order status updates."""
        super().orderStatus(
            orderId,
            status,
            filled,
            remaining,
            avgFillPrice,
            permId,
            parentId,
            lastFillPrice,
            clientId,
            whyHeld,
            mktCapPrice,
        )

        with self._lock:
            self._order_statuses[orderId] = {
                "status": status,
                "filled": filled,
                "remaining": remaining,
                "avgFillPrice": avgFillPrice,
                "lastFillPrice": lastFillPrice,
            }

    def openOrder(
        self,
        orderId: OrderId,
        contract: IBContract,
        order: IBOrder,
        orderState: OrderState,
    ):
        """Receive open order information."""
        super().openOrder(orderId, contract, order, orderState)

    def execDetails(self, reqId: int, contract: IBContract, execution):
        """Receive execution details."""
        super().execDetails(reqId, contract, execution)

        with self._lock:
            self._executions.append(
                {
                    "orderId": execution.orderId,
                    "clientId": execution.clientId,
                    "symbol": contract.symbol,
                    "side": execution.side,
                    "shares": execution.shares,
                    "price": execution.price,
                    "time": execution.time,
                }
            )

    def accountSummary(
        self, reqId: int, account: str, tag: str, value: str, currency: str
    ):
        """Receive account summary information."""
        super().accountSummary(reqId, account, tag, value, currency)

        with self._lock:
            self._account_summary[tag] = float(value)

    def position(
        self, account: str, contract: IBContract, position: float, avgCost: float
    ):
        """Receive position information."""
        super().position(account, contract, position, avgCost)

        with self._lock:
            self._positions.append(
                {
                    "symbol": contract.symbol,
                    "position": position,
                    "avgCost": avgCost,
                    "contract": contract,
                }
            )

    def contractDetails(self, reqId: int, contractDetails):
        """Receive contract details."""
        super().contractDetails(reqId, contractDetails)

        with self._lock:
            self._contracts[reqId] = contractDetails

    def connectAck(self):
        """Acknowledge successful connection."""
        super().connectAck()
        self._connected = True

    def connectionClosed(self):
        """Handle connection closure."""
        super().connectionClosed()
        self._connected = False


class IBClient(EClient):
    """Client class for IB API interactions."""

    def __init__(self, wrapper):
        super().__init__(wrapper)
        self._next_req_id = 1
        self._lock = threading.Lock()

    def get_next_req_id(self):
        """Get next request ID."""
        with self._lock:
            req_id = self._next_req_id
            self._next_req_id += 1
            return req_id


class IBExecutionConnector(TradingExecutionInterface):
    """Interactive Brokers execution connector using ibapi library."""

    # Enum mappings
    SIDE_MAPPING = {
        OrderSide.BUY: "BUY",
        OrderSide.SELL: "SELL",
    }

    TYPE_MAPPING = {
        OrderType.MARKET: "MKT",
        OrderType.LIMIT: "LMT",
        OrderType.STOP: "STP",
        OrderType.STOP_LIMIT: "STP LMT",
    }

    TIF_MAPPING = {
        TimeInForce.DAY: "DAY",
        TimeInForce.GTC: "GTC",
        TimeInForce.IOC: "IOC",
        TimeInForce.FOK: "FOK",
    }

    STATUS_MAPPING = {
        "PendingSubmit": OrderStatus.PENDING,
        "PreSubmitted": OrderStatus.PENDING,
        "Submitted": OrderStatus.PENDING,
        "Filled": OrderStatus.FILLED,
        "PartiallyFilled": OrderStatus.PARTIALLY_FILLED,
        "Cancelled": OrderStatus.CANCELLED,
        "ApiCancelled": OrderStatus.CANCELLED,
        "Inactive": OrderStatus.REJECTED,
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
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.timeout = timeout
        self.readonly = readonly
        self.account = account

        # Initialize IB wrapper and client
        self.wrapper = IBWrapper()
        self.client = IBClient(self.wrapper)
        self._connected = False
        self._ready_event = self.wrapper._ready_event = threading.Event()

        # Connect to IB Gateway/TWS
        self._connect()

    def _connect(self) -> None:
        """Establish connection to IB Gateway/TWS."""
        try:
            # Connect to IB
            self.client.connect(self.host, self.port, self.client_id)

            # Start the message processing thread
            self.api_thread = threading.Thread(
                target=self.run_message_loop, daemon=True
            )
            self.api_thread.start()

            # Wait for connection and next valid ID
            if not self._ready_event.wait(timeout=self.timeout):
                self.client.disconnect()
                raise ExecutionError(f"Connection timeout after {self.timeout} seconds")

            if not self.wrapper._connected:
                raise ExecutionError("Failed to connect to IB Gateway/TWS")

        except ConnectionRefusedError as e:
            raise ExecutionError(
                "Cannot connect to IB Gateway/TWS. Ensure Gateway/TWS is running."
            ) from e
        except Exception as e:
            raise ExecutionError(f"Failed to connect to IB: {str(e)}") from e

    def run_message_loop(self):
        """Run the IB API message loop."""
        try:
            self.client.run()
        except Exception as e:
            print(f"Error in message loop: {e}")

    def _wait_for_response(self, req_id: int, timeout: Optional[float] = None) -> bool:
        """Wait for a response to a request."""
        if req_id not in self.wrapper._events:
            self.wrapper._events[req_id] = threading.Event()

        return self.wrapper._events[req_id].wait(timeout or self.timeout)

    def _create_contract(self, symbol: str) -> IBContract:
        """Create appropriate IB Contract based on symbol format."""
        symbol = symbol.upper().strip()
        contract = IBContract()

        # Check for forex pair (e.g., EURUSD)
        if len(symbol) == 6 and symbol[:3].isalpha() and symbol[3:].isalpha():
            contract.symbol = symbol[:3]
            contract.secType = "CASH"
            contract.currency = symbol[3:]
            contract.exchange = "IDEALPRO"
            return contract

        # Check for option format (e.g., AAPL 20231215 150 C)
        parts = symbol.split()
        if len(parts) >= 4:
            ticker = parts[0]
            date_str = parts[1]
            strike_str = parts[2]
            right = parts[3]

            # Validate components
            ticker_valid = ticker.isalpha()
            date_valid = (
                len(date_str) == 6 or len(date_str) == 8
            ) and date_str.isdigit()
            strike_valid = (
                strike_str.replace(".", "", 1).isdigit()
                if "." in strike_str
                else strike_str.isdigit()
            )
            right_valid = right.upper() in ["C", "P"]

            if ticker_valid and date_valid and strike_valid and right_valid:
                contract.symbol = ticker
                contract.secType = "OPT"
                contract.currency = "USD"
                contract.exchange = "SMART"

                # Convert date based on format
                if len(date_str) == 6:
                    # YYMMDD to YYYYMMDD
                    date = "20" + date_str[:2] + date_str[2:4] + date_str[4:]
                else:
                    # YYYYMMDD - already in correct format
                    date = date_str
                contract.lastTradeDateOrContractMonth = date
                contract.strike = float(strike_str)
                contract.right = "CALL" if right.upper() == "C" else "PUT"
                contract.multiplier = "100"
                return contract

        # Check for futures format (e.g., ESZ3)
        if len(symbol) >= 2 and symbol[:-1].isalpha() and symbol[-1].isdigit():
            root = symbol[:-1]
            year_code = symbol[-1]

            # Simple mapping for month codes if present
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

            # Check if second to last character is a month code
            if len(root) >= 2 and root[-1].upper() in month_map:
                month_code = root[-1].upper()
                root = root[:-1]
                month = month_map[month_code]

                # Handle year code - single digit maps to current decade
                year_code_num = int(year_code)
                current_year = 2023  # Should be dynamic
                decade = (current_year // 10) * 10
                year = decade + year_code_num
                if year < current_year:
                    year += 10

                contract.symbol = root
                contract.secType = "FUT"
                contract.currency = "USD"
                contract.exchange = "CME"
                contract.lastTradeDateOrContractMonth = f"{year}{month}"
                return contract

        # Default to stock
        contract.symbol = symbol
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        return contract

    def _qualify_contract(self, contract: IBContract) -> bool:
        """Qualify contract with IB to get complete details."""
        try:
            req_id = self.client.get_next_req_id()
            self.client.reqContractDetails(req_id, contract)

            if not self._wait_for_response(req_id, timeout=5):
                return False

            return req_id in self.wrapper._contracts
        except Exception as e:
            raise ExecutionError(f"Failed to qualify contract: {str(e)}") from e

    def _convert_order_to_ib(self, order: OrderRequest) -> IBOrder:
        """Convert OrderRequest to IB Order object."""
        ib_order = IBOrder()

        # Set order type
        order_type = self.TYPE_MAPPING.get(order.order_type)
        if not order_type:
            raise ValidationError(f"Unsupported order type: {order.order_type}")
        ib_order.orderType = order_type

        # Set action and quantity
        ib_order.action = self.SIDE_MAPPING[order.side]
        ib_order.totalQuantity = order.quantity

        # Set price based on order type
        if order.order_type == OrderType.LIMIT:
            ib_order.lmtPrice = order.price
        elif order.order_type == OrderType.STOP:
            ib_order.auxPrice = order.stop_price
        elif order.order_type == OrderType.STOP_LIMIT:
            ib_order.lmtPrice = order.price
            ib_order.auxPrice = order.stop_price

        # Set time in force
        ib_order.tif = self.TIF_MAPPING.get(order.time_in_force, "DAY")

        return ib_order

    def _convert_order_status(self, status: str) -> OrderStatus:
        """Map IB order status to OrderStatus enum."""
        return self.STATUS_MAPPING.get(status, OrderStatus.PENDING)

    def _convert_ib_order_type(self, order_type: str) -> OrderType:
        """Map IB order type to OrderType enum."""
        type_mapping = {
            "MKT": OrderType.MARKET,
            "LMT": OrderType.LIMIT,
            "STP": OrderType.STOP,
            "STP LMT": OrderType.STOP_LIMIT,
        }
        return type_mapping.get(order_type, OrderType.MARKET)

    def place_order(self, order: OrderRequest) -> OrderResult:
        """Place a trading order and return the result."""
        # Validate order
        self.validate_order(order)

        try:
            # Get next valid order ID
            if not self.wrapper._next_order_id:
                time.sleep(1)  # Wait for nextValidId message

            if not self.wrapper._next_order_id:
                raise ExecutionError("No valid order ID available")

            order_id = self.wrapper._next_order_id
            self.wrapper._next_order_id += 1

            # Create and qualify contract
            contract = self._create_contract(order.symbol)
            if not self._qualify_contract(contract):
                raise ValidationError(f"Invalid contract: {order.symbol}")

            # Convert order to IB format
            ib_order = self._convert_order_to_ib(order)

            # Place order
            self.client.placeOrder(order_id, contract, ib_order)

            # Create result with pending status
            return OrderResult(
                order_id=str(order_id),
                client_order_id=getattr(order, "client_order_id", None),
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=order.quantity,
                filled_quantity=0,
                price=getattr(order, "price", None),
                stop_price=getattr(order, "stop_price", None),
                avg_fill_price=None,
                status=OrderStatus.PENDING,
                timestamp=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            raise ExecutionError(f"Failed to place order: {str(e)}") from e

    def cancel_order(self, order_id: str) -> OrderResult:
        """Cancel an existing order."""
        try:
            # Convert string order_id to int
            order_id_int = int(order_id)

            # Cancel the order
            self.client.cancelOrder(order_id_int)

            # Get updated order status
            return self.get_order(order_id)

        except ValueError as e:
            raise ValidationError(f"Invalid order ID: {order_id}") from e
        except Exception as e:
            raise ExecutionError(f"Failed to cancel order: {str(e)}") from e

    def get_order(self, order_id: str) -> OrderResult:
        """Retrieve order status and details."""
        try:
            # Convert string order_id to int
            order_id_int = int(order_id)

            # Get order status from wrapper
            with self.wrapper._lock:
                order_status = self.wrapper._order_statuses.get(order_id_int)

            if not order_status:
                raise OrderNotFoundError(f"Order not found: {order_id}")

            # Convert to OrderResult
            return OrderResult(
                order_id=order_id,
                client_order_id=None,  # Not available from order status
                symbol="UNKNOWN",  # Would need to track this separately
                side=OrderSide.BUY,  # Would need to track this separately
                order_type=OrderType.MARKET,  # Would need to track this separately
                quantity=order_status.get("filled", 0)
                + order_status.get("remaining", 0),
                filled_quantity=order_status.get("filled", 0),
                price=None,  # Would need to track this separately
                stop_price=None,
                avg_fill_price=order_status.get("avgFillPrice"),
                status=self._convert_order_status(order_status.get("status")),
                timestamp=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

        except ValueError as e:
            raise ValidationError(f"Invalid order ID: {order_id}") from e
        except Exception as e:
            raise ExecutionError(f"Failed to get order: {str(e)}") from e

    def get_account(self) -> AccountInfo:
        """Retrieve account information."""
        try:
            # Request account summary
            req_id = self.client.get_next_req_id()
            tags = "NetLiquidation,AvailableFunds,BuyingPower,TotalCashValue"
            self.client.reqAccountSummary(req_id, "All", tags)

            if not self._wait_for_response(req_id, timeout=5):
                raise ExecutionError("Timeout getting account summary")

            with self.wrapper._lock:
                summary = self.wrapper._account_summary.copy()
                positions = list(self.wrapper._positions)

            # Extract key values
            net_liquidation = summary.get("NetLiquidation", 0.0)
            available_funds = summary.get("AvailableFunds", 0.0)
            buying_power = summary.get("BuyingPower", 0.0)
            total_cash = summary.get("TotalCashValue", 0.0)

            # Convert positions
            quantchain_positions = []
            for pos in positions:
                if pos["position"] != 0:
                    quantchain_positions.append(
                        Position(
                            symbol=pos["symbol"],
                            quantity=pos["position"],
                            avg_entry_price=pos["avgCost"],
                            current_price=pos[
                                "avgCost"
                            ],  # Using avg cost as current price
                            market_value=pos["position"] * pos["avgCost"],
                            unrealized_pnl=0.0,
                            unrealized_pnl_percent=0.0,
                        )
                    )

            return AccountInfo(
                account_id=self.account or str(self.client_id),
                buying_power=buying_power,
                cash=total_cash,
                portfolio_value=net_liquidation,
                positions=quantchain_positions,
                margin_available=available_funds,
            )

        except Exception as e:
            raise ExecutionError(f"Failed to get account info: {str(e)}") from e

    def get_positions(self) -> List[Position]:
        """Retrieve current open positions."""
        try:
            # Request positions
            self.client.reqPositions()
            time.sleep(1)  # Wait for position data

            with self.wrapper._lock:
                positions = list(self.wrapper._positions)

            # Convert to Position objects
            quantchain_positions = []
            for pos in positions:
                if pos["position"] != 0:
                    quantchain_positions.append(
                        Position(
                            symbol=pos["symbol"],
                            quantity=pos["position"],
                            avg_entry_price=pos["avgCost"],
                            current_price=pos[
                                "avgCost"
                            ],  # Using avg cost as current price
                            market_value=pos["position"] * pos["avgCost"],
                            unrealized_pnl=0.0,
                            unrealized_pnl_percent=0.0,
                        )
                    )

            return quantchain_positions

        except Exception as e:
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
            # Request executions
            req_id = self.client.get_next_req_id()
            self.client.reqExecutions(req_id, ExecutionFilter())

            if not self._wait_for_response(req_id, timeout=10):
                raise ExecutionError("Timeout getting execution history")

            with self.wrapper._lock:
                executions = list(self.wrapper._executions)

            # Convert to OrderResult objects
            orders = []
            for exec in executions:
                order_result = OrderResult(
                    order_id=str(exec["orderId"]),
                    client_order_id=exec.get("clientId"),
                    symbol=exec["symbol"],
                    side=OrderSide.BUY if exec["side"] == "BOT" else OrderSide.SELL,
                    order_type=OrderType.MARKET,  # Default to market
                    quantity=exec["shares"],
                    filled_quantity=exec["shares"],
                    price=None,
                    stop_price=None,
                    avg_fill_price=exec["price"],
                    status=OrderStatus.FILLED,
                    timestamp=exec["time"],
                )

                # Apply filters
                if symbol and order_result.symbol != symbol:
                    continue
                if status and order_result.status != status:
                    continue
                if start_date and order_result.timestamp < start_date:
                    continue
                if end_date and order_result.timestamp > end_date:
                    continue

                orders.append(order_result)

            # Sort by timestamp descending
            orders.sort(key=lambda x: x.timestamp, reverse=True)

            # Apply limit
            if limit:
                orders = orders[:limit]

            return orders

        except Exception as e:
            raise ExecutionError(f"Failed to get order history: {str(e)}") from e

    def is_market_open(self, symbol: Optional[str] = None) -> bool:
        """Check if the market is open for trading."""
        # For simplicity, return True
        # In a real implementation, you would check market hours for the specific symbol
        return True

    def validate_order(self, order: OrderRequest) -> None:
        """Validate order parameters."""
        # Call parent validation
        super().validate_order(order)

        # IB-specific validation
        if not order.symbol or len(order.symbol.strip()) == 0:
            raise ValidationError("Symbol is required")

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed information about a symbol."""
        try:
            # Create and qualify contract
            contract = self._create_contract(symbol)

            req_id = self.client.get_next_req_id()
            self.client.reqContractDetails(req_id, contract)

            if not self._wait_for_response(req_id, timeout=5):
                return {"symbol": symbol}

            with self.wrapper._lock:
                details = self.wrapper._contracts.get(req_id)
                if not details:
                    return {"symbol": symbol}

            return {
                "symbol": symbol,
                "name": details.longName or symbol,
                "security_type": details.underSecType or "STK",
                "exchange": details.exchange,
                "currency": details.currency,
                "min_tick": details.minTick,
                "price_precision": (
                    len(str(details.minTick).split(".")[1])
                    if "." in str(details.minTick)
                    else 0
                ),
                "multiplier": details.multiplier,
            }

        except Exception as e:
            raise ExecutionError(f"Failed to get symbol info: {str(e)}") from e

    def disconnect(self) -> None:
        """Disconnect from IB Gateway/TWS."""
        try:
            self.client.disconnect()
        except Exception:
            pass  # Ignore errors during disconnection

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.disconnect()
