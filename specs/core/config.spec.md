### Module: `quantchain.core.config`

#### Overview
The configuration system provides centralized management of QuantChain application settings, supporting loading from environment variables, JSON/YAML files, and default values with deep merging capabilities.

#### Classes

##### Class: `QuantChainConfig`

###### Constructor: `__init__(config_file: Optional[str] = None)`
- **Description:** Initialize configuration from environment variables and optional config file.
- **Parameters:**
  - `config_file`: Path to JSON or YAML configuration file (optional).
- **Raises:** `FileNotFoundError` if specified config file does not exist.

###### Method: `get(key: str, default: Any = None) -> Any`
- **Description:** Retrieve configuration value by dot-separated key path.
- **Parameters:**
  - `key`: Dot-separated configuration key (e.g., "llm.provider").
  - `default`: Default value to return if key not found.
- **Returns:** Configuration value or default.
- **Raises:** None (returns default on missing key).

###### Method: `get_api_key(provider: str) -> Optional[str]`
- **Description:** Retrieve API key for a specific data provider.
- **Parameters:**
  - `provider`: Provider name ("alpaca", "alpha_vantage").
- **Returns:** API key string or None if not found.
- **Raises:** None.

###### Method: `to_dict() -> Dict[str, Any]`
- **Description:** Return complete configuration as dictionary.
- **Returns:** Deep copy of configuration dictionary.
- **Raises:** None.

#### Functions

##### Function: `get_config(config_file: Optional[str] = None) -> QuantChainConfig`
- **Description:** Get singleton configuration instance.
- **Parameters:**
  - `config_file`: Path to config file (used only on first call).
- **Returns:** Global QuantChainConfig instance.
- **Raises:** `FileNotFoundError` if config file specified and not found.

##### Function: `reload_config(config_file: Optional[str] = None) -> QuantChainConfig`
- **Description:** Reload global configuration instance.
- **Parameters:**
  - `config_file`: Path to config file.
- **Returns:** New QuantChainConfig instance.
- **Raises:** `FileNotFoundError` if config file not found.

#### Configuration Structure
```yaml
llm:
  provider: "ollama"  # or "vllm"
  model: "llama2:7b"
  temperature: 0.7
  max_tokens: 1000

data:
  default_provider: "alpaca"
  cache_enabled: true
  cache_dir: "./data/cache"

trading:
  default_broker: "alpaca"
  paper_trading: true
  max_position_size: 0.1

backtesting:
  default_engine: "backtesting.py"
  initial_balance: 10000
  commission: 0.001

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "./logs/quantchain.log"
```

#### Environment Variables
- `QUANTCHAIN_LLM_PROVIDER`: Override LLM provider
- `QUANTCHAIN_LLM_MODEL`: Override LLM model
- `QUANTCHAIN_DATA_PROVIDER`: Override data provider
- `QUANTCHAIN_PAPER_TRADING`: Override paper trading (true/false)
- `ALPACA_API_KEY`: Alpaca API key
- `ALPACA_API_SECRET`: Alpaca API secret
- `ALPHA_VANTAGE_API_KEY`: Alpha Vantage API key

#### Error Handling
- File operations may raise `FileNotFoundError` for missing config files
- JSON/YAML parsing may raise `json.JSONDecodeError` or `yaml.YAMLError`
- Invalid key access returns default value (no exceptions)

#### Dependencies
- `os` for environment variables
- `pathlib.Path` for file operations
- `json` for JSON parsing
- `yaml` for YAML parsing
- `typing` for type hints
