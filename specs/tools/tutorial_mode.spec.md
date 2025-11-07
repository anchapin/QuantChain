# Tutorial Mode Specification

## Overview

The Tutorial Mode is a learning-focused trading simulation system that provides enhanced feedback and educational features to help users understand market dynamics and improve their trading skills. It differs from paper trading in its educational focus - while paper trading simulates realistic market conditions for strategy validation, tutorial mode focuses on learning, feedback loops, and confidence building.

### Key Differentiators

- **Learning Focus**: Provides educational context and explanations for each trading decision
- **Mistake Tracking**: Identifies, categorizes, and analyzes trading mistakes with learning recommendations
- **Market Driver Analysis**: Explains the underlying factors influencing market movements
- **Confidence Metrics**: Tracks user confidence and readiness for live trading
- **Session-Based Learning**: Manages tutorial sessions with clear objectives and progress tracking

## Core Classes

### TutorialExecutor

The main executor for tutorial mode that extends the paper trading functionality with learning-focused features.

```python
class TutorialExecutor(TradingExecutionInterface):
    """Tutorial executor for learning-focused trading simulation."""
    
    def __init__(
        self,
        initial_cash: float = 100000.0,
        config: Optional[QuantChainConfig] = None,
        **kwargs: Any
    ) -> None
```

**Key Methods**:
- `start_tutorial_session(symbols, objectives, duration_seconds)`: Initialize new tutorial session
- `place_order(order)`: Execute order with enhanced feedback and learning analysis
- `analyze_decision(order, result)`: Provide detailed analysis of trade decision
- `get_tutorial_feedback()`: Get comprehensive feedback on current session
- `end_tutorial_session()`: Finalize session with summary and recommendations
- `export_tutorial_report()`: Generate detailed tutorial report

### TutorialSession

Manages a single tutorial session with metadata and progress tracking.

```python
@dataclass
class TutorialSession:
    """Manages a single tutorial session."""
    
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    symbols: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    duration_seconds: int = 3600  # 1 hour default
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Properties**:
- `is_active`: Check if session is currently active
- `elapsed_time`: Get elapsed time in seconds
- `add_objective(objective)`: Add a learning objective
- `to_dict()`: Convert session to dictionary

### MarketDriverAnalysis

Analyzes market drivers for educational feedback and decision context.

```python
class MarketDriverAnalysis:
    """Analyzes market drivers for educational feedback."""
    
    def __init__(self, rag_system=None):
        """Initialize market driver analysis."""
        
    def analyze_market_drivers(self, symbol: str, order: OrderResult) -> List[str]:
        """Analyze market drivers for a trade decision."""
        
    def generate_educational_context(self, symbol: str, drivers: List[str]) -> str:
        """Generate educational context for market drivers."""
```

**Driver Categories**:
- **Price Action**: Current market price and movements
- **Technical Indicators**: RSI, MACD, volume changes
- **Order Type**: Market vs. limit order implications
- **Position Sizing**: Risk management considerations
- **News Sentiment**: Market sentiment from news sources

### MistakeTracker

Tracks and categorizes trading mistakes with learning recommendations.

```python
class MistakeTracker:
    """Tracks and categorizes trading mistakes."""
    
    def analyze_mistake(self, order: OrderResult, market_context: Dict[str, Any]) -> Optional[TradingMistake]:
        """Analyze an order for potential mistakes."""
        
    def get_learning_recommendations(self) -> List[str]:
        """Get learning recommendations based on mistake patterns."""
```

**Mistake Categories**:
- **Timing Mistakes**: Suboptimal entry/exit timing in volatile markets
- **Sizing Mistakes**: Inappropriate position sizes (too large or too small)
- **Risk Management Mistakes**: Insufficient risk controls or excessive exposure
- **Market Misread**: Misinterpretation of market direction or conditions

**Severity Levels**:
- **Minor**: Small learning opportunities with minimal impact
- **Moderate**: Important learning points with notable impact
- **Critical**: Major mistakes requiring immediate attention

### ConfidenceMetrics

Tracks confidence building metrics and readiness assessment for live trading.

```python
class ConfidenceMetrics:
    """Tracks confidence building metrics for tutorial."""
    
    def record_decision(self, decision_quality: float, risk_assessment: str, 
                       consistency_score: float = None) -> None:
        """Record a trading decision with quality metrics."""
        
    def is_ready_for_live_trading(self, threshold: float = 0.75) -> bool:
        """Check if ready for live trading based on confidence threshold."""
