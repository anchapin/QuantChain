# Interactive Brokers Execution Connector Specification

## Overview

The Interactive Brokers (IB) execution connector provides integration with Interactive Brokers' trading infrastructure using the `ib_async` library. This connector supports multiple asset classes (stocks, forex, futures, options) and both paper and live trading environments.

## Class Definition

### IBExecutionConnector

**Description**: Interactive Brokers execution connector using ib_async library, supporting stocks, forex, futures, and options across global markets

**Signature**: 
```python
IBExecutionConnector(
    host: str = '127.0.0.1',
    port: int = 7497,
    client_id: int = 1,
    timeout: int = 10,
    readonly: bool = False,
    account: Optional[str] = None,
    **kwargs
)
```

**Parameters**:
- `host`: IB Gateway/TWS host (default: '127.0.0.1')
- `port`: Connection port 
  - 7497 for TWS paper trading
  - 7496 for TWS live trading
  - 4002 for Gateway paper trading
  - 4001 for Gateway live trading
- `client_id`: Unique client identifier (1-32, default: 1)
- `timeout`: Connection timeout in seconds (default: 10)
- `readonly`: Read-only mode, no order placement (default: False)
- `account`: Specific account to use for multi-account setups (optional)
- `**kwargs`: Additional configuration parameters

## Core Methods (implementing TradingExecutionInterface)

### place_order(order: OrderRequest) -> OrderResult

Maps standard OrderType to IB order types and places the order.

**Implementation Steps**:
1. Validate order using `validate_order()`
2. Convert symbol to IB Contract using `_create_contract()`
3. Qualify contract using `_qualify_contract()` to resolve details
4. Convert OrderRequest to IB Order using `_convert_order_to_ib()`
5. Call `ib.placeOrder()` and wait for acknowledgment
6. Store trade in `_order_map` for tracking
7. Convert IB Trade to OrderResult and return

**IB-specific behavior**:
- Handles contract qualification for different security types
- Supports fractional shares where available
- Manages order transmission with proper error mapping

### cancel_order(order_id: str) -> OrderResult

Cancels an existing order.

**Implementation Steps**:
1. Find trade in `_order_map` or search `ib.trades()`
2. If not found, raise OrderNotFoundError
3. Call `ib.cancelOrder(trade.order)`
4. Update trade status and return OrderResult

### get_order(order_id: str) -> OrderResult

Retrieves order status and details.

**Implementation Steps**:
1. Search `_order_map` for order_id
2. If not found, search `ib.trades()` and `ib.openOrders()`
3. If still not found, raise OrderNotFoundError
4. Convert IB Trade/Order to OrderResult and return

### get_account() -> AccountInfo

Retrieves account information.

**Implementation Steps**:
1. Call `ib.accountSummary(account=self.account)` to get account values
2. Extract NetLiquidation, AvailableFunds, BuyingPower, TotalCashValue
3. Call `get_positions()` to get position list
4. Return AccountInfo with all fields populated

### get_positions() -> List[Position]

Retrieves current open positions.

**Implementation Steps**:
1. Call `ib.positions(account=self.account)` to get all positions
2. For each IB position, create Position object:
   - Extract symbol from contract, quantity, avgCost
   - Get current price from market data or use avgCost
   - Calculate market_value, unrealized_pnl, unrealized_pnl_percent
3. Return list of Position objects

### get_order_history(...) -> List[OrderResult]

Retrieves historical orders with optional filtering.

**Implementation Steps**:
1. Retrieve trades from `ib.trades()` and `ib.fills()`
2. Apply filters:
   - By symbol if provided
   - By status if provided (map to IB status)
   - By date range (start_date, end_date)
   - By limit if provided
3. Convert each trade to OrderResult
4. Sort by timestamp descending
5. Return filtered list

### is_market_open(symbol: Optional[str] = None) -> bool

Checks if market is open for trading.

**Implementation Steps**:
1. If symbol is forex, return True (24/5 market)
2. If symbol provided, create contract and check contract details for trading hours
3. Otherwise, check general market status
4. Return boolean indicating market status

## Helper Methods

### _create_contract(symbol: str) -> Contract

Creates appropriate IB Contract based on symbol format.

**Symbol Formats**:
- Stocks: 'AAPL', 'MSFT'
- Forex: 'EURUSD', 'GBPJPY'
- Futures: 'ESZ3', 'NQH4'
- Options: 'AAPL 20231215 150 C', 'SPY 20240120 450 P'

