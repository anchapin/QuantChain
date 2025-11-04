# Memecoin Vibe Trader Agent Specification

## Overview
The Memecoin Vibe Trader is an autonomous trading agent that identifies and trades promising memecoin opportunities by combining on-chain data analysis with social media sentiment and LLM-based "vibe" assessment.

## Agent Logic Flow

### 1. Scan Phase
- **Input**: Time window for new token detection (default: last hour)
- **Process**: Query DexscreenerDataConnector for newly created token pairs
- **Output**: List of new token pairs with basic metrics (liquidity, volume, age)

### 2. Filter Phase
- **Input**: Raw token list from Scan Phase
- **Process**: For each token, use SocialMediaScraper to gather social metrics:
  - Telegram channel follower count
  - Twitter/X follower count
  - Recent social media activity velocity
  - Community engagement metrics
- **Output**: Filtered list of tokens with social metrics attached

### 3. Analyze Phase (LLM Reasoning)
- **Input**: Filtered token list with social and on-chain metrics
- **Process**: Pass data to LLM for "vibe" assessment ranking:
  - Token name analysis (memetic potential)
  - Social media velocity assessment
  - Tokenomics evaluation (supply, distribution)
  - Risk assessment based on patterns
- **Output**: Ranked list of tokens with vibe scores and trading recommendations

### 4. Execute Phase
- **Input**: Ranked token list with trading signals
- **Process**:
  - Apply risk management filters (position sizing, max allocation)
  - Execute trades via AlpacaExecutionTool for qualifying opportunities
- **Output**: Trade execution confirmations and position updates

## Component Interfaces

### DexscreenerDataConnector
```python
class DexscreenerDataConnector:
    def get_new_token_pairs(self, time_window: str = "1h") -> List[TokenPair]:
        """
        Fetch newly created token pairs from Dexscreener

        Args:
            time_window: Time window to look back (e.g., "1h", "24h")

        Returns:
            List of TokenPair objects with basic metrics
        """
        pass
```

### SocialMediaScraper
```python
class SocialMediaScraper:
    def get_social_metrics(self, token_symbol: str, token_address: str) -> SocialMetrics:
        """
        Scrape social media metrics for a token

        Args:
            token_symbol: Token symbol (e.g., "PEPE")
            token_address: Token contract address

        Returns:
            SocialMetrics object with follower counts, activity, etc.
        """
        pass
```

### AlpacaExecutionTool
```python
class AlpacaExecutionTool:
    def execute_market_order(self, symbol: str, side: str, quantity: float) -> OrderResult:
        """
        Execute a market order via Alpaca

        Args:
            symbol: Trading symbol
            side: "buy" or "sell"
            quantity: float

        Returns:
            OrderResult with execution details
        """
        pass
```

## Data Structures

### TokenPair
```python
@dataclass
class TokenPair:
    address: str
    symbol: str
    name: str
    liquidity: float
    volume_24h: float
    created_at: datetime
    dex: str
```

### SocialMetrics
```python
@dataclass
class SocialMetrics:
    telegram_followers: int
    twitter_followers: int
    recent_posts: int
    engagement_rate: float
    sentiment_score: float
```

### VibeAssessment
```python
@dataclass
class VibeAssessment:
    token: TokenPair
    social_metrics: SocialMetrics
    vibe_score: float  # 0-100 scale
    recommendation: str  # "BUY", "HOLD", "SKIP"
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    reasoning: str
```

## Configuration Parameters

### Agent Configuration
```python
@dataclass
class MemecoinVibeTraderConfig:
    scan_interval: int = 3600  # seconds
    max_positions: int = 5
    max_allocation_per_trade: float = 0.02  # 2% of portfolio
    min_liquidity_threshold: float = 10000  # USD
    min_vibe_score_threshold: float = 70
    risk_tolerance: str = "MEDIUM"
```

## Error Handling

### Expected Errors
- **DexscreenerAPIError**: When Dexscreener API is unavailable
- **SocialMediaScrapingError**: When social media scraping fails
- **LLMInferenceError**: When LLM ranking fails
- **ExecutionError**: When trade execution fails
- **InsufficientFundsError**: When portfolio has insufficient funds

### Error Recovery
- Retry failed API calls with exponential backoff
- Skip tokens that fail social media scraping
- Use fallback ranking logic if LLM fails
- Log all errors with context for debugging

## Testing Requirements

### Unit Tests
- Mock all external dependencies (APIs, LLMs)
- Test each phase in isolation
- Test error handling scenarios

### Integration Tests
- Test end-to-end flow with real components
- Test backtesting integration
- Test concurrent token processing

### Backtesting Tests
- Test against historical memecoin data
- Validate performance metrics
- Test risk management effectiveness

## Performance Requirements

### Latency
- Token scanning: < 30 seconds
- Social media scraping: < 60 seconds per token
- LLM ranking: < 10 seconds per batch
- Trade execution: < 5 seconds

### Scalability
- Handle 100+ new tokens per hour
- Process social metrics for 50+ tokens concurrently
- Maintain < 5 minute total cycle time

## Monitoring and Logging

### Metrics to Track
- Tokens scanned per cycle
- Social media scraping success rate
- LLM inference latency
- Trade execution success rate
- Portfolio performance vs benchmark

### Alerts
- API failures
- High error rates
- Portfolio drawdown thresholds
- Performance degradation