```

**Metrics Tracked**:
- **Decision Quality**: Overall quality of trading decisions (0-1 scale)
- **Consistency Score**: Consistency of decision-making over time
- **Risk Management Adherence**: Following proper risk management practices
- **Learning Progress**: Improvement trends and learning curve

## Training Session Lifecycle

### 1. Session Initialization
```python
# Start a new tutorial session
session = tutorial_executor.start_tutorial_session(
    symbols=["AAPL", "MSFT"],
    objectives=["Understand market drivers", "Practice risk management"],
    duration_seconds=3600  # 1 hour
)
```

### 2. Making Trades with Feedback
```python
# Place order with automatic analysis
order = OrderRequest(
    symbol="AAPL",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=100
)
result = tutorial_executor.place_order(order)

# Get detailed analysis
analysis = tutorial_executor.get_decision_history()[-1]
print(f"Decision quality: {analysis.decision_quality}")
print(f"Market drivers: {analysis.market_drivers}")
print(f"Educational context: {analysis.educational_context}")
```

### 3. Tracking Progress
```python
# Get comprehensive feedback
feedback = tutorial_executor.get_tutorial_feedback()
print(f"Confidence score: {feedback.confidence_score}")
print(f"Mistakes: {len(feedback.mistakes)}")
print(f"Recommendations: {feedback.recommendations}")

# Check readiness for live trading
ready = tutorial_executor.is_ready_for_live_trading()
print(f"Ready for live trading: {ready}")
```

### 4. Session Completion
```python
# End session with comprehensive report
report = tutorial_executor.end_tutorial_session()
print(f"Final confidence: {report['final_feedback'].confidence_score}")
print(f"Learning objectives progress: {report['learning_progress']}")
```

## Market Driver Analysis

### Identification Process

1. **Basic Analysis**: Identifies drivers from order parameters
2. **Technical Analysis**: Incorporates technical indicators if available
3. **RAG Integration**: Retrieves historical context from similar market conditions
4. **Educational Synthesis**: Creates educational explanations

### Driver Categories

#### Price Action Drivers
- Current price levels
- Recent price movements
- Market liquidity considerations

#### Technical Drivers
- Oversold/overbought conditions (RSI)
- Trend signals (MACD)
- Volume patterns
- Support/resistance levels

#### Order Type Drivers
- Immediate execution requirements (market orders)
- Price discipline considerations (limit orders)
- Risk management implications (stop orders)

#### Position Sizing Drivers
- Risk exposure levels
- Portfolio allocation considerations
- Market impact assessments

### Educational Context Generation

The system generates educational context by:
1. **Explaining Market Drivers**: Clear descriptions of current market factors
2. **Providing Learning Notes**: General principles and best practices
3. **Suggesting Alternatives**: Different approaches for similar situations
4. **Connecting to Theory**: Underlying market theory and concepts

## Mistake Tracking

### Analysis Process

1. **Pattern Recognition**: Identifies common mistake patterns
2. **Context Analysis**: Considers market conditions and circumstances
3. **Severity Assessment**: Evaluates impact and importance
4. **Learning Generation**: Creates actionable learning points

### Mistake Detection Algorithms

#### Timing Mistakes
- High volatility with immediate market fills
- Entering positions during unfavorable market conditions
- Missing optimal entry/exit windows

#### Sizing Mistakes
- Position sizes > 20% of portfolio (too large)
- Position sizes < 1% of portfolio (too small)
- Inconsistent position sizing strategy

#### Risk Management Mistakes
- Using > 50% of portfolio in single position
- No stop-losses in volatile markets
- Inadequate risk controls for conditions

#### Market Misread Mistakes
- Immediate adverse price movement after execution
- Contradicting multiple technical indicators
- Ignoring significant market events/news

### Learning Recommendations

Generated based on mistake patterns:
- **Timing Focus**: Market timing techniques and patience
- **Sizing Focus**: Position sizing rules and risk management
- **Risk Focus**: Stop-losses and risk controls
- **Analysis Focus**: Market analysis and confirmation signals

## Confidence Metrics

### Scoring System

#### Decision Quality Score (0-1)
- Order type appropriateness
- Position sizing considerations
- Risk management alignment
- Market condition awareness

#### Consistency Score (0-1)
- Standard deviation of decision quality
- Similar decisions in similar conditions
- Strategy adherence over time

#### Risk Management Score (0-1)
- Use of appropriate risk controls
- Position size discipline
- Stop-loss implementation

### Readiness Assessment

Users are considered ready for live trading when:
- **Minimum Experience**: At least 10 trading decisions
- **Confidence Threshold**: Overall confidence ≥ 0.75 (configurable)
- **Consistency Requirement**: Decision consistency ≥ 0.6
- **Risk Management**: Risk management score ≥ 0.7

## Configuration

### Tutorial Mode Settings

```yaml
tutorial:
  enabled: false
  session_duration: 3600  # 1 hour
  learning_objectives:
    - "Understand market drivers"
    - "Practice risk management"
    - "Learn from mistakes"
  feedback_level: detailed  # basic, detailed, comprehensive
  track_mistakes: true
  analyze_market_drivers: true
  confidence_threshold: 0.75
  max_mistakes_per_session: 10
