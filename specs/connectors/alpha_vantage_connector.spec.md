### Component: Alpha Vantage Data Connector

#### Overview
The Alpha Vantage Data Connector provides a unified interface for accessing Alpha Vantage's market data APIs for both equities and forex markets. It supports historical time series data, real-time quotes, and market information with built-in caching, error handling, and rate limit awareness.

#### Requirements
- **Multi-Market Support**: Equity and forex data
- **Data Types**: Historical bars, real-time quotes, symbol information
- **Caching**: Symbol information caching with TTL
- **Error Handling**: Comprehensive exception handling with proper error types
- **Timeframes**: Support for standard timeframes (1Min, 5Min, 15Min, 30Min, 60Min, 1D, 1W, 1M)
- **Authentication**: API key management (16-character uppercase key)
- **Rate Limiting**: Awareness of Alpha Vantage's free tier limits (5 calls/min, 500/day)

#### Interface: `AlphaVantageDataConnector`

**Signature:**
```python
class AlphaVantageDataConnector(DataFeedInterface):
    def __init__(self, api_key: str, api_secret: Optional[str] = None, **kwargs: Any) -> None:
        """Initialize Alpha Vantage data connector."""

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
- `api_key`: Alpha Vantage API key (16 uppercase alphanumeric characters)
- `api_secret`: Not used for Alpha Vantage (included for interface compatibility)
- `symbol`: Trading symbol (e.g., 'AAPL' for equities, 'EUR/USD' for forex)
- `timeframe`: Timeframe string ('1Min', '5Min', '15Min', '30Min', '60Min', '1D', '1W', '1M')
- `start_date`: Start date for historical data
- `end_date`: End date for historical data (defaults to now)
- `limit`: Maximum number of records to return
- `market`: Market filter ('equity', 'forex', or None for all)

**Returns:**
- `get_historical_data`: DataFrame with columns [timestamp, open, high, low, close, volume]
- `get_real_time_data`: Dict with price and volume data
- `get_quote`: Dict with bid/ask prices and sizes
- `get_available_symbols`: List of available symbol strings
- `get_symbol_info`: Dict with symbol metadata
- `is_market_open`: Boolean indicating market status

**Raises:**
- `AuthenticationError`: Invalid API key
- `SymbolNotFoundError`: Symbol not found
- `DataSourceError`: API or network errors
- `RateLimitError`: API rate limit exceeded
- `ValueError`: Invalid timeframe or parameters

#### Supported Timeframes
- **Intraday**: 1Min, 5Min, 15Min, 30Min, 60Min
- **Daily/Weekly/Monthly**: 1D, 1W, 1M

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
    'currency': str,  # 'USD', 'EUR', etc.
    'region': str,  # 'United States', 'Europe', etc.
    'min_order_size': float,
    'max_order_size': Optional[float],
    'price_precision': int,  # 2 for equities, 4 for forex
    'size_precision': int  # # 0 for equities, 8 for forex
}
```

#### Symbol Format
- **Equities**: Standard ticker symbols (e.g., 'AAPL', 'GOOGL', 'MSFT')
- **Forex**: Currency pair format 'BASE/QUOTE' (e.g., 'EUR/USD', 'GBP/JPY')

#### Configuration Options
- `timeout`: Request timeout in seconds (default: 30)
- `max_retries`: Maximum number of retry attempts (default: 3)
- `cache_ttl`: Cache time-to-live in seconds for symbol data (default: 3600)
- `symbol_limit`: Maximum symbols to return in get_available_symbols (default: 100)

#### Dependencies
- requests>=2.25.0
- pandas>=1.3.0

#### Usage Example
```python
from quantchain.connectors.alpha_vantage_connector import AlphaVantageDataConnector
from datetime import datetime, timedelta

# Initialize connector
connector = AlphaVantageDataConnector(api_key="YOUR_API_KEY")

# Get historical equity data
start_date = datetime.now() - timedelta(days=30)
df = connector.get_historical_data("AAPL", "1D", start_date)

# Get historical forex data
forex_df = connector.get_historical_data("EUR/USD", "1H", start_date)

# Get real-time quote
quote = connector.get_quote("AAPL")

# Get available symbols
equities = connector.get_available_symbols(market="equity")
forex_pairs = connector.get_available_symbols(market="forex")

# Check market status
is_equity_market_open = connector.is_market_open("equity")
is_forex_market_open = connector.is_market_open("forex")  # Always True
```

#### Error Handling
- **Authentication Errors**: Invalid API key format or rejected key
- **Rate Limiting**: Detection of rate limits from API responses
- **Network Errors**: Retry logic with exponential backoff
- **Invalid Symbols**: Proper error messages for unknown symbols
- **Data Parsing**: Graceful handling of malformed API responses

#### Caching Strategy
- Symbol information cached with configurable TTL (default 1 hour)
- Automatic cache refresh on expiration
- Thread-safe cache operations
- Graceful degradation when cache refresh fails

#### Rate Limits
- **Free Tier**: 5 calls per minute, 500 calls per day
- **Premium Tier**: Higher limits available
- **Implementation**: Rate limit detection and appropriate error handling
- **Recommendation**: Premium tier for production use

#### API Endpoints Used
- **Equity Historical**: TIME_SERIES_INTRADAY, TIME_SERIES_DAILY, TIME_SERIES_WEEKLY, TIME_SERIES_MONTHLY
- **Forex Historical**: FX_INTRADAY, FX_DAILY, FX_WEEKLY, FX_MONTHLY
- **Real-time Equity**: GLOBAL_QUOTE
- **Real-time Forex**: CURRENCY_EXCHANGE_RATE
- **Symbol Search**: SYMBOL_SEARCH
- **Market Status**: MARKET_STATUS

#### Testing
- Mock Alpha Vantage API responses
- Test all error conditions
- Validate data format compliance
- Test caching behavior
- Test rate limit handling
- Test all supported timeframes
- Integration tests with different market types
