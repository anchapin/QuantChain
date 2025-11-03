# Data Feed Interface Specification

## Overview
The `DataFeedInterface` provides a standardized abstraction for accessing financial market data across different data providers (Alpaca, Dexscreener, Alpha Vantage, etc.). This interface ensures consistency and interchangeability between different data sources.

## Interface Definition

### Abstract Base Class: `DataFeedInterface`

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import pandas as pd

class DataFeedInterface(ABC):
    """Abstract base class for all data feed connectors."""

    @abstractmethod
    def __init__(self, api_key: str, api_secret: Optional[str] = None, **kwargs):
        """Initialize the data feed connector.

        Args:
            api_key: API key for authentication
            api_secret: Optional API secret for authentication
            **kwargs: Additional provider-specific configuration
        """
        pass

    @abstractmethod
    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Fetch historical price data for a symbol.

        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'BTC-USD', 'ETH/USDT')
            timeframe: Timeframe string (e.g., '1Min', '5Min', '1H', '1D')
            start_date: Start date for data retrieval
            end_date: End date for data retrieval (defaults to now)
            limit: Maximum number of records to return

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume

        Raises:
            DataSourceError: If data cannot be fetched
            ValueError: If parameters are invalid
        """
        pass

    @abstractmethod
    def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch real-time price data for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dict containing current price data with keys:
            - timestamp: Current timestamp
            - price: Current price
            - bid: Best bid price (if available)
            - ask: Best ask price (if available)
            - volume: Recent volume

        Raises:
            DataSourceError: If data cannot be fetched
        """
        pass

    @abstractmethod
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get current quote for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dict containing quote data with keys:
            - symbol: Trading symbol
            - timestamp: Quote timestamp
            - bid_price: Bid price
            - ask_price: Ask price
            - bid_size: Bid size
            - ask_size: Ask size
            - last_price: Last traded price
            - last_size: Last traded size

        Raises:
            DataSourceError: If quote cannot be fetched
        """
        pass

    @abstractmethod
    def get_available_symbols(self, market: Optional[str] = None) -> List[str]:
        """Get list of available symbols for trading.

        Args:
            market: Optional market filter (e.g., 'equity', 'crypto', 'forex')

        Returns:
            List of available trading symbols

        Raises:
            DataSourceError: If symbols cannot be fetched
        """
        pass

    @abstractmethod
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed information about a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dict containing symbol information with keys:
            - symbol: Trading symbol
            - name: Full name/description
            - market: Market type (equity, crypto, forex, etc.)
            - currency: Base currency
            - min_order_size: Minimum order size
            - max_order_size: Maximum order size
            - price_precision: Number of decimal places for price
            - size_precision: Number of decimal places for size

        Raises:
            DataSourceError: If symbol info cannot be fetched
            ValueError: If symbol is not found
        """
        pass

    @abstractmethod
    def is_market_open(self, market: Optional[str] = None) -> bool:
        """Check if the market is currently open for trading.

        Args:
            market: Optional specific market to check

        Returns:
            True if market is open, False otherwise

        Raises:
            DataSourceError: If market status cannot be determined
        """
        pass
```

## Error Handling

### Custom Exceptions

```python
class DataSourceError(Exception):
    """Raised when data cannot be fetched from the source."""
    pass

class AuthenticationError(DataSourceError):
    """Raised when API authentication fails."""
    pass

class RateLimitError(DataSourceError):
    """Raised when API rate limits are exceeded."""
    pass

class SymbolNotFoundError(ValueError):
    """Raised when a requested symbol is not found."""
    pass
```

## Implementation Guidelines

### Data Format Standardization
- All timestamps should be UTC datetime objects
- Price data should use float64 precision
- Volume data should use int64 for whole numbers
- DataFrames should have consistent column names: `timestamp`, `open`, `high`, `low`, `close`, `volume`

### Timeframe Format
- Use standard timeframe strings: `1Min`, `5Min`, `15Min`, `1H`, `4H`, `1D`, `1W`, `1M`
- Implement timeframe conversion if the provider uses different formats

### Caching Strategy
- Implement market-state-aware caching to minimize API calls
- Cache historical data with appropriate TTL based on timeframe
- Cache symbol lists for reasonable periods (e.g., 1 hour)

### Rate Limiting
- Implement exponential backoff for rate limit errors
- Provide clear error messages for rate limiting
- Consider implementing request batching where supported

## Testing Requirements

### Unit Tests
- Mock external API calls
- Test error handling for all exception types
- Test data format validation
- Test parameter validation

### Integration Tests
- Test with sandbox/demo APIs where available
- Test rate limiting behavior
- Test data consistency across different methods

## Examples

### Usage Example
```python
from quantchain.connectors.alpaca_connector import AlpacaDataConnector

# Initialize connector
connector = AlpacaDataConnector(api_key="your_key", api_secret="your_secret")

# Get historical data
data = connector.get_historical_data(
    symbol="AAPL",
    timeframe="1D",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# Get real-time quote
quote = connector.get_quote("AAPL")
print(f"AAPL current price: ${quote['last_price']}")
```
