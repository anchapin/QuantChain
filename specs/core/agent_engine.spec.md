### Core Agent Engine Specification

#### Overview
The Core Agent Engine provides a model-agnostic agent framework using LangGraph for stateful agent reasoning, memory, and reflection. It supports multiple LLM providers (OpenAI, Anthropic, Ollama, vLLM) and includes RAG capabilities for market data caching with reflective performance analysis.

#### Architecture Components

1. **Agent Framework (LangGraph-based)**
   - Stateful reasoning loops
   - Memory management
   - Tool integration
   - Reflection mechanisms

2. **LLM Provider Abstraction**
   - OpenAI GPT models
   - Anthropic Claude models
   - Local Ollama models
   - vLLM served models

3. **RAG System**
   - Vector store for market data
   - Retrieval-augmented generation
   - Caching for performance

4. **Reflection System**
   - Performance analysis
   - Decision quality metrics
   - Learning from past actions

#### Interfaces

##### Agent Class
```python
class QuantChainAgent:
    def __init__(self, config: QuantChainConfig, tools: List[Tool], llm_provider: LLMProvider)
    def run(self, input_data: Dict[str, Any]) -> AgentResponse
    def reflect(self) -> ReflectionReport
```

##### LLM Provider Interface
```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str
    @abstractmethod
    def get_model_name(self) -> str
```

##### RAG System
```python
class MarketDataRAG:
    def __init__(self, vector_store: VectorStore)
    def store_market_data(self, data: MarketData)
    def retrieve_relevant_data(self, query: str) -> List[MarketData]
    def generate_augmented_prompt(self, base_prompt: str, query: str) -> str
```

##### Reflection System
```python
class ReflectionEngine:
    def analyze_performance(self, actions: List[AgentAction]) -> PerformanceMetrics
    def generate_insights(self, metrics: PerformanceMetrics) -> List[str]
    def update_strategy(self, insights: List[str])
```

#### Data Structures

##### AgentAction
```python
@dataclass
class AgentAction:
    timestamp: datetime
    action_type: str
    parameters: Dict[str, Any]
    result: Any
    confidence_score: float
```

##### MarketData
```python
@dataclass
class MarketData:
    symbol: str
    timestamp: datetime
    data_type: str  # 'price', 'news', 'technical'
    content: Dict[str, Any]
    embedding: Optional[List[float]] = None
```

##### PerformanceMetrics
```python
@dataclass
class PerformanceMetrics:
    total_actions: int
    successful_actions: int
    average_confidence: float
    win_rate: float
    profit_loss: float
    risk_adjusted_return: float
```

#### Error Handling
- `LLMProviderError`: For LLM provider failures
- `RAGError`: For retrieval/storage failures
- `ReflectionError`: For analysis failures
- `AgentStateError`: For invalid agent states

#### Configuration Requirements
The engine uses the existing `QuantChainConfig` system with additional keys:
- `agent.max_iterations`: Maximum reasoning steps
- `agent.reflection_interval`: How often to perform reflection
- `rag.vector_store_type`: Type of vector store ('chromadb', 'faiss')
- `rag.embedding_model`: Model for generating embeddings
