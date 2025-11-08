# Smart Contract Auditor Agent Specification

## Overview
The Smart Contract Auditor Agent is a specialized security and financial analysis agent that examines smart contracts for vulnerabilities, risks, and investment opportunities. It combines static code analysis with financial metrics to provide comprehensive assessments of DeFi protocols and token contracts.

## Agent Logic Flow

### 1. Contract Discovery Phase
- **Input**: Contract address or protocol name
- **Process**: 
  - Retrieve contract ABI and source code from blockchain explorers
  - Get contract metadata (creation date, author, verification status)
  - Identify contract type (ERC20, ERC721, DeFi protocol, etc.)
- **Output**: Contract metadata and source code

### 2. Static Analysis Phase
- **Input**: Contract source code, ABI, bytecode
- **Process**: 
  - Scan for common vulnerability patterns
  - Analyze code complexity and gas efficiency
  - Check for implementation of security best practices
  - Identify external dependencies and potential supply chain risks
- **Output**: Security vulnerability report with severity ratings

### 3. Financial Analysis Phase
- **Input**: Contract address, tokenomics data
- **Process**:
  - Analyze token distribution and vesting schedules
  - Evaluate liquidity pools and trading volume
  - Calculate yield farming APYs and sustainability
  - Assess protocol revenue models
- **Output**: Financial metrics and risk assessment

### 4. Investment Opportunity Assessment Phase
- **Input**: Security analysis, financial metrics, market data
- **Process**:
  - Combine security score with financial potential
  - Compare with similar protocols
  - Calculate risk-adjusted returns
  - Generate investment recommendation
- **Output**: Investment recommendation with supporting data

## Component Interfaces

### ContractRetriever
```python
class ContractRetriever:
    def get_contract_source(self, address: str, chain: str) -> ContractSource:
        """
        Retrieve contract source code and metadata
        
        Args:
            address: Contract address
            chain: Blockchain network
            
        Returns:
            ContractSource with source code, ABI, and metadata
        """
        pass
        
    def get_contract_bytecode(self, address: str, chain: str) -> bytes:
        """
        Retrieve contract bytecode
        
        Args:
            address: Contract address
            chain: Blockchain network
            
        Returns:
            Contract bytecode
        """
        pass
```

### VulnerabilityScanner
```python
class VulnerabilityScanner:
    def scan_vulnerabilities(self, contract: ContractSource) -> VulnerabilityReport:
        """
        Scan contract for security vulnerabilities
        
        Args:
            contract: Contract source and metadata
            
        Returns:
            VulnerabilityReport with identified issues
        """
        pass
```

### FinancialAnalyzer
```python
class FinancialAnalyzer:
    def analyze_tokenomics(self, contract_address: str, chain: str) -> TokenomicsAnalysis:
        """
        Analyze token economics and distribution
        
        Args:
            contract_address: Token contract address
            chain: Blockchain network
            
        Returns:
            TokenomicsAnalysis with distribution and metrics
        """
        pass
        
    def analyze_defi_protocol(self, protocol_address: str, chain: str) -> ProtocolAnalysis:
        """
        Analyze DeFi protocol metrics and sustainability
        
        Args:
            protocol_address: Protocol contract address
            chain: Blockchain network
            
        Returns:
            ProtocolAnalysis with TVL, APY, and revenue data
        """
        pass
```

## Data Structures

### ContractSource
```python
@dataclass
class ContractSource:
    address: str
    chain: str
    name: Optional[str]
    source_code: str
    abi: List[Dict[str, Any]]
    bytecode: bytes
    compiler_version: str
    optimization_enabled: bool
    constructor_arguments: str
    contract_type: str  # ERC20, ERC721, Custom, etc.
    verification_status: bool
    creation_date: datetime
    deployer_address: str
```

### Vulnerability
```python
@dataclass
class Vulnerability:
    vulnerability_type: str  # "reentrancy", "overflow", "access_control", etc.
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
    description: str
    location: str  # File and line number
    code_snippet: str
    recommendation: str
    cwe_id: Optional[str]  # Common Weakness Enumeration ID
    cvss_score: Optional[float]  # CVSS severity score
```

### VulnerabilityReport
```python
@dataclass
class VulnerabilityReport:
    contract_address: str
    chain: str
    scan_date: datetime
    vulnerabilities: List[Vulnerability]
    overall_security_score: float  # 0-100
    gas_efficiency_score: float  # 0-100
    code_quality_score: float  # 0-100
    audit_status: str  # "SAFE", "WARNING", "DANGEROUS"
    summary: str
    recommendations: List[str]
```

