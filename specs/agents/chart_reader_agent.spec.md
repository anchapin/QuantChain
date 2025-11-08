# Multimodal Chart-Reader Agent Specification

## Overview
The Chart-Reader Agent is a specialized trading agent that analyzes financial charts using multimodal AI capabilities. It combines visual pattern recognition with traditional technical indicators to generate trading signals with confidence scores.

## Agent Logic Flow

### 1. Data Collection Phase
- **Input**: Symbol, timeframes (1m, 5m, 15m, 1h, 4h, 1d)
- **Process**: Fetch OHLCV data via market data connectors
- **Output**: Time series data for chart rendering

### 2. Chart Rendering Phase
- **Input**: OHLCV data
- **Process**: Generate chart images with:
  - Candlestick patterns
  - Volume bars
  - Technical indicators overlay (MA, RSI, MACD, Bollinger Bands)
  - Support/resistance lines
- **Output**: Chart images in format compatible with vision models

### 3. Multimodal Analysis Phase
- **Input**: Chart images, technical indicator data, market context
- **Process**: Use vision-capable LLM to:
  - Identify chart patterns (head & shoulders, triangles, flags, double tops/bottoms)
  - Assess pattern quality and completion probability
  - Correlate visual patterns with technical indicators
  - Evaluate overall market structure
- **Output**: Pattern recognition results with confidence scores

### 4. Signal Generation Phase
- **Input**: Pattern analysis, technical indicators, market context
- **Process**: 
  - Combine visual pattern signals with technical indicators
  - Apply risk assessment based on pattern reliability history
  - Generate actionable trading recommendations
  - Calculate confidence score based on pattern strength and confluence
- **Output**: Trading signals with entry/exit points and risk parameters

## Component Interfaces

### ChartRenderer
```python
class ChartRenderer:
    def render_candlestick_chart(self, data: OHLCVData, indicators: List[TechnicalIndicator], timeframe: str) -> ChartImage:
        """
        Render candlestick chart with technical indicators overlay
        
        Args:
            data: OHLCV data
            indicators: List of technical indicators to overlay
            timeframe: Chart timeframe
            
        Returns:
            ChartImage object with image data and metadata
        """
        pass
```

### PatternRecognizer
```python
class PatternRecognizer:
    def analyze_chart(self, chart_image: ChartImage, context: MarketContext) -> PatternAnalysis:
        """
        Analyze chart for patterns using vision model
        
        Args:
            chart_image: Chart image to analyze
            context: Current market context
            
        Returns:
            PatternAnalysis with identified patterns and confidence scores
        """
        pass
```

### TechnicalIndicatorCalculator
```python
class TechnicalIndicatorCalculator:
    def calculate_indicators(self, data: OHLCVData, indicator_types: List[str]) -> Dict[str, TechnicalIndicator]:
        """
        Calculate technical indicators
        
        Args:
            data: OHLCV data
            indicator_types: List of indicator types to calculate
            
        Returns:
            Dictionary of technical indicators
        """
        pass
```

## Data Structures

### ChartImage
```python
@dataclass
class ChartImage:
    image_data: bytes  # PNG/JPEG image data
    symbol: str
    timeframe: str
    timestamp: datetime
    indicators_applied: List[str]
    metadata: Dict[str, Any]
```

### PatternAnalysis
```python
@dataclass
class Pattern:
    pattern_type: str  # "head_and_shoulders", "triangle", "flag", etc.
    pattern_subtype: str  # "ascending", "descending", etc.
    confidence: float  # 0-100
    completion_percentage: float  # 0-100
    price_target: Optional[float]
    invalidation_level: float
    time_remaining: Optional[timedelta]
    
@dataclass
class PatternAnalysis:
    patterns: List[Pattern]
    overall_sentiment: str  # "bullish", "bearish", "neutral"
    confluence_score: float  # How many indicators agree with patterns
    recommended_action: str  # "BUY", "SELL", "HOLD"
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: List[float]  # Multiple profit targets
    reasoning: str
```

### TechnicalIndicator
```python
@dataclass
class TechnicalIndicator:
    name: str
    values: List[float]
    signal: str  # "OVERBOUGHT", "OVERSOLD", "NEUTRAL"
    divergence: Optional[str]  # "BULLISH", "BEARISH", None
    timestamp: datetime
```

## Agent Configuration

### ChartReaderAgentConfig
```python
@dataclass
class ChartReaderAgentConfig:
    # Timeframes to analyze
    timeframes: List[str] = field(default_factory=lambda: ["15m", "1h", "4h", "1d"])
    
    # Patterns to detect
    patterns_enabled: List[str] = field(default_factory=lambda: [
        "head_and_shoulders", "double_top", "double_bottom",
        "triangle", "flag", "pennant", "wedge", "channel"
    ])
    
    # Technical indicators
    indicators_enabled: List[str] = field(default_factory=lambda: [
        "SMA", "EMA", "RSI", "MACD", "Bollinger_Bands", "Volume"
    ])
    
    # Signal thresholds
    min_pattern_confidence: float = 70.0
    min_confluence_score: float = 60.0
    
    # Risk management
    max_position_size: float = 0.05  # 5% of portfolio
    default_stop_loss_pct: float = 2.0  # 2%
    default_take_profit_ratio: float = 2.0  # 2:1 R:R
    
    # Chart rendering options
    chart_width: int = 800
    chart_height: int = 600
    candle_count: int = 200  # Number of candles to display
    
    # Vision model configuration
    vision_model_provider: str = "openai"  # openai, anthropic, local
    vision_model_name: str = "gpt-4-vision-preview"
```

## Pattern Library

### Historical Performance Tracking
```python
@dataclass
class PatternPerformance:
    pattern_type: str
    total_occurrences: int
    success_rate: float
    average_profit_pct: float
    average_loss_pct: float
    average_holding_period: timedelta
    timeframe: str
    last_updated: datetime
```

## Integration Points

1. **Market Data Connectors**: Use existing connectors for OHLCV data
2. **LLM Integration**: Extend existing LLM provider to support vision models
3. **Trading Execution**: Use existing trading execution interfaces
4. **Risk Management**: Integrate with existing risk management modules

## Testing Requirements

1. **Unit Tests**:
   - Chart rendering accuracy
   - Pattern identification accuracy with test charts
   - Technical indicator calculations

2. **Integration Tests**:
   - End-to-end signal generation
   - Performance with real-time data
   - Memory and performance constraints

3. **Backtesting**:
   - Historical performance on known patterns
   - Comparison with baseline strategies
   - Performance metrics (win rate, profit factor, max drawdown)

## Performance Considerations

1. **Latency**: Chart rendering and vision model processing time
2. **Memory**: Image data storage and processing
3. **API Costs**: Vision model API usage optimization
4. **Caching**: Pattern recognition results caching
5. **Batch Processing**: Multiple symbols/timeframes efficiently

## Error Handling

1. **Chart Rendering Failures**: Fallback to text-based analysis
2. **Vision Model Unavailable**: Graceful degradation to technical-only analysis
3. **Insufficient Data**: Minimum data requirements before analysis
4. **Pattern Ambiguity**: Confidence thresholds for ambiguous cases
