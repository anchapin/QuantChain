### Class: `PaperTradingExecutor`

**Description:** A paper trading implementation that simulates real market conditions without using actual money. Useful for testing strategies and agent performance in a risk-free environment.

**Signature:** `PaperTradingExecutor(initial_cash: float, **kwargs)`

**Parameters:**
- `initial_cash`: float - Starting cash balance (default: 100000.0)
- `**kwargs`: Additional configuration
  - `commission_per_trade`: float - Commission per trade (default: 0.0)
  - `commission_per_share`: float - Commission per share/contract (default: 0.0)
  - `slippage_model`: SlippageModel - Model for simulating slippage (default: NoSlippage)
  - `fill_model`: FillModel - Model for order fills (default: ImmediateFill)
  - `market_data_provider`: Optional object - Real-time market data provider
  - `price_source`: str - Source for price data ('mock', 'provider', 'random')

**Slippage Models:**

#### `NoSlippage`
- Orders fill at requested price exactly
- Useful for theoretical strategy testing

#### `FixedSlippage`
- Fixed percentage slippage for market orders
- Configuration: slippage_percent (default: 0.1%)

#### `VolumeSlippage`
- Slippage based on order size vs market volume
- Larger orders experience more slippage

#### `RandomSlippage`
- Random slippage within configurable bounds
- Simulates market uncertainty

**Fill Models:**

#### `ImmediateFill`
- Market orders fill immediately
- Limit orders fill immediately if price allows

#### `PartialFill`
- Orders may fill partially based on market volume
- Simulates realistic fill behavior

#### `TimeBasedFill`
- Orders fill over time based on market conditions
- More realistic simulation of order execution

### Core Trading Operations

#### `place_order(order: OrderRequest) -> OrderResult`
**Paper trading behavior:**
- Simulates order matching based on current market data
- Applies slippage model to adjust fill prices
- Applies commission fees
- Updates account balance and positions
- Handles partial fills based on fill model

**Market Order Processing:**
- Uses current market price (bid/ask midpoint)
- Applies slippage to simulate realistic fill price
- Immediate or time-based execution based on fill model

**Limit Order Processing:**
- Places order in order book at limit price
- Monitors market data for fill opportunities
- Fills when market price crosses limit price
- May expire based on time_in_force

**Stop Order Processing:**
- Monitors market price for trigger condition
- Converts to market order when stop price hit
- Applies slippage and fills accordingly

#### `cancel_order(order_id: str) -> OrderResult`
- Cancels pending orders in the paper trading book
- Cannot cancel already filled orders
- Returns updated order status

#### `get_order(order_id: str) -> OrderResult`
- Retrieves order from paper trading book
- Returns current fill status and details
- Provides execution timestamps

### Account Management

#### `get_account() -> AccountInfo`
- Tracks cash balance including unrealized P&L
- Updates portfolio value based on current prices
- Shows available buying power
- Tracks realized and unrealized P&L

#### `get_positions() -> List[Position]`
- Maintains current positions in paper trading book
- Calculates unrealized P&L using current market data
- Tracks average entry prices
- Shows position P&L and percentages

### Market Data Integration

#### `update_market_data(symbols: List[str]) -> None`
- Updates market prices for specified symbols
- Can integrate with real data providers
- Uses mock data for testing scenarios

#### `set_market_price(symbol: str, price: float) -> None`
- Manually sets market price for a symbol
- Useful for testing specific scenarios
- Triggers order fills if conditions are met

### Performance Tracking

#### `get_performance_metrics() -> PerformanceMetrics`
- Tracks overall portfolio performance
- Calculates returns, Sharpe ratio, max drawdown
- Records trade statistics (win rate, avg profit/loss)
- Provides risk metrics

#### `export_trade_history() -> pd.DataFrame`
- Exports complete trade history
- Includes entry/exit prices, P&L, timestamps
- Useful for post-trade analysis

### Scenario Testing

#### `run_scenario(scenario: MarketScenario) -> ScenarioResult`
- Runs portfolio through historical market scenarios
- Tests strategy performance under different conditions
- Provides backtesting-like capabilities

### Configuration Examples

```python
# Basic paper trading with no fees or slippage
executor = PaperTradingExecutor(initial_cash=100000.0)

# Realistic paper trading with fees and slippage
executor = PaperTradingExecutor(
    initial_cash=100000.0,
    commission_per_trade=1.0,
    commission_per_share=0.005,
    slippage_model=FixedSlippage(slippage_percent=0.1),
    fill_model=PartialFill()
)

# Paper trading with real market data
executor = PaperTradingExecutor(
    initial_cash=100000.0,
    market_data_provider=alpaca_data,
    price_source='provider'
)

# Advanced configuration for crypto trading
executor = PaperTradingExecutor(
    initial_cash=50000.0,
    commission_per_trade=2.5,
    slippage_model=VolumeSlippage(base_slippage=0.05),
    fill_model=TimeBasedFill(fill_delay_seconds=5)
)
```

### Order Book Simulation

**Features:**
- Maintains limit order book for each symbol
- Price-time priority for order matching
- Bid-ask spread simulation
- Market depth modeling

**Order Matching Logic:**
1. Incoming market orders match against resting limit orders
2. Best price orders matched first
3. Partial fills handled for large orders
4. Order book updates after each fill

### Risk Management

#### `set_risk_limits(limits: RiskLimits) -> None`
- Maximum position size per symbol
- Maximum daily loss limits
- Maximum leverage limits
- Position concentration limits

#### `check_risk_limits(order: OrderRequest) -> bool`
- Validates order against risk constraints
- Prevents excessive risk-taking
- Returns True if order complies with limits

### Performance Features

- **Backtesting Mode**: Replay historical data
- **Real-time Mode**: Live market data simulation  
- **Monte Carlo**: Random market scenarios
- **Stress Testing**: Extreme market conditions

### Integration with Brokers

- Can be wrapped around real broker execution
- A/B testing of strategies
- Gradual rollout from paper to live trading
- Shadow trading (mirror live orders in paper)

### Reporting and Analytics

#### `generate_report() -> TradingReport`
- Comprehensive performance report
- Trade-by-trade analysis
- Risk metrics breakdown
- Performance attribution

#### `plot_performance() -> None`
- Equity curve visualization
- Drawdown chart
- Return distribution
- Sector exposure (if applicable)

### Example Usage

```python
# Initialize paper trading executor
executor = PaperTradingExecutor(
    initial_cash=100000.0,
    commission_per_trade=1.0,
    slippage_model=FixedSlippage(slippage_percent=0.1)
)

# Set market prices for testing
executor.set_market_price("AAPL", 150.0)
executor.set_market_price("MSFT", 300.0)

# Place orders
order = OrderRequest(
    symbol="AAPL",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=100
)
result = executor.place_order(order)

# Check account status
account = executor.get_account()
print(f"Current portfolio value: ${account.portfolio_value}")

# Get performance metrics
metrics = executor.get_performance_metrics()
print(f"Total return: {metrics.total_return:.2%}")
print(f"Win rate: {metrics.win_rate:.2%}")
```

### Dependencies

- `pandas>=1.21.0` for data handling
- `numpy>=1.21.0` for calculations
- Standard QuantChain execution interface
- Optional: real market data providers

### Testing Requirements

- Test order fills with various market conditions
- Test slippage and commission calculations
- Test risk limit enforcement
- Performance benchmarking against real trading
- Integration tests with market data providers
