### Component: Polygon.io Data Connector

#### Overview
The Polygon.io Data Connector provides a unified interface for accessing Polygon.io's market data APIs for both equities and forex markets. It supports historical aggregates, real-time quotes, and symbol information with built-in caching, error handling, and rate limit management.

#### Requirements
- **Multi-Market Support**: Equities and forex market data
- **Data Types**: Historical aggregates, real-time quotes, latest trades
- **Caching**: Symbol information caching with TTL
- **Error Handling**: Comprehensive exception handling with proper error types
- **Timeframes**: Support for standard timeframes (1Min, 5Min, 15Min, 1H, 4H, 1D, 1W, 1M)
- **Authentication**: Secure API key management integration

#### Interface: `PolygonDataConnector`

**Signature:**
```python
class PolygonDataConnector(DataFeedInterface):
    def __init__(self, api_key: str, api_secret: Optional[str] = None, **kwargs: Any) -> None:
        """Initialize Polygon.io data connector."""

    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """Fetch historical price data."""

    def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch real-time price data."""

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get current quote for a symbol."""

    def get_available_symbols(
        self, market: Optional[str] = None, limit: Optional[int] = None
    ) -> List[str]:
        """Get list of available symbols."""

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed information about a symbol."""

    def is_market_open(self, market: Optional[str] = None) -> bool:
        """Check if the market is currently open."""
```

**Parameters:**
- `api_key`: Polygon.io API key (20-50 character alphanumeric string)
- `api_secret`: Not used for Polygon.io (None)
- `symbol`: Trading symbol (e.g., 'AAPL' for equities, 'C:EURUSD' for forex)
- `timeframe`: Timeframe string ('1Min', '5Min', '1H', '1D', etc.)
- `start_date`: Start date for historical data
- `end_date`: End date for historical data (defaults to now)
- `limit`: Maximum number of records to return
- `market`: Market filter ('equity', 'forex', or None for all)
- `cache_ttl`: Symbol cache TTL in seconds (default: 3600)
- `adjusted`: Whether to use adjusted prices (default: True)
- `limit`: Default limit for pagination (default: 5000)

**Returns:**
- `get_historical_data`: DataFrame with columns [timestamp, open, high, low, close, volume]
- `get_real_time_data`: Dict with price and volume data
- `get_quote`: Dict with bid/ask prices and sizes
- `get_available_symbols`: List of available symbol strings
- `get_symbol_info`: Dict with symbol metadata
- `is_market_open`: Boolean indicating market status

**Raises:**
- `AuthenticationError`: Invalid API credentials
- `SymbolNotFoundError`: Symbol not found
- `DataSourceError`: API or network errors
- `RateLimitError`: Rate limit exceeded
- `ValueError`: Invalid parameters

#### Supported Timeframes
- 1Min → (1, "minute")
- 5Min → (5, "minute")
- 15Min → (15, "minute")
- 1H → (1, "hour")
- 4H → (4, "hour")
- 1D → (1, "day")
- 1W → (1, "week")
- 1M → (1, "month")

#### Data Formats
**Historical Data DataFrame:**
```python
DataFrame({
    'timestamp': datetime64[ns],
    'open': float64,
    'high': float64,
    'low': float64,
    'close': float64,
    'volume': int64
})
```

**Real-time Data:**
```python
{
    'timestamp': datetime,
    'price': float,
    'bid': float,
    'ask': float,
    'volume': int
}
```

**Quote Data:**
```python
{
    'symbol': str,
    'timestamp': datetime,
    'bid_price': float,
    'ask_price': float,
    'bid_size': float,
    'ask_size': float,
    'last_price': float,
    'last_size': float
}
```

#### Symbol Information
```python
{
    'symbol': str,
    'name': str,
    'market': str,  # 'equity' or 'forex'
    'currency': str,  # 'USD' for equities, base currency for forex
    'min_order_size': float,
    'max_order_size': Optional[float],
    'price_precision': int,  # Typically 4 for forex, 2-4 for equities
    'size_precision': int
}
```

#### Symbol Formats
- **Equities**: Standard ticker symbols (e.g., 'AAPL', 'GOOGL')
- **Forex**: Polygon.io format with 'C:' prefix (e.g., 'C:EURUSD')
- **Forex Conversion**: Connector accepts 'EUR/USD' or 'EURUSD' and converts to 'C:EURUSD'

#### Configuration Options
- `cache_ttl`: Symbol cache TTL in seconds (default: 3600)
- `adjusted`: Whether to use adjusted prices (default: True)
- `limit`: Default limit for pagination (default: 5000)

#### Dependencies
- polygon-api-client>=1.0.0
- pandas>=1.5.3
- python-dotenv (for security integration)

#### Usage Example
```python
from quantchain.connectors.polygon_connector import PolygonDataConnector
from quantchain.core.security import APISecurityManager
from datetime import datetime, timedelta

# Get credentials from security manager
security = APISecurityManager()
api_key = security.get_api_key("polygon")

# Initialize connector
connector = PolygonDataConnector(api_key)

# Get historical data for equity
start_date = datetime.now() - timedelta(days=30)
df = connector.get_historical_data("AAPL", "1D", start_date)

# Get historical data for forex
df_forex = connector.get_historical_data("C:EURUSD", "1H", start_date)

# Get real-time quote
quote = connector.get_quote("AAPL")

# Check market status
is_equity_open = connector.is_market_open("equity")
is_forex_open = connector.is_market_open("forex")  # Always True

# Get available symbols
equities = connector.get_available_symbols("equity", limit=100)
forex_pairs = connector.get_available_symbols("forex", limit=50)
```

#### Error Handling
- Network timeouts and retries
- Rate limit detection and handling (429 status codes)
- Invalid symbol detection
- Authentication failure handling
- Data availability checks
- Iterator handling for paginated responses

#### Caching Strategy
- Symbol information cached for configurable TTL (default: 1 hour)
- Automatic cache refresh on expiration
- Thread-safe cache operations
- Separate caching for equities and forex symbols

#### Testing
- Mock Polygon.io API responses using patch decorators
- Test all error conditions including rate limits
- Validate data format compliance
- Test caching behavior
- Test both equity and forex symbol handling
- Integration tests with security module
- Test symbol format normalization (EUR/USD → C:EURUSD)