**Implementation**:
- Parse symbol to determine security type
- Create appropriate Contract (Stock, Forex, Future, Option)
- Set exchange to 'SMART' for stocks, specific exchanges for others
- Return Contract object

### _qualify_contract(contract: Contract) -> Contract

Qualifies contract with IB to get complete details.

**Implementation**:
- Call `ib.qualifyContracts(contract)` to resolve details
- Handle RequestError for invalid contracts
- Return qualified contract or raise ValidationError

### _convert_order_to_ib(order: OrderRequest) -> Order

Converts standard OrderRequest to IB Order object.

**Mapping**:
- OrderSide: BUY/SELL → 'BUY'/'SELL'
- OrderType: MARKET/LIMIT/STOP/STOP_LIMIT → MarketOrder/LimitOrder/StopOrder/StopLimitOrder
- TimeInForce: DAY/GTC/IOC/FOK → 'DAY'/'GTC'/'IOC'/'FOK'

**Implementation**:
- Set action (BUY/SELL), totalQuantity, orderType
- Set lmtPrice for limit orders, auxPrice for stop orders
- Set tif (time in force) and other parameters
- Return Order object

### _convert_ib_order_to_result(trade: Trade) -> OrderResult

Converts IB Trade object to standard OrderResult.

**Implementation**:
- Extract order details from IB Trade object
- Map IB order status to OrderStatus enum using `_convert_order_status()`
- Calculate filled_quantity from trade.orderStatus.filled
- Calculate avg_fill_price from fills list
- Return OrderResult with all fields populated

### _convert_order_status(status: str) -> OrderStatus

Maps IB order status strings to OrderStatus enum.

**Status Mapping**:
- 'Submitted' → OrderStatus.PENDING
- 'PreSubmitted' → OrderStatus.PENDING
- 'Filled' → OrderStatus.FILLED
- 'PartiallyFilled' → OrderStatus.PARTIALLY_FILLED
- 'Cancelled' → OrderStatus.CANCELLED
- 'Inactive' → OrderStatus.REJECTED
- 'ApiCancelled' → OrderStatus.CANCELLED
- 'PendingSubmit' → OrderStatus.PENDING
- 'PendingCancel' → OrderStatus.PENDING

### _run_async(coro)

Synchronous wrapper for async operations.

**Implementation**:
- Accept coroutine as parameter
- Run coroutine in event loop using `asyncio.run_coroutine_threadsafe` or `loop.run_until_complete`
- Handle exceptions and timeouts
- Return result or raise appropriate exception

### _connect()

Establishes connection to IB Gateway/TWS.

**Implementation**:
- Use `ib.connect()` with host, port, clientId, timeout
- Set `IB.RaiseRequestErrors = True` for exception-based error handling
- Handle connection errors with proper exception mapping

## Error Handling

Maps IB exceptions to QuantChain exceptions:

- `ConnectionRefusedError` → `AuthenticationError` ("Cannot connect to IB Gateway/TWS")
- `asyncio.TimeoutError` → `ExecutionError` ("Connection timeout")
- `RequestError` with code 201 → `OrderNotFoundError`
- `RequestError` with code 321 → `ValidationError` ("Invalid contract")
- `RequestError` with code 10147 → `InsufficientFundsError`
- Other `RequestError` → `ExecutionError`

## Configuration Examples

### Paper Trading with TWS
```python
connector = IBExecutionConnector(
    host='127.0.0.1',
    port=7497,  # TWS paper trading
    client_id=1
)
```

### Live Trading with IB Gateway
```python
connector = IBExecutionConnector(
    host='127.0.0.1',
    port=4001,  # Gateway live trading
    client_id=2,
    account='U1234567'
)
```

## Dependencies

- `ib_async>=1.0.0` for IB API integration
- Standard QuantChain core components

## Testing Requirements

- Mock IB client and all async methods
- Test contract creation for different security types
- Test order placement, cancellation, and status retrieval
- Test account and position retrieval
- Test error handling for all exception types
- Test async-to-sync wrapper functionality
- Test both success and failure paths for all methods

## Implementation Notes

- Use synchronous wrappers for all async IB operations
- Maintain order tracking in `_order_map` for quick lookups
- Handle contract qualification errors gracefully
- Support multiple security types (stocks, forex, futures, options)
- Ensure thread-safety for event loop operations
- Clean up resources in disconnect method
- Follow the standardized interface for execution tools
