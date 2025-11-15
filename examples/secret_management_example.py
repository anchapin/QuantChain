"""
Example of using QuantChain's production-grade secret management system.

This example demonstrates how to use different secret managers and
how to migrate from development (.env) to production secret management.
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from quantchain.core.security import (
    APISecurityManager,
    create_secret_manager,
    list_secret_managers,
)

# Example 1: Using default secret manager (from environment)
print("=== Example 1: Default Secret Manager ===")
try:
    manager = APISecurityManager()

    # Try to get credentials (will fail if not set)
    try:
        api_key = manager.get_api_key("alpaca")
        api_secret = manager.get_api_secret("alpaca")
        print("✓ Retrieved Alpaca credentials")
    except Exception as e:
        print(f"✗ Failed to retrieve Alpaca credentials: {e}")

    try:
        api_key = manager.get_api_key("openai")
        print("✓ Retrieved OpenAI key")
    except Exception as e:
        print(f"✗ Failed to retrieve OpenAI key: {e}")

except Exception as e:
    print(f"✗ Failed to initialize manager: {e}")

# Example 2: List available secret managers
print("\n=== Example 2: Available Secret Managers ===")
try:
    managers = list_secret_managers()
    print(f"Available secret managers: {managers}")
except Exception as e:
    print(f"✗ Failed to list managers: {e}")

# Example 3: Create a specific secret manager
print("\n=== Example 3: Creating Custom Manager ===")
try:
    # Create an environment-based manager
    env_manager = create_secret_manager("env")
    print("✓ Created environment manager")

    # Create a file-based manager
    file_manager = create_secret_manager("file", file_path=".secrets.json")
    print("✓ Created file manager")

    # Try to create a vault manager (will fail without proper setup)
    try:
        vault_manager = create_secret_manager(
            "vault", url="http://localhost:8200", token="test"
        )
        print("✓ Created vault manager")
    except Exception:
        print("! Vault manager requires proper configuration")

except Exception as e:
    print(f"✗ Failed to create custom manager: {e}")

# Example 4: Service status check
print("\n=== Example 4: Service Status ===")
try:
    manager = APISecurityManager()
    services = ["alpaca", "openai", "anthropic", "polygon", "ibkr"]

    for service in services:
        try:
            valid = manager.validate_service_credentials(service)
            has_key = manager.get_api_key(service) is not None
            has_secret = manager.get_api_secret(service) is not None
        except Exception:
            valid = False
            has_key = False
            has_secret = False

        status_line = (
            f"{service:15} | Valid: {valid} | Has Key: {has_key} "
            f"| Has Secret: {has_secret}"
        )
        print(status_line)

except Exception as e:
    print(f"✗ Failed to check service status: {e}")

# Example 5: Production configuration guide
print("\n=== Example 5: Production Setup Guide ===")
print(
    """
For production deployment, configure your environment:

1. HashiCorp Vault:
   export QUANTCHAIN_SECRET_BACKEND=vault
   export VAULT_ADDR=https://your-vault.com
   export VAULT_TOKEN=your-token

2. AWS Secrets Manager:
   export QUANTCHAIN_SECRET_BACKEND=aws
   export AWS_REGION=us-east-1
   export AWS_ACCESS_KEY_ID=your-key
   export AWS_SECRET_ACCESS_KEY=your-secret

3. Google Cloud Secret Manager:
   export QUANTCHAIN_SECRET_BACKEND=gcp
   export GCP_PROJECT=your-project
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

4. Store secrets in your secret manager:
   - quantchain/alpaca: {"key": "your-key", "secret": "your-secret"}
   - quantchain/openai: {"key": "your-openai-key"}
   - quantchain/anthropic: {"key": "your-anthropic-key"}
"""
)

# Example 6: Migration from .env to production
print("\n=== Example 6: Migration Guide ===")
print(
    """
To migrate from .env files to production secret management:

1. Install required packages:
   pip install hvac boto3 google-cloud-secret-manager

2. Set up your production secret manager (see Example 5)

3. Add secrets to your secret manager using their CLI/tools:
    vault kv put secret/data/services/alpaca key="your-key" secret="your-secret"
    aws secretsmanager create-secret --name quantchain/alpaca \
        --secret-string '{"key":"your-key","secret":"your-secret"}'

4. Update your deployment configuration to use production backend

5. Remove .env files from production systems

6. Test with this script to ensure everything works
"""
)

print("\n=== Secret Management Example Complete ===")
