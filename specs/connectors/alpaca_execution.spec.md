### Class: `AlpacaExecutionConnector`

**Description:** Alpaca-specific implementation of the trading execution interface supporting both equity and crypto markets with paper trading capabilities.

**Signature:** `AlpacaExecutionConnector(api_key: str, api_secret: str, **kwargs)`

**Parameters:**
- `api_key`: Alpaca API key
- `api_secret`: Alpaca API secret  
- `**kwargs`: Additional configuration
  - `use_paper`: bool - Whether to use paper trading (default: True)
  - `base_url`: Optional[str] - Custom API base URL
  - `data_feed`: str - Data feed source ('iex', 'sip', etc.)

**Methods:**

### Core Trading Operations

#### `place_order(order: OrderRequest) -> OrderResult`
**Alpaca-specific behavior:**
- Maps OrderSide to Alpaca `OrderSide` enum
- Maps OrderType to Alpaca `OrderType` enum  
- Maps TimeInForce to Alpaca `TimeInForce` enum
- Handles crypto vs equity symbol formatting
- Supports fractional shares for equities when available
- Validates order size against symbol requirements

**Crypto-specific handling:**
- Normalizes crypto symbols (e.g., 'BTC-USD' -> 'BTC/USD')
- Uses crypto-specific order endpoints
- Handles crypto precision requirements

**Paper trading behavior:**
- Uses paper trading environment when `use_paper=True`
- Simulates real market conditions with paper money
- All order types supported in paper trading

#### `cancel_order(order_id: str) -> OrderResult`
**Alpaca-specific behavior:**
- Uses Alpaca's cancel_order endpoint
- Handles crypto vs equity order cancellation
- Returns updated order status with cancellation timestamp

#### `get_order(order_id: str) -> OrderResult`
**Alpaca-specific behavior:**
- Uses Alpaca's get_order endpoint
- Converts Alpaca order status to standard OrderStatus enum
- Handles both filled and cancelled orders
- Returns detailed fill information

### Account Information

#### `get_account() -> AccountInfo`
**Alpaca-specific behavior:**
- Maps Alpaca account fields to AccountInfo format
- Handles both equity and crypto account balances
- Calculates portfolio value including both asset classes
- Handles margin information for margin accounts

#### `get_positions() -> List[Position]`
**Alpaca-specific behavior:**
- Retrieves both equity and crypto positions
- Calculates unrealized P&L using current market data
- Handles fractional share positions
- Normalizes position sizes (long = positive, short = negative)

### Market Information

#### `is_market_open(symbol: Optional[str] = None) -> bool`
**Alpaca-specific behavior:**
- For equities: Uses Alpaca market clock API
- For crypto: Always returns True (crypto markets 24/7)
- For specific symbols: Returns market status based on asset class

#### `get_order_history(...) -> List[OrderResult]`
**Alpaca-specific behavior:**
- Uses Alpaca's get_orders endpoint with filtering
- Handles crypto vs equity order history
- Supports pagination for large order histories
- Converts Alpaca order statuses to standard format

### Symbol-specific Operations

#### `_normalize_symbol(symbol: str) -> str`
- Converts crypto symbols to Alpaca format
- Handles both 'BTC/USD' and 'BTC-USD' formats
- Validates symbol format for Alpaca requirements

#### `_get_asset_class(symbol: str) -> str`
- Determines if symbol is crypto or equity
- Uses symbol format to identify asset class
- Supports custom symbol mappings

### Configuration

#### `_configure_client()`
- Initializes Alpaca TradingClient with appropriate settings
- Configures paper trading vs live trading endpoints
- Sets up proper API authentication
- Handles custom base URLs if provided

### Error Handling

**Alpaca-specific error mappings:**
- `APIError` -> `ExecutionError`
- `RequestError` -> `ValidationError`  
- `OrderNotFoundError` -> `OrderNotFoundError`
- `InsufficientFundsError` -> `InsufficientFundsError`
- Network errors -> `ExecutionError`

### Rate Limiting

- Implements proper rate limiting for Alpaca API
- Handles both free and paid tier rate limits
- Implements exponential backoff for retries
- Provides rate limit status information

### Example Usage

```python
# Initialize Alpaca execution connector
executor = AlpacaExecutionConnector(
    api_key="your-api-key",
    api_secret="your-api-secret",
    use_paper=True  # Paper trading mode
)

# Place a market order for equities
order = OrderRequest(
    symbol="AAPL",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=10
)
result = executor.place_order(order)

# Place a limit order for crypto
crypto_order = OrderRequest(
    symbol="BTC/USD",
    side=OrderSide.BUY,
    order_type=OrderType.LIMIT,
    quantity=0.001,
    price=45000.0
)
crypto_result = executor.place_order(crypto_order)

# Get account information
account = executor.get_account()
print(f"Portfolio value: ${account.portfolio_value}")

# Get current positions
positions = executor.get_positions()
for pos in positions:
    print(f"{pos.symbol}: {pos.quantity} shares, P&L: {pos.unrealized_pnl}")
```

### Dependencies

- `alpaca-py>=0.43.0` for Alpaca API integration
- `pandas>=1.21.0` for data handling
- Standard QuantChain core components

### Testing Requirements

- Mock Alpaca API responses for unit tests
- Test both equity and crypto order flows
- Test paper trading vs live trading configurations  
- Test error handling and edge cases
- Test rate limiting behavior
- Integration tests with Alpaca paper trading API
