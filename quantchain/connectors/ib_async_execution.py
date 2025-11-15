"""Interactive Brokers async execution connector for QuantChain."""

import asyncio
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple, Callable

from ib_async import IB, Contract, Order, OrderState, Trade, Position, PortfolioItem, ScanData, BarDataList, TagValue
from ib_async.contract import ContractDescription, ContractDetails
from ib_async.objects import BarData
from pandas import DataFrame, Series

from quantchain.connectors.base import BaseExecutionConnector
from quantchain.core.execution import (
    OrderRequest, OrderResult, OrderSide, OrderType, OrderStatus,
    AccountInfo, Position as QuantChainPosition, ExecutionError
)

logger = logging.getLogger(__name__)

# Error classes specific to IB async execution
class IBAsyncExecutionError(ExecutionError):
    """Base exception for IB async execution errors."""
    pass

class IBAsyncConnectionError(IBAsyncExecutionError):
    """Exception for connection errors."""
    pass

class IBAsyncContractError(IBAsyncExecutionError):
    """Exception for contract-related errors."""
    pass

class IBAsyncOrderError(IBAsyncExecutionError):
    """Exception for order-related errors."""
    pass

class IBAsyncDataError(IBAsyncExecutionError):
    """Exception for data retrieval errors."""
    pass

