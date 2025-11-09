## Summary
This PR implements a new CCXT data connector that provides access to 100+ cryptocurrency exchanges through the ccxt library.

## Changes
- **New connector**: `CCXTDataConnector` in `quantchain/connectors/ccxt_connector.py`
- **Full interface implementation**: Implements all methods from `DataFeedInterface`
- **Exchange support**: Works with any ccxt-supported exchange (default: Binance)
- **Comprehensive tests**: 35 tests with mocked ccxt dependencies
- **Documentation**: Complete specification in `specs/connectors/ccxt_connector.spec.md`
- **Example usage**: Example script in `examples/ccxt_connector_example.py`
- **Dependencies**: Added ccxt>=4.0.0 to requirements.txt
- **Exports**: Updated connector module exports

## Features
- ✅ Multi-exchange support (100+ exchanges via ccxt)
- ✅ Configurable exchange selection
- ✅ Symbol normalization (BTC/USDT, BTC-USDT, BTCUSDT)
- ✅ Timeframe conversion (1Min→1m, 1H→1h, etc.)
- ✅ Market data caching with TTL
- ✅ Comprehensive error handling with proper exception mapping
- ✅ Sandbox mode support
- ✅ Rate limiting and timeout configuration
- ✅ API authentication support

## API Methods
- `get_historical_data()` - Fetch OHLCV data
- `get_real_time_data()` - Get current price data
- `get_quote()` - Get detailed quote
- `get_available_symbols()` - List available symbols
- `get_symbol_info()` - Get symbol metadata
- `is_market_open()` - Check market status (always True for crypto)

## Test Coverage
- 35 unit tests covering all functionality
- Mocked ccxt dependencies (works without installation)
- Error handling validation
- Configuration testing

## Files Added/Modified
- `quantchain/connectors/ccxt_connector.py` (new)
- `tests/connectors/test_ccxt_connector.py` (new)
- `specs/connectors/ccxt_connector.spec.md` (new)
- `examples/ccxt_connector_example.py` (new)
- `quantchain/connectors/__init__.py` (updated)
- `requirements.txt` (updated)

## Usage
```python
from quantchain.connectors.ccxt_connector import CCXTDataConnector

# Initialize with default exchange (Binance)
connector = CCXTDataConnector()

# Or use custom exchange
connector = CCXTDataConnector(exchange='kraken', api_key='...', api_secret='...')

# Fetch historical data
df = connector.get_historical_data('BTC/USDT', '1D', start_date)

# Get real-time price
price_data = connector.get_real_time_data('BTC/USDT')
```
