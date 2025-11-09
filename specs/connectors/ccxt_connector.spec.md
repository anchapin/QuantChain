### Component: CCXT Data Connector

#### Overview
The CCXT Data Connector provides a unified interface for accessing cryptocurrency market data from 100+ exchanges via the ccxt library. It supports multiple exchanges with standardized API, configurable settings, and comprehensive error handling.

#### Requirements
- **Multi-Exchange Support**: Access to 100+ cryptocurrency exchanges via ccxt
- **Configurable Exchange**: Select exchange at initialization (default: binance)
- **Data Types**: Historical OHLCV, real-time quotes, market information
- **Timeframe Conversion**: Convert QuantChain timeframes to ccxt format
- **Symbol Normalization**: Handle various symbol formats (BTC-USD, BTCUSD, BTC/USD)
- **Caching**: Market data caching with TTL
- **Error Handling**: Comprehensive exception handling with proper error types
- **Rate Limiting**: Built-in rate limit handling via ccxt
- **Authentication**: Optional API key support for exchanges requiring credentials

#### Interface: `CCXTDataConnector`

**Signature:**
```python
class CCXTDataConnector(DataFeedInterface):
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        exchange: str = "binance",
        **kwargs: Any
    ) -> None:
        """Initialize CCXT data connector with specified exchange."""

    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data."""

    def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch real-time ticker data."""

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
- `api_key`: Optional API key for authenticated exchanges
- `api_secret`: Optional API secret for authenticated exchanges
- `exchange`: Exchange name (default: 'binance')
- `symbol`: Trading symbol (e.g., 'BTC/USDT', 'ETH-USD')
- `timeframe`: Timeframe string ('1Min', '5Min', '1H', '1D', etc.)
- `start_date`: Start date for historical data
- `end_date`: End date for historical data (defaults to now)
- `limit`: Maximum number of records to return
- `market`: Market filter (ignored, always 'crypto' for ccxt)

**Kwargs Parameters:**
- `sandbox`: Use testnet/sandbox mode (default: False)
- `enableRateLimit`: Enable ccxt rate limiting (default: True)
- `cache_ttl`: Market cache time-to-live in seconds (default: 3600)
- `timeout`: Request timeout in seconds (default: 30)

**Returns:**
- `get_historical_data`: DataFrame with columns [timestamp, open, high, low, close, volume]
- `get_real_time_data`: Dict with price and volume data
- `get_quote`: Dict with bid/ask prices and sizes
- `get_available_symbols`: List of available symbol strings
- `get_symbol_info`: Dict with symbol metadata
- `is_market_open`: Boolean indicating market status (always True for crypto)

**Raises:**
- `AuthenticationError`: Invalid API credentials
- `SymbolNotFoundError`: Symbol not found
- `DataSourceError`: API or network errors
- `RateLimitError`: Rate limit exceeded
- `ValueError`: Invalid timeframe or parameters

#### Supported Timeframes
- 1Min → 1m
- 5Min → 5m
- 15Min → 15m
- 1H → 1h
- 4H → 4h
- 1D → 1d
- 1W → 1w

#### Data Formats
**Historical Data DataFrame:**
```python
DataFrame({
    'timestamp': datetime64[ns],
    'open': float64,
    'high': float64,
    'low': float64,
    'close': float64,
    'volume': float64
})
```

**Real-time Data:**
```python
{
    'timestamp': datetime,
    'price': float,
    'bid': float,
    'ask': float,
    'volume': float
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

**Symbol Information:**
```python
{
    'symbol': str,
    'name': str,
    'market': str,  # 'crypto'
    'currency': str,  # quote currency (e.g., 'USDT', 'USD')
    'min_order_size': float,
    'max_order_size': Optional[float],
    'price_precision': int,
    'size_precision': int
}
```

#### Supported Exchanges
Popular supported exchanges include:
- Binance
- Coinbase
- Kraken
- Bybit
- OKX
- And 100+ more via ccxt

#### Configuration Options
- `exchange`: Exchange name (default: 'binance')
- `sandbox`: Use testnet/sandbox mode (default: False)
- `enableRateLimit`: Enable ccxt rate limiting (default: True)
- `cache_ttl`: Market cache time-to-live in seconds (default: 3600)
- `timeout`: Request timeout in seconds (default: 30)

#### Dependencies
- ccxt>=4.0.0
- pandas>=1.3.0
- python-dotenv (for security integration)

#### Usage Example
```python
from quantchain.connectors.ccxt_connector import CCXTDataConnector
from quantchain.core.security import APISecurityManager
from datetime import datetime, timedelta

# Get credentials from security manager (optional)
security = APISecurityManager()
api_key = security.get_api_key("binance")  # Optional
api_secret = security.get_api_secret("binance")  # Optional

# Initialize connector with default exchange (binance)
connector = CCXTDataConnector(api_key, api_secret)

# Initialize with custom exchange
connector = CCXTDataConnector(
    api_key,
    api_secret,
    exchange="coinbase",
    sandbox=True,
    cache_ttl=1800
)

# Get historical data
start_date = datetime.now() - timedelta(days=30)
df = connector.get_historical_data("BTC/USDT", "1D", start_date)

# Get real-time quote
quote = connector.get_quote("ETH/USDT")

# Get available symbols
symbols = connector.get_available_symbols(limit=100)

# Check market status (always True for crypto)
is_open = connector.is_market_open()
```

#### Error Handling
- Maps ccxt exceptions to QuantChain exceptions:
  - ccxt.AuthenticationError → AuthenticationError
  - ccxt.RateLimitExceeded → RateLimitError
  - ccxt.BadSymbol → SymbolNotFoundError
  - ccxt.NetworkError/ExchangeNotAvailable → DataSourceError
- Network timeouts and retries via ccxt
- Rate limit handling via ccxt built-in throttling
- Invalid symbol detection
- Authentication failure handling
- Data availability checks

#### Helper Methods
- `_convert_timeframe()`: Convert QuantChain timeframe to ccxt format
- `_normalize_symbol()`: Convert various symbol formats to ccxt format (BTC/USDT)
- `_refresh_market_cache()`: Refresh market data cache with TTL

#### Caching Strategy
- Market information cached for 1 hour (configurable)
- Automatic cache refresh on expiration
- Thread-safe cache operations
- Cache bypass on manual refresh

#### Testing
- Mock ccxt exchange instances
- Test all error conditions
- Validate data format compliance
- Test caching behavior
- Test symbol normalization
- Test timeframe conversion
- Test multiple exchanges