class IBAsyncExecutionConnector(BaseExecutionConnector):
    """
    Async Interactive Brokers execution connector using ib_async.

    This connector handles order placement, position management, and market data
    retrieval through the Interactive Brokers API in an asynchronous manner.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 1,
        account: Optional[str] = None,
        timeout: int = 10,
        readonly: bool = False
    ):
        """
        Initialize IB async execution connector.

        Args:
            host: IB gateway or TWS host address
            port: IB gateway or TWS port (7497 for TWS, 7496 for gateway)
            client_id: Client ID for IB connection
            account: Specific account to use
            timeout: Connection timeout in seconds
            readonly: If True, orders won't be placed
        """
        super().__init__()

        self.host = host
        self.port = port
        self.client_id = client_id
        self.account = account
        self.timeout = timeout
        self.readonly = readonly

        self.ib = IB()
        self._connected = False
        self._orders: Dict[str, Trade] = {}
        self._contracts: Dict[str, Contract] = {}
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._market_data_cache: Dict[str, DataFrame] = {}

        # Setup event handlers
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Setup event handlers for IB events."""
        self.ib.errorEvent += self._on_error
        self.ib.orderStatusEvent += self._on_order_status
        self.ib.updatePortfolioEvent += self._on_portfolio_update
        self.ib.positionEvent += self._on_position_update
        self.ib.accountValueEvent += self._on_account_value
        self.ib.contractDetailsEvent += self._on_contract_details

    async def connect(self) -> bool:
        """
        Connect to IB gateway/TWS.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self._connected:
                return True

            await self.ib.connectAsync(
                host=self.host,
                port=self.port,
                clientId=self.client_id,
                timeout=self.timeout
            )

            # If account not specified, use the first available one
            if not self.account:
                accounts = await self.ib.ibkrAccountSummaryAsync()
                if accounts:
                    self.account = accounts[0].account
                else:
                    raise IBAsyncConnectionError("No accounts found")

            self._connected = True
            logger.info(f"Connected to IB at {self.host}:{self.port} with account {self.account}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to IB: {e}")
            raise IBAsyncConnectionError(f"Failed to connect to IB: {e}")

    async def disconnect(self) -> None:
        """Disconnect from IB gateway/TWS."""
        if self._connected:
            self.ib.disconnect()
            self._connected = False
            logger.info("Disconnected from IB")

    async def is_connected(self) -> bool:
        """Check if connected to IB."""
        return self._connected and self.ib.isConnected()

    async def place_order(self, order_request: OrderRequest) -> OrderResult:
        """
        Place an order with IB.

        Args:
            order_request: Order request containing order details

        Returns:
            OrderResult with execution details
        """
        if not await self.is_connected():
            await self.connect()

        if self.readonly:
            raise IBAsyncOrderError("Cannot place order in readonly mode")

        try:
            # Get or create contract
            contract = await self._get_contract(order_request)

            # Create IB order
            order = self._create_ib_order(order_request)

            # Place order
            trade = await self.ib.placeOrderAsync(contract, order)

            # Store trade
            self._orders[trade.order.permId] = trade

            # Convert to OrderResult
            result = self._convert_trade_to_result(trade)

            logger.info(f"Placed order {result.order_id} for {order_request.symbol}")
            return result

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise IBAsyncOrderError(f"Failed to place order: {e}")

    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancellation successful, False otherwise
        """
        if not await self.is_connected():
            await self.connect()

        if self.readonly:
            raise IBAsyncOrderError("Cannot cancel order in readonly mode")

        try:
            # Find trade by order ID
            trade = None
            for t in self._orders.values():
                if str(t.order.permId) == order_id:
                    trade = t
                    break

            if not trade:
                logger.error(f"Order {order_id} not found")
                return False

            # Cancel order
            await self.ib.cancelOrderAsync(trade.order)

            logger.info(f"Canceled order {order_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    async def get_order(self, order_id: str) -> Optional[OrderResult]:
        """
        Get order details.

        Args:
            order_id: Order ID to retrieve

        Returns:
            OrderResult with order details, or None if not found
        """
        if not await self.is_connected():
            await self.connect()

        try:
            # Find trade by order ID
            trade = None
            for t in self._orders.values():
                if str(t.order.permId) == order_id:
                    trade = t
                    break

            if not trade:
                return None

            return self._convert_trade_to_result(trade)

        except Exception as e:
            logger.error(f"Failed to get order {order_id}: {e}")
            return None

    async def get_orders(self) -> List[OrderResult]:
        """
        Get all open orders.

        Returns:
            List of OrderResult objects
        """
        if not await self.is_connected():
            await self.connect()

        try:
            # Get all open trades
            trades = self.ib.openTrades()

            # Convert to OrderResult objects
            results = []
            for trade in trades:
                # Store trade if not already stored
                if trade.order.permId not in self._orders:
                    self._orders[trade.order.permId] = trade

                result = self._convert_trade_to_result(trade)
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            return []

    async def get_positions(self) -> List[QuantChainPosition]:
        """
        Get current positions.

        Returns:
            List of QuantChain position objects
        """
        if not await self.is_connected():
            await self.connect()

        try:
            # Get all positions
            ib_positions = await self.ib.positionsAsync()

            # Convert to QuantChain positions
            positions = []
            for pos in ib_positions:
                if pos.position != 0:  # Only include non-zero positions
                    # Get current price
                    contract = pos.contract
                    price = await self._get_current_price(contract)

                    # Create QuantChain position
                    position = QuantChainPosition(
                        symbol=self._get_symbol_from_contract(contract),
                        quantity=pos.position,
                        price=price,
                        market_value=pos.position * price if price else 0.0,
                        unrealized_pnl=pos.position * (price - pos.avgCost) if price else 0.0
                    )
                    positions.append(position)

            return positions

        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []

    async def get_account_info(self) -> AccountInfo:
        """
        Get account information.

        Returns:
            AccountInfo object with account details
        """
        if not await self.is_connected():
            await self.connect()

        try:
            # Get account summary
            summary = await self.ib.accountSummaryAsync()

            # Extract key values
            total_cash = 0.0
            portfolio_value = 0.0
            buying_power = 0.0

            for item in summary:
                if item.tag == "TotalCashValue":
                    total_cash = float(item.value)
                elif item.tag == "NetLiquidation":
                    portfolio_value = float(item.value)
                elif item.tag == "BuyingPower":
                    buying_power = float(item.value)

            return AccountInfo(
                account_id=self.account,
                cash=total_cash,
                portfolio_value=portfolio_value,
                buying_power=buying_power,
                total_equity=portfolio_value
            )

        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return AccountInfo(
                account_id=self.account,
                cash=0.0,
                portfolio_value=0.0,
                buying_power=0.0,
                total_equity=0.0
            )

    async def get_historical_data(
        self,
        symbol: str,
        duration: str,
        bar_size: str,
        what_to_show: str = "TRADES",
        use_rth: bool = True,
        end_date_time: Optional[datetime] = None
    ) -> DataFrame:
        """
        Get historical market data.

        Args:
            symbol: Symbol to get data for
            duration: Duration string (e.g., "1 D", "1 W", "1 M", "1 Y")
            bar_size: Bar size string (e.g., "1 min", "5 mins", "1 hour", "1 day")
            what_to_show: What to show (TRADES, MIDPOINT, BID, ASK, etc.)
            use_rth: Whether to use regular trading hours only
            end_date_time: End datetime for data retrieval

        Returns:
            DataFrame with historical data
        """
        if not await self.is_connected():
            await self.connect()

        try:
            # Create contract
            contract = self._create_contract_from_symbol(symbol)

            # Get historical data
            bars = await self.ib.reqHistoricalDataAsync(
                contract,
                endDateTime=end_date_time or "",
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=use_rth,
                formatDate=2
            )

            # Convert to DataFrame
            data = [
                {
                    "date": bar.date,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume
                }
                for bar in bars
            ]

            df = DataFrame(data)
            df.set_index("date", inplace=True)

            return df

        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            return DataFrame()

    async def get_market_data(
        self,
        symbol: str,
        tick_type: str = "mid",
        snapshot: bool = True
    ) -> Dict[str, Any]:
        """
        Get current market data.

        Args:
            symbol: Symbol to get data for
            tick_type: Type of data to get (bid, ask, last, mid, etc.)
            snapshot: Whether to get snapshot or streaming

        Returns:
            Dictionary with market data
        """
        if not await self.is_connected():
            await self.connect()

        try:
            # Create contract
            contract = self._create_contract_from_symbol(symbol)

            # Get market data
            ticker = await self.ib.reqMktDataAsync(contract, snapshot=snapshot)

            # Extract data
            data = {}

            if tick_type == "bid" and ticker.bid:
                data["bid"] = ticker.bid
            if tick_type == "ask" and ticker.ask:
                data["ask"] = ticker.ask
            if tick_type == "last" and ticker.last:
                data["last"] = ticker.last
            if tick_type == "mid" and ticker.midpoint():
                data["mid"] = ticker.midpoint()

            if ticker.close:
                data["close"] = ticker.close
            if ticker.volume:
                data["volume"] = ticker.volume

            return data

        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return {}

    async def get_contract_details(self, symbol: str) -> Dict[str, Any]:
        """
        Get contract details.

        Args:
            symbol: Symbol to get details for

        Returns:
            Dictionary with contract details
        """
        if not await self.is_connected():
            await self.connect()

        try:
            # Create contract
            contract = self._create_contract_from_symbol(symbol)

            # Get contract details
            details = await self.ib.reqContractDetailsAsync(contract)

            if not details:
                return {}

            # Extract details
            detail = details[0]
            return {
                "symbol": detail.contract.symbol,
                "sec_type": detail.contract.secType,
                "currency": detail.contract.currency,
                "exchange": detail.contract.exchange,
                "primary_exchange": detail.contract.primaryExchange,
                "description": detail.longName,
                "min_tick": detail.minTick,
                "price_magnifier": detail.priceMagnifier,
                "order_types": detail.validExchanges,
                "valid_exchanges": detail.validExchanges
            }

        except Exception as e:
            logger.error(f"Failed to get contract details for {symbol}: {e}")
            return {}

    async def _get_contract(self, order_request: OrderRequest) -> Contract:
        """Get or create contract for order."""
        symbol = order_request.symbol
        sec_type = order_request.security_type or "STK"
        currency = order_request.currency or "USD"
        exchange = order_request.exchange or "SMART"

        # Check cache first
        contract_key = f"{symbol}_{sec_type}_{currency}_{exchange}"
        if contract_key in self._contracts:
            return self._contracts[contract_key]

        # Create contract
        contract = Contract(
            symbol=symbol,
            secType=sec_type,
            currency=currency,
            exchange=exchange
        )

        # Qualify contract (fill in missing details)
        contracts = await self.ib.qualifyContractsAsync(contract)
        if contracts:
            contract = contracts[0]

        # Cache contract
        self._contracts[contract_key] = contract

        return contract

    def _create_contract_from_symbol(self, symbol: str, sec_type: str = "STK") -> Contract:
        """Create contract from symbol."""
        return Contract(
            symbol=symbol,
            secType=sec_type,
            currency="USD",
            exchange="SMART"
        )

    def _create_ib_order(self, order_request: OrderRequest) -> Order:
        """Create IB order from order request."""
        # Map order type
        order_type = self._map_order_type(order_request.order_type)

        # Map order side
        action = "BUY" if order_request.side == OrderSide.BUY else "SELL"

        # Create order
        order = Order(
            action=action,
            orderType=order_type,
            totalQuantity=abs(order_request.quantity),
        )

        # Set price for limit orders
        if order_request.order_type == OrderType.LIMIT and order_request.price:
            order.lmtPrice = order_request.price

        # Set stop price for stop orders
        if order_request.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and order_request.stop_price:
            order.auxPrice = order_request.stop_price

        # Set limit price for stop limit orders
        if order_request.order_type == OrderType.STOP_LIMIT and order_request.price:
            order.lmtPrice = order_request.price

        # Set time in force
        order.tif = "DAY"  # Default to day order

        # Set account
        order.account = self.account

        # Set order ID from request if provided
        if order_request.order_id:
            order.clientId = int(order_request.order_id)

        return order

    def _map_order_type(self, order_type: OrderType) -> str:
        """Map QuantChain order type to IB order type."""
        mapping = {
            OrderType.MARKET: "MKT",
            OrderType.LIMIT: "LMT",
            OrderType.STOP: "STP",
            OrderType.STOP_LIMIT: "STP LMT"
        }
        return mapping.get(order_type, "MKT")

    def _convert_trade_to_result(self, trade: Trade) -> OrderResult:
        """Convert IB trade to OrderResult."""
        # Map order status
        status = self._map_order_status(trade.orderStatus.status)

        # Calculate execution price
        price = 0.0
        if trade.orderStatus.filled > 0 and trade.orderStatus.avgFillPrice > 0:
            price = trade.orderStatus.avgFillPrice
        elif trade.order and hasattr(trade.order, 'lmtPrice') and trade.order.lmtPrice:
            price = trade.order.lmtPrice

        return OrderResult(
            order_id=str(trade.order.permId),
            client_order_id=str(trade.order.clientId) if trade.order.clientId else None,
            symbol=self._get_symbol_from_contract(trade.contract),
            side=OrderSide.BUY if trade.order.action == "BUY" else OrderSide.SELL,
            order_type=self._map_ib_order_type(trade.order.orderType),
            quantity=trade.order.totalQuantity,
            filled_quantity=trade.orderStatus.filled,
            price=price,
            status=status,
            time_in_force=trade.order.tif,
            stop_price=trade.order.auxPrice if hasattr(trade.order, 'auxPrice') else None,
            create_time=trade.log[0].time if trade.log else datetime.now(),
            update_time=trade.orderStatus.time if trade.orderStatus.time else datetime.now()
        )

    def _map_order_status(self, ib_status: str) -> OrderStatus:
        """Map IB order status to QuantChain order status."""
        mapping = {
            "PendingSubmit": OrderStatus.PENDING,
            "PendingCancel": OrderStatus.PENDING_CANCEL,
            "PreSubmitted": OrderStatus.PENDING,
            "Submitted": OrderStatus.SUBMITTED,
            "ApiPending": OrderStatus.SUBMITTED,
            "ApiCancelled": OrderStatus.CANCELLED,
            "Cancelled": OrderStatus.CANCELLED,
            "Filled": OrderStatus.FILLED,
            "Partial": OrderStatus.PARTIALLY_FILLED,
            "Inactive": OrderStatus.REJECTED
        }
        return mapping.get(ib_status, OrderStatus.UNKNOWN)

    def _map_ib_order_type(self, ib_type: str) -> OrderType:
        """Map IB order type to QuantChain order type."""
        mapping = {
            "MKT": OrderType.MARKET,
            "LMT": OrderType.LIMIT,
            "STP": OrderType.STOP,
            "STP LMT": OrderType.STOP_LIMIT
        }
        return mapping.get(ib_type, OrderType.MARKET)

    def _get_symbol_from_contract(self, contract: Contract) -> str:
        """Extract symbol from contract."""
        return contract.symbol

    async def _get_current_price(self, contract: Contract) -> Optional[float]:
        """Get current price for a contract."""
        try:
            ticker = await self.ib.reqMktDataAsync(contract, snapshot=True)
            return ticker.last or ticker.midpoint() or ticker.close
        except Exception:
            return None

    # Event handlers
    def _on_error(self, reqId, errorCode, errorString, contract):
        """Handle IB error events."""
        logger.error(f"IB Error {errorCode}: {errorString}")

    def _on_order_status(self, trade: Trade):
        """Handle order status updates."""
        logger.debug(f"Order status update: {trade.order.permId} - {trade.orderStatus.status}")

    def _on_portfolio_update(self, item: PortfolioItem):
        """Handle portfolio updates."""
        logger.debug(f"Portfolio update: {item.contract.symbol} - {item.position}")

    def _on_position_update(self, position: Position):
        """Handle position updates."""
        logger.debug(f"Position update: {position.contract.symbol} - {position.position}")

    def _on_account_value(self, value):
        """Handle account value updates."""
        logger.debug(f"Account value update: {value.tag} - {value.value}")

    def _on_contract_details(self, reqId, details):
        """Handle contract details."""
        logger.debug(f"Contract details received for reqId: {reqId}")
