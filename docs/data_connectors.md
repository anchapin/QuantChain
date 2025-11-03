# Data Connectors

This document provides detailed information about the data connectors available in QuantChain.

## Overview

QuantChain data connectors implement the `DataFeedInterface` which provides a standardized way to access market data from various sources. All connectors support common operations like retrieving historical data, real-time quotes, and market information.

## Available Connectors

### Alpaca Data Connector

The Alpaca connector provides access to US equity markets and cryptocurrency markets through Alpaca's API.

#### Supported Markets
- **US Equities**: NYSE, NASDAQ stocks (paper and live trading)
- **Cryptocurrencies**: Major crypto pairs via Alpaca Crypto

#### Features
- Historical price data with multiple timeframes
- Real-time quotes and market data
- Market status information
- Symbol and asset information
- Paper trading support

#### Timeframes Supported
- `1Min` - 1 minute
- `5Min` - 5 minutes  
- `15Min` - 15 minutes
- `1H` - 1 hour
- `4H` - 4 hours
- `1D` - 1 day
- `1W` - 1 week
- `1M` - 1 month

#### Authentication
Requires Alpaca API credentials:
- `api_key`: Your Alpaca API key
- `api_secret`: Your Alpaca API secret

#### Usage Example

```python
from quantchain.connectors import AlpacaDataConnector
from datetime import datetime, timezone

# Initialize connector
connector = AlpacaDataConnector(
    api_key="your_api_key",
    api_secret="your_api_secret",
    use_paper=True  # Use paper trading for testing
)

# Get historical stock data
start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
end_date = datetime(2024, 1, 2, tzinfo=timezone.utc)
data = connector.get_historical_data("AAPL", "1D", start_date, end_date)

# Get real-time crypto data
crypto_data = connector.get_real_time_data("BTC/USD")

# Get current quote
quote = connector.get_quote("AAPL")

# Check if market is open
is_open = connector.is_market_open("equity")

# Get available symbols
symbols = connector.get_available_symbols("equity")
```

#### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | str | Required | Alpaca API key |
| `api_secret` | str | Required | Alpaca API secret |
| `use_paper` | bool | True | Use paper trading environment |
| `crypto_feed` | str | "iex" | Data feed for crypto markets |

### Dexscreener Data Connector

The Dexscreener connector provides access to decentralized exchange (DEX) data across multiple blockchains.

#### Supported Markets
- **DEX Pairs**: Uniswap, PancakeSwap, SushiSwap, and other major DEXs
- **Blockchains**: Ethereum, BSC, Polygon, Avalanche, Arbitrum, and more

#### Features
- Real-time token prices and liquidity data
- Trending pairs discovery
- Pair search functionality
- Volume and market cap information
- DEX-specific information (liquidity pools, etc.)

#### Limitations
- Only provides current/snapshot data (no historical data)
- Rate limited by Dexscreener's public API
- Data availability depends on DEX liquidity

#### Authentication
No authentication required - uses Dexscreener's public API.

#### Usage Example

```python
from quantchain.connectors import DexscreenerDataConnector

# Initialize connector (no API key needed)
connector = DexscreenerDataConnector()

# Get real-time data for a specific pair
# Format: BASE/QUOTE:PAIR_ADDRESS or just the pair address
data = connector.get_real_time_data("WETH/USDC:0x1234567890abcdef")

# Get current quote
quote = connector.get_quote("WETH/USDC:0x1234567890abcdef")

# Get trending pairs
trending = connector.get_trending_pairs(limit=10)

# Search for pairs containing a token
results = connector.search_pairs("WETH")

# Get symbol information
info = connector.get_symbol_info("WETH/USDC:0x1234567890abcdef")
```

#### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | str | None | Optional API key (not required) |
| `timeout` | int | 30 | Request timeout in seconds |
| `max_retries` | int | 3 | Maximum number of retry attempts |

## Standardized Interface

All connectors implement the `DataFeedInterface` with the following methods:

### Core Methods

#### `get_historical_data(symbol, timeframe, start_date, end_date=None, limit=None)`
Retrieves historical price data for a symbol.

**Parameters:**
- `symbol` (str): Trading symbol (e.g., 'AAPL', 'BTC/USD')
- `timeframe` (str): Timeframe ('1Min', '1H', '1D', etc.)
- `start_date` (datetime): Start date for data retrieval
- `end_date` (datetime, optional): End date (defaults to now)
- `limit` (int, optional): Maximum number of records

**Returns:** `pandas.DataFrame` with columns:
- `timestamp`: Datetime index
- `open`: Opening price
- `high`: Highest price
- `low`: Lowest price  
- `close`: Closing price
- `volume`: Trading volume

#### `get_real_time_data(symbol)`
Retrieves current market data for a symbol.

**Parameters:**
- `symbol` (str): Trading symbol

**Returns:** `dict` with current market data:
- `timestamp`: Current timestamp
- `price`: Current price
- `bid`: Best bid price
- `ask`: Best ask price
- `volume`: Recent volume

#### `get_quote(symbol)`
Retrieves detailed quote information for a symbol.

**Parameters:**
- `symbol` (str): Trading symbol

**Returns:** `dict` with quote data:
- `symbol`: Trading symbol
- `timestamp`: Quote timestamp
- `bid_price`: Best bid price
- `ask_price`: Best ask price
- `bid_size`: Bid size
- `ask_size`: Ask size
- `last_price`: Last traded price
- `last_size`: Last traded size

#### `get_available_symbols(market=None)`
Retrieves list of available trading symbols.

**Parameters:**
- `market` (str, optional): Filter by market type ('equity', 'crypto')

**Returns:** `list` of available symbols

#### `get_symbol_info(symbol)`
Retrieves detailed information about a symbol.

**Parameters:**
- `symbol` (str): Trading symbol

**Returns:** `dict` with symbol information:
- `symbol`: Trading symbol
- `name`: Full name/description
- `market`: Market type
- `currency`: Base currency
- `min_order_size`: Minimum order size
- `max_order_size`: Maximum order size
- `price_precision`: Price decimal precision
- `size_precision`: Size decimal precision

#### `is_market_open(market=None)`
Checks if the market is currently open for trading.

**Parameters:**
- `market` (str, optional): Specific market to check

**Returns:** `bool` indicating if market is open

## Error Handling

Connectors use standardized exceptions from `quantchain.core.exceptions`:

- `DataSourceError`: General data source errors
- `AuthenticationError`: Authentication/authorization failures
- `SymbolNotFoundError`: Symbol not found or invalid
- `RateLimitError`: API rate limit exceeded
- `NetworkError`: Network connectivity issues

## Best Practices

1. **Error Handling**: Always wrap connector calls in try-catch blocks
2. **Rate Limiting**: Implement proper delays between API calls
3. **Data Validation**: Validate returned data before using
4. **Connection Management**: Use context managers where applicable
5. **Paper Trading**: Test with paper trading environments before live trading

## Testing

All connectors include comprehensive tests with mocked API responses. Run tests with:

```bash
pytest tests/connectors/ -v --cov=quantchain.connectors
```

## Adding New Connectors

To add a new data connector:

1. Implement the `DataFeedInterface` in a new class
2. Add comprehensive tests following the TDD approach
3. Create documentation following this format
4. Update the module exports in `quantchain/connectors/__init__.py`

Example:

```python
from .base_interface import DataFeedInterface
from quantchain.core.exceptions import DataSourceError

class MyConnector(DataFeedInterface):
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        # Initialize your connector
    
    def get_historical_data(self, symbol, timeframe, start_date, end_date=None, limit=None):
        # Implement historical data retrieval
        pass
    
    # Implement other required methods...
```
