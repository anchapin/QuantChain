# Secret Management in QuantChain

## Overview

QuantChain provides a production-grade secret management system that securely handles API keys and other sensitive credentials. The system supports multiple secret backends and provides a unified interface for accessing credentials across different environments.

## Architecture

The secret management system consists of:

1. **Abstract Secret Manager Interface** (`SecretManager`) - Base interface for all implementations
2. **Secret Manager Implementations**:
   - `VaultSecretManager` - HashiCorp Vault
   - `AWSSecretsManager` - AWS Secrets Manager
   - `GCPSecretManager` - Google Cloud Secret Manager
   - `EnvSecretManager` - Environment variables (development only)
3. **Factory Pattern** - For creating the appropriate secret manager
4. **Legacy Compatibility Layer** - Maintains backward compatibility with existing code

## Configuration

### Environment Variables

- `QUANTCHAIN_SECRET_BACKEND` - Secret backend to use (`vault`, `aws`, `gcp`, or `env`)
- `QUANTCHAIN_DEV_MODE` - Set to enable development mode warnings

### Backend-Specific Configuration

#### HashiCorp Vault
```bash
export QUANTCHAIN_SECRET_BACKEND=vault
export VAULT_ADDR=https://vault.example.com
export VAULT_TOKEN=your-vault-token
```

#### AWS Secrets Manager
```bash
export QUANTCHAIN_SECRET_BACKEND=aws
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
```

#### Google Cloud Secret Manager
```bash
export QUANTCHAIN_SECRET_BACKEND=gcp
export GCP_PROJECT=your-project-id
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

#### Environment Variables (Development Only)
```bash
export QUANTCHAIN_SECRET_BACKEND=env
export ALPACA_API_KEY=your-alpaca-key
export ALPACA_API_SECRET=your-alpaca-secret
```

## Usage

### Basic Usage

```python
from quantchain.core.security import APISecurityManager

# Create security manager (automatically uses configured backend)
security_manager = APISecurityManager()

# Get API key for a service
api_key = security_manager.get_api_key("alpaca")
api_secret = security_manager.get_api_secret("alpaca")
```

### Custom Backend Configuration

```python
from quantchain.core.security import APISecurityManager
from quantchain.core.secret_managers import VaultSecretManager

# Use Vault with custom configuration
security_manager = APISecurityManager(
    backend="vault",
    url="https://vault.example.com",
    token="your-token",
    namespace="quantchain"
)
```

### Direct Secret Manager Usage

```python
from quantchain.core.secret_managers import create_secret_manager

# Create AWS Secrets Manager
aws_manager = create_secret_manager(
    backend="aws",
    region_name="us-west-2"
)

# Get secrets
credentials = aws_manager.get_service_credentials("alpaca")
```

## Secret Structure

### Recommended Secret Names

QuantChain expects secrets to be organized as follows:

#### HashiCorp Vault
```
secret/data/services/alpaca
{
  "key": "your-alpaca-key",
  "secret": "your-alpaca-secret"
}
```

#### AWS Secrets Manager
```
quantchain/alpaca
{
  "key": "your-alpaca-key",
  "secret": "your-alpaca-secret"
}
```

#### Google Cloud Secret Manager
```
quantchain/alpaca
{
  "key": "your-alpaca-key",
  "secret": "your-alpaca-secret"
}
```

## Production Deployment

### Security Best Practices

1. **Never use `.env` files in production** - Use a production-grade secret manager
2. **Encrypt secrets at rest** - All supported secret managers provide encryption
3. **Use least-privilege access** - Grant only necessary permissions
4. **Rotate secrets regularly** - Implement secret rotation policies
5. **Monitor access** - Enable audit logging for secret access

### Migration from .env Files

1. **Set up your secret manager** (Vault, AWS, or GCP)
2. **Migrate secrets** from your `.env` file to the secret manager
3. **Update configuration** to use the appropriate backend
4. **Remove `.env` files** from production systems

## Supported Services

QuantChain includes validation patterns for common services:

- **alpaca** - Alpaca trading API
- **polygon** - Polygon.io market data
- **alpha_vantage** - Alpha Vantage market data
- **anthropic** - Anthropic Claude API
- **openai** - OpenAI API
- **ib_async** - Interactive Brokers API

## Error Handling

The system provides specific exceptions:

- `CredentialNotFoundError` - Secret not found
- `InvalidCredentialFormatError` - Invalid credential format
- `SecurityConfigurationError` - Configuration issues

## Development Mode

For local development, you can use environment variables:

```python
# This will show a warning about development-only use
security_manager = APISecurityManager(backend="env")
```

To suppress the warning:

```bash
export QUANTCHAIN_DEV_MODE=1
```

## Testing

For testing, you can use mock implementations:

```python
from unittest.mock import Mock
from quantchain.core.secret_managers import SecretManager

class MockSecretManager(SecretManager):
    def get_secret(self, key):
        return f"mock-{key}"
    
    def get_service_credentials(self, service):
        return {"key": f"mock-{service}-key", "secret": f"mock-{service}-secret"}
    
    def validate_service(self, service):
        return True

# Register and use the mock
from quantchain.core.secret_managers import register_secret_manager
register_secret_manager("mock", MockSecretManager)

security_manager = APISecurityManager(backend="mock")
```

## Migration Guide

### From Old API to New API

**Old:**
```python
manager = APISecurityManager()
manager.set_api_key("alpaca", "key", "secret")
```

**New (production):**
```python
# Store in your secret manager system (e.g., Vault, AWS, GCP)
# Then retrieve:
manager = APISecurityManager()
key = manager.get_api_key("alpaca")
secret = manager.get_api_secret("alpaca")
```

**New (development):**
```python
# Still works with warnings
manager = APISecurityManager(backend="env")
manager.set_api_key("alpaca", "key", "secret")  # Shows deprecation warning
```

## Troubleshooting

### Common Issues

1. **"No API key found" error**
   - Check your secret manager configuration
   - Verify the secret exists in the correct path
   - Ensure proper permissions

2. **"Unsupported secret backend" error**
   - Check the backend name spelling
   - Verify required packages are installed

3. **Connection errors**
   - Verify network connectivity to secret manager
   - Check authentication credentials
   - Ensure firewall rules allow access

### Debug Logging

Enable debug logging to troubleshoot:

```python
import logging
logging.getLogger("quantchain.core.secret_managers").setLevel(logging.DEBUG)
```