### TokenomicsAnalysis
```python
@dataclass
class TokenomicsAnalysis:
    token_address: str
    total_supply: float
    circulating_supply: float
    holder_count: int
    top_holders: List[Dict[str, Any]]  # Address and percentage
    vesting_schedule: List[Dict[str, Any]]
    liquidity_pools: List[Dict[str, Any]]
    market_cap: float
    fully_diluted_market_cap: float
    inflation_rate: float
    distribution_score: float  # 0-100, higher = more decentralized
```

### ProtocolAnalysis
```python
@dataclass
class ProtocolAnalysis:
    protocol_address: str
    protocol_name: str
    total_value_locked: float
    annual_revenue: float
    apy_rates: Dict[str, float]  # Different pools/strategies
    risk_factors: List[str]
    sustainability_score: float  # 0-100
    competitor_comparison: Dict[str, Any]
    market_position: str  # "LEADER", "CHALLENGER", "NICHE"
```

### InvestmentRecommendation
```python
@dataclass
class InvestmentRecommendation:
    contract_address: str
    contract_type: str
    recommendation: str  # "STRONG_BUY", "BUY", "HOLD", "AVOID", "STRONG_AVOID"
    confidence_score: float  # 0-100
    security_score: float  # 0-100
    financial_score: float  # 0-100
    risk_level: str  # "VERY_LOW", "LOW", "MEDIUM", "HIGH", "VERY_HIGH"
    potential_return: Optional[float]
    risk_factors: List[str]
    opportunity_factors: List[str]
    investment_horizon: str  # "SHORT", "MEDIUM", "LONG"
    reasoning: str
```

## Agent Configuration

### SmartContractAuditorConfig
```python
@dataclass
class SmartContractAuditorConfig:
    # Analysis settings
    deep_analysis_enabled: bool = True
    gas_analysis_enabled: bool = True
    supply_chain_analysis: bool = True
    
    # Security thresholds
    minimum_security_score: float = 70.0
    critical_vulnerabilities_threshold: int = 0
    high_vulnerabilities_threshold: int = 2
    
    # Financial analysis thresholds
    minimum_liquidity: float = 100000.0  # USD
    maximum_holder_concentration: float = 0.30  # 30% top holders
    minimum_distributed_supply: float = 0.60  # 60% circulating
    
    # Investment criteria
    minimum_confidence_score: float = 75.0
    minimum_combined_score: float = 70.0  # Weighted average of security + financial
    
    # Data sources
    blockchain_explorers: Dict[str, str] = field(default_factory=lambda: {
        "ethereum": "https://api.etherscan.io/api",
        "bsc": "https://api.bscscan.com/api",
        "polygon": "https://api.polygonscan.com/api"
    })
    
    # API keys for blockchain explorers
    api_keys: Dict[str, str] = field(default_factory=dict)
    
    # Caching settings
    cache_analysis_results: bool = True
    cache_ttl_hours: int = 24
```

## Vulnerability Database

### VulnerabilityPattern
```python
@dataclass
class VulnerabilityPattern:
    pattern_id: str
    name: str
    cwe_id: str
    severity: str
    description: str
    code_pattern: str
    detection_regex: str
    recommendation: str
    examples: List[str]
```

## Integration Points

1. **Blockchain Explorers**: Etherscan, BscScan, PolygonScan APIs
2. **DeFi Data Platforms**: DeFiLlama, DEX data aggregators
3. **Market Data**: CoinGecko, CoinMarketCap for price data
4. **LLM Integration**: For complex reasoning and report generation
5. **Trading Execution**: For executing investment recommendations

## Testing Requirements

1. **Unit Tests**:
   - Vulnerability pattern matching
   - Financial metric calculations
   - Investment scoring logic

2. **Integration Tests**:
   - API integration with blockchain explorers
   - End-to-end analysis workflows
   - Data accuracy validation

3. **Security Tests**:
   - Test against known vulnerable contracts
   - Validate false positive/negative rates
   - Performance with large contracts

## Performance Considerations

1. **API Rate Limits**: Efficient usage of blockchain explorer APIs
2. **Parallel Processing**: Concurrent analysis of multiple contracts
3. **Caching**: Store analysis results to avoid repeated work
4. **Large Contract Handling**: Memory management for complex contracts

## Error Handling

1. **API Failures**: Retry mechanisms with exponential backoff
2. **Unverified Contracts**: Clear warnings and limited analysis
3. **Incomplete Data**: Graceful degradation with partial analysis
4. **Timeouts**: Configurable timeouts for external API calls
