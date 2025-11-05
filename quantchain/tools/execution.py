"""Alpaca execution tool for trading operations."""

from dataclasses import dataclass
from typing import Any, Dict

from ..connectors.alpaca_execution import AlpacaExecutionConnector
from ..tools.trading_execution import OrderRequest, OrderSide, OrderType, OrderResult


@dataclass
class AlpacaExecutionTool:
    """Tool for executing trades via Alpaca.

    This tool provides a simplified interface for market orders,
    wrapping the AlpacaExecutionConnector for use in trading agents.
    """

    connector: AlpacaExecutionConnector

    @classmethod
    def from_credentials(
        cls, api_key: str, api_secret: str, use_paper: bool = True, **kwargs: Any
    ) -> "AlpacaExecutionTool":
        """Create tool from Alpaca credentials.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            use_paper: Whether to use paper trading
            **kwargs: Additional connector configuration

        Returns:
            Configured AlpacaExecutionTool
        """
        connector = AlpacaExecutionConnector(
            api_key=api_key, api_secret=api_secret, use_paper=use_paper, **kwargs
        )
        return cls(connector=connector)

    def execute_market_order(
        self, symbol: str, side: str, quantity: float
    ) -> OrderResult:
        """Execute a market order.

        Args:
            symbol: Trading symbol (e.g., 'BTC/USD', 'AAPL')
            side: Order side ('buy' or 'sell')
            quantity: Order quantity

        Returns:
            OrderResult with execution details

        Raises:
            ValueError: If side is invalid
            ExecutionError: If order execution fails
        """
        # Validate side
        if side.lower() not in ["buy", "sell"]:
            raise ValueError(f"Invalid side: {side}. Must be 'buy' or 'sell'")

        # Convert to enum
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL

        # Create order request
        order_request = OrderRequest(
            symbol=symbol,
            side=order_side,
            order_type=OrderType.MARKET,
            quantity=quantity,
        )

        # Execute order
        return self.connector.place_order(order_request)

    def get_account_balance(self) -> Dict[str, float]:
        """Get current account balance information.

        Returns:
            Dictionary with balance information
        """
        account = self.connector.get_account()
        return {
            "buying_power": account.buying_power,
            "cash": account.cash,
            "portfolio_value": account.portfolio_value,
            "total_equity": account.total_equity,
        }

    def get_positions(self) -> list:
        """Get current open positions.

        Returns:
            List of position dictionaries
        """
        positions = self.connector.get_positions()
        return [
            {
                "symbol": pos.symbol,
                "quantity": pos.quantity,
                "avg_entry_price": pos.avg_entry_price,
                "current_price": pos.current_price,
                "market_value": pos.market_value,
                "unrealized_pnl": pos.unrealized_pnl,
                "unrealized_pnl_percent": pos.unrealized_pnl_percent,
            }
            for pos in positions
        ]
