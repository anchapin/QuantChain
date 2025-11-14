"""Alpaca execution connector for equity and crypto trading."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..core.exceptions import AuthenticationError
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

# Alpaca compatibility guard
ALPACA_AVAILABLE = False
try:
    from alpaca.trading import OrderRequest as AlpacaOrderRequest
    from alpaca.trading import OrderSide as AlpacaOrderSide
    from alpaca.trading import OrderType as AlpacaOrderType
    from alpaca.trading import StopLossRequest, TakeProfitRequest
    from alpaca.trading import TimeInForce as AlpacaTimeInForce
    from alpaca.trading import TradingClient
    from alpaca.trading.requests import GetAssetsRequest

    ALPACA_AVAILABLE = True
except ImportError:
    pass


class AlpacaExecutionConnector(TradingExecutionInterface):
    """Alpaca execution connector supporting both equity and crypto markets."""

    # Mapping between standard and Alpaca enums
    SIDE_MAPPING = {
        OrderSide.BUY: AlpacaOrderSide.BUY,
        OrderSide.SELL: AlpacaOrderSide.SELL,
    }

    TYPE_MAPPING = {
        OrderType.MARKET: AlpacaOrderType.MARKET,
        OrderType.LIMIT: AlpacaOrderType.LIMIT,
        OrderType.STOP: AlpacaOrderType.STOP,
        OrderType.STOP_LIMIT: AlpacaOrderType.STOP_LIMIT,
    }

    TIME_IN_FORCE_MAPPING = {
        TimeInForce.DAY: AlpacaTimeInForce.DAY,
        TimeInForce.GTC: AlpacaTimeInForce.GTC,
        TimeInForce.IOC: AlpacaTimeInForce.IOC,
        TimeInForce.FOK: AlpacaTimeInForce.FOK,
    }

    # Reverse mapping for Alpaca to standard
    ALPACA_SIDE_MAPPING = {v: k for k, v in SIDE_MAPPING.items()}
    ALPACA_TYPE_MAPPING = {v: k for k, v in TYPE_MAPPING.items()}
    ALPACA_TIME_IN_FORCE_MAPPING = {v: k for k, v in TIME_IN_FORCE_MAPPING.items()}

    def __init__(self, api_key: str, api_secret: str, **kwargs: Any) -> None:
        """Initialize Alpaca execution connector.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            **kwargs: Additional configuration
                - use_paper: Whether to use paper trading (default: True)
                - base_url: Optional custom API base URL
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.use_paper = kwargs.get("use_paper", True)
        self.base_url = kwargs.get("base_url")

        try:
            # Initialize Alpaca trading client
            self.client = TradingClient(
                api_key, api_secret, paper=self.use_paper, url_override=self.base_url
            )

            # Cache for symbol information
            self._symbol_cache: Dict[str, Dict[str, Any]] = {}
            self._cache_timestamp: Optional[float] = None
            self._cache_ttl = 3600  # 1 hour

        except Exception as e:
            raise AuthenticationError(
                f"Failed to authenticate with Alpaca: {str(e)}"
            ) from e

    def _is_crypto_symbol(self, symbol: str) -> bool:
        """Check if symbol is a crypto pair."""
        return "-" in symbol or "/" in symbol

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to Alpaca format."""
        return symbol.replace("-", "/") if self._is_crypto_symbol(symbol) else symbol

    def _get_asset_class(self, symbol: str) -> str:
        """Determine asset class for symbol."""
        return "crypto" if self._is_crypto_symbol(symbol) else "equity"

    def _convert_order_status(self, alpaca_status: str) -> OrderStatus:
        """Convert Alpaca order status to standard OrderStatus."""
        status_mapping = {
            "new": OrderStatus.PENDING,
            "partially_filled": OrderStatus.PARTIALLY_FILLED,
            "filled": OrderStatus.FILLED,
            "done_for_day": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "expired": OrderStatus.EXPIRED,
            "replaced": OrderStatus.PENDING,
            "pending_cancel": OrderStatus.CANCELLED,
            "pending_replace": OrderStatus.PENDING,
            "accepted": OrderStatus.PENDING,
            "pending_new": OrderStatus.PENDING,
            "accepted_for_bidding": OrderStatus.PENDING,
            "rejected": OrderStatus.REJECTED,
            "suspended": OrderStatus.REJECTED,
        }
        return status_mapping.get(alpaca_status.lower(), OrderStatus.PENDING)

    def _convert_alpaca_order(self, alpaca_order: Any) -> OrderResult:
        """Convert Alpaca order to OrderResult."""

        # Helper function to safely convert to float
        def _safe_float(value: Any) -> Optional[float]:
            """Safely convert a value to float, handling strings and Mock objects."""
            if value is None:
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                # Handle case where value is a Mock object or cannot be converted
                return 0.0

        # Helper function to safely extract order_id from mock objects
        def _safe_get_id(order_obj: Any) -> str:
            """Safely extract order_id from both real and mock Alpaca order objects."""
            # Try direct attribute access first
            if hasattr(order_obj, "id"):
                return str(getattr(order_obj, "id"))
            # For mock objects, try common attributes
            if hasattr(order_obj, "order_id"):
                return str(getattr(order_obj, "order_id"))
            # Fallback to string representation
            return str(order_obj)

        return OrderResult(
            order_id=_safe_get_id(alpaca_order),
            client_order_id=getattr(alpaca_order, "client_order_id", None),
            symbol=alpaca_order.symbol,
            side=self.ALPACA_SIDE_MAPPING.get(alpaca_order.side, OrderSide.BUY),
            order_type=self.ALPACA_TYPE_MAPPING.get(
                alpaca_order.order_type, OrderType.MARKET
            ),
            quantity=_safe_float(alpaca_order.qty) or 0.0,
            filled_quantity=_safe_float(alpaca_order.filled_qty) or 0.0,
            price=_safe_float(alpaca_order.limit_price),
            stop_price=_safe_float(alpaca_order.stop_price),
            avg_fill_price=_safe_float(alpaca_order.filled_avg_price),
            status=self._convert_order_status(alpaca_order.status),
            timestamp=alpaca_order.submitted_at or datetime.now(timezone.utc),
            updated_at=alpaca_order.updated_at,
        )

    def _get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed symbol information from Alpaca."""
        try:
            # Try to get asset information
            request = GetAssetsRequest()
            if assets := self.client.get_all_assets(request):
                asset = assets[0] if isinstance(assets, list) else assets
                asset_class = getattr(asset, "asset_class", "equity")
                if hasattr(asset_class, "value"):
                    asset_class_str = asset_class.value
                else:
                    asset_class_str = str(asset_class)

                return {
                    "symbol": getattr(asset, "symbol", symbol),
                    "name": getattr(asset, "name", symbol),
                    "asset_class": asset_class_str,
                    "tradable": getattr(asset, "tradable", True),
                    "fractionable": getattr(asset, "fractionable", False),
                    "min_order_size": getattr(asset, "min_order_size", 1),
                    "price_precision": 4 if asset_class_str.lower() == "crypto" else 2,
                    "size_precision": 8 if asset_class_str.lower() == "crypto" else 0,
                }
        except Exception:
            pass

        # Return default info if asset lookup fails
        return {
            "symbol": symbol,
            "name": symbol,
            "asset_class": self._get_asset_class(symbol),
            "tradable": True,
            "fractionable": False,
            "min_order_size": 1,
            "price_precision": 2,
            "size_precision": 0,
        }

    def place_order(self, order: OrderRequest) -> OrderResult:
        """Place a trading order with Alpaca."""
        try:
            # Validate order
            self.validate_order(order)

            # Normalize symbol for Alpaca
            normalized_symbol = self._normalize_symbol(order.symbol)

            # Create Alpaca order request
            alpaca_request = AlpacaOrderRequest(
                symbol=normalized_symbol,
                qty=order.quantity,
                side=self.SIDE_MAPPING[order.side],
                type=self.TYPE_MAPPING[order.order_type],
                time_in_force=self.TIME_IN_FORCE_MAPPING[order.time_in_force],
                client_order_id=order.client_order_id,
            )

            # Add take profit and stop loss as needed
            if order.order_type == OrderType.LIMIT and order.price:
                alpaca_request.take_profit = TakeProfitRequest(limit_price=order.price)
            elif order.order_type == OrderType.STOP and order.stop_price:
                alpaca_request.stop_loss = StopLossRequest(stop_price=order.stop_price)
            elif order.order_type == OrderType.STOP_LIMIT:
                if order.stop_price:
                    alpaca_request.stop_loss = StopLossRequest(
                        stop_price=order.stop_price
                    )
                if order.price:
                    alpaca_request.take_profit = TakeProfitRequest(
                        limit_price=order.price
                    )

            # Submit order to Alpaca
            alpaca_order = self.client.submit_order(alpaca_request)

            # Convert and return result
            return self._convert_alpaca_order(alpaca_order)

        except Exception as e:
            error_message = str(e).lower()
            if "insufficient" in error_message or "balance" in error_message:
                raise InsufficientFundsError(f"Insufficient funds: {str(e)}") from e
            elif "invalid" in error_message or "validation" in error_message:
                raise ValidationError(f"Invalid order: {str(e)}") from e
            else:
                raise ExecutionError(f"Failed to place order: {str(e)}") from e

    def cancel_order(self, order_id: str) -> OrderResult:
        """Cancel an existing order."""
        try:
            # Cancel the order
            self.client.cancel_order_by_id(order_id)

            # Get updated order status
            alpaca_order = self.client.get_order_by_id(order_id)
            return self._convert_alpaca_order(alpaca_order)

        except Exception as e:
            # Check for specific error messages that indicate order not found
            error_msg = str(e).lower()
            if any(
                keyword in error_msg
                for keyword in [
                    "not found",
                    "does not exist",
                    "no such order",
                    "invalid order",
                ]
            ):
                raise OrderNotFoundError(f"Order {order_id} not found") from e
            raise ExecutionError(f"Failed to cancel order {order_id}: {str(e)}") from e

    def get_order(self, order_id: str) -> OrderResult:
        """Retrieve order status and details."""
        try:
            # Use simpler approach without complex request object
            alpaca_order = self.client.get_order_by_id(order_id)
            return self._convert_alpaca_order(alpaca_order)

        except Exception as e:
            # Check for specific error messages that indicate order not found
            error_msg = str(e).lower()
            if any(
                keyword in error_msg
                for keyword in [
                    "not found",
                    "does not exist",
                    "no such order",
                    "invalid order",
                ]
            ):
                raise OrderNotFoundError(f"Order {order_id} not found") from e
            raise ExecutionError(f"Failed to get order {order_id}: {str(e)}") from e

    def get_account(self) -> AccountInfo:
        """Retrieve account information."""
        try:
            # Get account from Alpaca
            account = self.client.get_account()

            # Handle both dictionary and object cases
            account_id = str(getattr(account, "id", "unknown"))
            buying_power = float(getattr(account, "buying_power", 0))
            cash = float(getattr(account, "cash", 0))
            portfolio_value = float(getattr(account, "portfolio_value", cash))

            # Get positions
            positions = self.get_positions()

            return AccountInfo(
                account_id=account_id,
                buying_power=buying_power,
                cash=cash,
                portfolio_value=portfolio_value,
                positions=positions,
                margin_available=(
                    float(getattr(account, "daytrading_buying_power", 0))
                    if hasattr(account, "daytrading_buying_power")
                    else None
                ),
            )

        except Exception as e:
            raise ExecutionError(f"Failed to get account info: {str(e)}") from e

    def get_positions(self) -> List[Position]:
        """Retrieve current open positions."""
        try:
            # Get positions from Alpaca
            alpaca_positions = self.client.get_all_positions()

            positions = []
            for pos in alpaca_positions:
                # Handle both dictionary and object cases
                symbol = str(getattr(pos, "symbol", "unknown"))
                quantity = float(getattr(pos, "qty", 0))
                avg_entry_price = float(getattr(pos, "avg_entry_price", 0))
                current_price = float(getattr(pos, "current_price", 0))
                market_value = float(getattr(pos, "market_value", 0))

                # Calculate unrealized P&L
                if abs(quantity) > 1e-10 and avg_entry_price > 0:
                    unrealized_pnl = (current_price - avg_entry_price) * abs(quantity)
                    unrealized_pnl_percent = (
                        (current_price - avg_entry_price) / avg_entry_price
                    ) * 100
                else:
                    unrealized_pnl = 0.0
                    unrealized_pnl_percent = 0.0

                positions.append(
                    Position(
                        symbol=symbol,
                        quantity=quantity,
                        avg_entry_price=avg_entry_price,
                        current_price=current_price,
                        market_value=market_value,
                        unrealized_pnl=unrealized_pnl,
                        unrealized_pnl_percent=unrealized_pnl_percent,
                    )
                )

            return positions

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
        """Retrieve historical orders."""
        try:
            # Build request with correct parameter names
            from alpaca.trading import GetOrdersRequest, QueryOrderStatus

            request = GetOrdersRequest(
                symbols=[symbol] if symbol else None,
                status=QueryOrderStatus(status.value) if status else None,
                after=start_date,
                until=end_date,
                limit=limit,
            )

            # Get orders from Alpaca
            alpaca_orders = self.client.get_orders(request)

            # Convert to standard format
            return [self._convert_alpaca_order(order) for order in alpaca_orders]

        except Exception as e:
            raise ExecutionError(f"Failed to get order history: {str(e)}") from e

    def is_market_open(self, symbol: Optional[str] = None) -> bool:
        """Check if the market is open for trading."""
        try:
            if symbol and self._is_crypto_symbol(symbol):
                # Crypto markets are always open
                return True

            # Get market clock
            clock = self.client.get_clock()
            return getattr(clock, "is_open", False)
        except Exception as e:
            raise ExecutionError(f"Failed to check market status: {str(e)}") from e

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed information about a symbol."""
        return self._get_symbol_info(symbol)

    def get_market_hours(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get market hours for a symbol or market."""
        try:
            clock = self.client.get_clock()

            is_open = getattr(clock, "is_open", False)

            return {
                "is_open": is_open,
                "next_open": getattr(clock, "next_open", None),
                "next_close": getattr(clock, "next_close", None),
                "timestamp": getattr(clock, "timestamp", datetime.now(timezone.utc)),
                "market_type": (
                    "crypto"
                    if (symbol and self._is_crypto_symbol(symbol))
                    else "equity"
                ),
            }

        except Exception as e:
            raise ExecutionError(f"Failed to get market hours: {str(e)}") from e

    def close_position(self, symbol: str) -> OrderResult:
        """Close position for a symbol (Alpaca-specific method)."""
        try:
            # Use simpler approach - close entire position
            order = self.client.close_position(symbol_or_asset_id=symbol)

            return self._convert_alpaca_order(order)

        except Exception as e:
            if "not found" in str(e).lower():
                raise OrderNotFoundError(f"No position found for {symbol}") from e
            raise ExecutionError(
                f"Failed to close position for {symbol}: {str(e)}"
            ) from e

    def validate_order(self, order: OrderRequest) -> None:
        """Validate order parameters with Alpaca-specific rules."""
        # Call base validation
        super().validate_order(order)

        # Get symbol information
        symbol_info = self._get_symbol_info(order.symbol)

        # Check if symbol is tradable
        if not symbol_info.get("tradable", True):
            raise ValidationError(f"Symbol {order.symbol} is not tradable")

        # Check minimum order size
        min_order_size = symbol_info.get("min_order_size", 1)
        if order.quantity < min_order_size:
            raise ValidationError(
                f"Order quantity {order.quantity} is below minimum {min_order_size}"
            )

        # For equities, validate order type
        if (
            symbol_info.get("asset_class") == "equity"
            and order.order_type == OrderType.STOP_LIMIT
        ):
            raise ValidationError("Stop limit orders not supported for equities")

        # For crypto, additional validation
        if self._is_crypto_symbol(order.symbol) and order.quantity < 1e-8:
            raise ValidationError("Crypto order quantity too small")
