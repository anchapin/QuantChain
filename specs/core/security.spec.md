### Module: Security Module

#### Overview
The Security module provides secure API key management and credential handling for QuantChain. It implements best practices for storing, retrieving, and managing sensitive financial API credentials.

#### Requirements
- **Secure Storage**: Never hardcode API keys in source code
- **Environment Variables**: Default to .env files and environment variables
- **Production Ready**: Support for Vault or cloud secret managers in production
- **Validation**: Validate API key formats and permissions
- **Encryption**: Optional encryption of stored credentials

#### Interface: `APISecurityManager`

**Signature:**
```python
class APISecurityManager:
    def __init__(self, env_file: str = ".env") -> None:
        """Initialize security manager with optional env file path."""

    def set_api_key(self, service: str, key: str, secret: Optional[str] = None) -> None:
        """Securely store API key for a service."""

    def get_api_key(self, service: str) -> str:
        """Retrieve API key for a service."""

    def get_api_secret(self, service: str) -> Optional[str]:
        """Retrieve API secret for a service."""

    def validate_credentials(self, service: str) -> bool:
        """Validate that stored credentials are properly formatted."""

    def list_services(self) -> List[str]:
        """List all configured services."""

    def remove_service(self, service: str) -> None:
        """Remove stored credentials for a service."""
```

**Parameters:**
- `service`: Service identifier (e.g., "alpaca", "polygon", "anthropic")
- `key`: API key string
- `secret`: Optional API secret string
- `env_file`: Path to .env file (default: ".env")

**Returns:**
- `set_api_key`: None
- `get_api_key`: API key string or raises `CredentialNotFoundError`
- `get_api_secret`: API secret string or None
- `validate_credentials`: True if valid, False if invalid
- `list_services`: List of configured service names
- `remove_service`: None

**Raises:**
- `CredentialNotFoundError`: When requested credentials don't exist
- `InvalidCredentialFormatError`: When credentials don't match expected format
- `SecurityConfigurationError`: When security setup is invalid

#### Supported Services
- alpaca: Trading and market data
- polygon: Market data
- alpha_vantage: Market data
- anthropic: LLM provider
- openai: LLM provider

#### Environment Variables Format
```
ALPACA_API_KEY=your_key_here
ALPACA_API_SECRET=your_secret_here
POLYGON_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

#### Production Deployment
For production environments, the module should support:
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault
- GCP Secret Manager

Configuration via environment variable:
```
QUANTCHAIN_SECRET_BACKEND=vault
QUANTCHAIN_VAULT_URL=https://vault.example.com
QUANTCHAIN_VAULT_TOKEN=your_token
```