```

### Configuration Parameters

- **enabled**: Enable/disable tutorial mode
- **session_duration**: Default session length in seconds
- **learning_objectives**: Default learning objectives for sessions
- **feedback_level**: Verbosity of feedback (basic, detailed, comprehensive)
- **track_mistakes**: Enable mistake tracking and analysis
- **analyze_market_drivers**: Enable market driver analysis
- **confidence_threshold**: Minimum confidence score for live trading readiness
- **max_mistakes_per_session**: Warning threshold for mistakes per session

### Environment Variables

- `QUANTCHAIN_TUTORIAL_ENABLED`: Enable/disable tutorial mode
- `QUANTCHAIN_TUTORIAL_FEEDBACK_LEVEL`: Set feedback verbosity

## Integration

### With Paper Trading

Training mode wraps the paper trading executor, extending its functionality:
- Inherits all paper trading simulation capabilities
- Adds educational feedback and learning features
- Maintains realistic market simulation

### With RAG System

When RAG is enabled, tutorial mode:
- Retrieves historical market data for context
- Identifies similar market conditions
- Provides educational background from past scenarios

### With Reflection Engine

Tutorial mode integrates with reflection system to:
- Record actions for performance analysis
- Generate insights from trading patterns
- Create improvement recommendations

### With Agent Engine

Tutorial mode can be used with agent trading:
- Agents receive enhanced feedback on decisions
- Learning objectives guide agent behavior
- Confidence metrics track agent performance

## Usage Examples

### Basic Training Session

```python
from quantchain.tools import TutorialExecutor
from quantchain.core.config import get_config

# Create tutorial executor
config = get_config("config.yaml")
tutorial_executor = TutorialExecutor(
    initial_cash=100000.0,
    config=config,
    learning_objectives=[
        "Understand market drivers",
        "Practice risk management"
    ]
)

# Start tutorial session
session = tutorial_executor.start_tutorial_session(
    symbols=["AAPL", "MSFT"],
    duration=3600
)

# Make trades with feedback
order = OrderRequest(
    symbol="AAPL",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=10
)
result = tutorial_executor.place_order(order)

# Get tutorial feedback
feedback = tutorial_executor.get_tutorial_feedback()
print(f"Decision quality: {feedback.decision_quality}")
print(f"Market drivers: {feedback.market_drivers}")

# End session and get report
report = tutorial_executor.end_tutorial_session()
print(f"Confidence score: {report['final_feedback'].confidence_score}")
print(f"Ready for live trading: {report['ready_for_live']}")
```

### Agent Integration

```python
from quantchain.agents import MemecoinVibeTrader
from quantchain.tools import TutorialExecutor

# Create tutorial executor
tutorial_executor = TutorialExecutor(
    initial_cash=100000.0,
    feedback_level="comprehensive"
)

# Create agent with tutorial mode
agent = MemecoinVibeTrader(
    data_provider=mock_data_provider,
    execution_tool=tutorial_executor,
    tutorial_mode=True  # Enable tutorial feedback
)

# Start tutorial session
tutorial_executor.start_tutorial_session(
    symbols=["BTC", "ETH"],
    objectives=["Understand crypto market dynamics"]
)

# Run agent cycle with tutorial feedback
results = agent.run_cycle()
print(f"Tutorial feedback: {results['tutorial_feedback']}")
```

## Best Practices

### For Learning

1. **Set Clear Objectives**: Define specific learning goals for each session
2. **Review Feedback**: Carefully review decision analysis and recommendations
3. **Practice Consistency**: Focus on consistent decision-making over time
4. **Learn from Mistakes**: Use mistake tracking to identify and address patterns
5. **Track Progress**: Monitor confidence metrics and learning trends

### For Progression

1. **Start Basic**: Begin with basic feedback level and simple objectives
2. **Increase Complexity**: Progress to detailed/comprehensive feedback
3. **Multiple Sessions**: Use multiple sessions to build skills over time
4. **Apply Learnings**: Implement recommendations from mistake analysis
5. **Assess Readiness**: Use confidence metrics to determine live trading readiness

### For Integration

1. **Configure Appropriately**: Set feedback level and tracking options to match learning goals
2. **Use with RAG**: Enable RAG for richer market context and educational value
3. **Monitor Performance**: Track confidence metrics and learning progress
4. **Review Reports**: Use comprehensive session reports for assessment
5. **Iterate Approach**: Adjust learning objectives based on progress and needs
