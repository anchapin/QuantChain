"""Base interface classes for QuantChain connectors."""

from abc import ABC, abstractmethod
from typing import List

from quantchain.tools.execution import (
    AccountInfo,
    OrderRequest,
    OrderResult,
)
from quantchain.tools.execution import Position as QuantChainPosition


class BaseExecutionConnector(ABC):
    """
    Base class for execution connectors.

    This abstract base class defines the interface that all execution connectors
    must implement to be compatible with the QuantChain framework.
    """

    @abstractmethod
    def connect(self) -> None:
        """Connect to the execution service."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the execution service."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to the execution service."""
        pass

    @abstractmethod
    def place_order(self, order: OrderRequest) -> OrderResult:
        """Place an order."""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        pass

    @abstractmethod
    def get_account(self) -> AccountInfo:
        """Get account information."""
        pass

    @abstractmethod
    def get_positions(self) -> List[QuantChainPosition]:
        """Get current positions."""
        pass

    @abstractmethod
    def is_market_open(self) -> bool:
        """Check if the market is open."""
        pass
