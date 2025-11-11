"""
Example of using QuantChain's production-grade secret management system.

This example demonstrates how to use different secret managers and
how to migrate from development (.env) to production secret management.
"""

import os
from quantchain.core.security import APISecurityManager
from quantchain.core.secret_managers import (
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
        print(
            f"Alpaca credentials found (key: {api_key[:8] if api_key else 'None'}...)"
        )
    except Exception as e:
        print(f"No Alpaca credentials: {e}")

except Exception as e:
    print(f"Error initializing security manager: {e}")

# Example 2: Explicitly using environment variables
print("\n=== Example 2: Environment Variables ===")
manager = APISecurityManager(backend="env")
print("Using environment variables for secrets")
# Check if credentials are available
if manager.validate_service("alpaca"):
    key = manager.get_api_key("alpaca")
    print(f"Alpaca key found: {key[:8] if key else 'None'}...")
else:
    print("No Alpaca credentials in environment")

# Example 3: Using Vault (production)
print("\n=== Example 3: HashiCorp Vault ===")
try:
    # This will show how to configure Vault, but will fail without actual Vault
    vault_manager = create_secret_manager(
        backend="vault",
        url="https://vault.example.com",
        token="your-vault-token",
        namespace="quantchain",
    )
    print("Vault secret manager configured successfully")
except Exception as e:
    print(f"Vault not available: {e}")

# Example 4: Using AWS Secrets Manager (production)
print("\n=== Example 4: AWS Secrets Manager ===")
try:
    aws_manager = create_secret_manager(
        backend="aws", region_name="us-east-1", profile_name="quantchain"
    )
    print("AWS Secrets Manager configured successfully")
except Exception as e:
    print(f"AWS Secrets Manager not available: {e}")

# Example 5: Using GCP Secret Manager (production)
print("\n=== Example 5: GCP Secret Manager ===")
try:
    gcp_manager = create_secret_manager(
        backend="gcp",
        project_id="your-project-id",
        credentials_path="/path/to/service-account.json",
    )
    print("GCP Secret Manager configured successfully")
except Exception as e:
    print(f"GCP Secret Manager not available: {e}")

# Example 6: List available backends
print("\n=== Example 6: Available Backends ===")
backends = list_secret_managers()
print(f"Available secret managers: {backends}")

# Example 7: Service validation
print("\n=== Example 7: Service Validation ===")
services = ["alpaca", "polygon", "alpha_vantage", "openai", "anthropic"]
for service in services:
    valid = manager.validate_service(service)
    try:
        has_key = manager.get_api_key(service) is not None
    except:
        has_key = False
    try:
        has_secret = manager.get_api_secret(service) is not None
    except:
        has_secret = False
    print(
        f"{service:15} | Valid: {valid} | Has Key: {has_key} | Has Secret: {has_secret}"
    )

# Example 8: Production configuration guide
print("\n=== Example 8: Production Setup Guide ===")
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

# Example 9: Migration from .env to production
print("\n=== Example 9: Migration Guide ===")
print(
    """
To migrate from .env files to production secret management:

1. Install required packages:
   pip install hvac boto3 google-cloud-secret-manager

2. Set up your production secret manager (see Example 8)

3. Add secrets to your secret manager using their CLI/tools:
   vault kv put secret/data/services/alpaca key="your-key" secret="your-secret"
   
4. Update your deployment configuration to use production backend

5. Remove .env files from production systems

6. Test with this script to ensure everything works
"""
)

print("\n=== Secret Management Example Complete ===")
