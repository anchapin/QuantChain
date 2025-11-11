"""AWS Secrets Manager secret manager implementation."""

import json
import logging
import os
from typing import Dict, Optional

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError as e:
    raise ImportError(
        "boto3 library is required for AWS Secrets Manager support. Install with: pip install boto3"
    ) from e

from .base import SecretManager

logger = logging.getLogger(__name__)


class AWSSecretsManager(SecretManager):
    """AWS Secrets Manager secret manager."""

    def __init__(
        self,
        region_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        profile_name: Optional[str] = None,
        **kwargs: Dict,
    ) -> None:
        """Initialize AWS Secrets Manager.

        Args:
            region_name: AWS region name (defaults to AWS_REGION env var)
            aws_access_key_id: AWS access key ID (defaults to AWS_ACCESS_KEY_ID env var)
            aws_secret_access_key: AWS secret access key (defaults to AWS_SECRET_ACCESS_KEY env var)
            aws_session_token: AWS session token (defaults to AWS_SESSION_TOKEN env var)
            profile_name: AWS profile name from credentials file
            **kwargs: Additional boto3.client parameters
        """
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = aws_secret_access_key or os.getenv(
            "AWS_SECRET_ACCESS_KEY"
        )
        self.aws_session_token = aws_session_token or os.getenv("AWS_SESSION_TOKEN")
        self.profile_name = profile_name or os.getenv("AWS_PROFILE")

        # Build session kwargs
        session_kwargs = {}
        if self.profile_name:
            session_kwargs["profile_name"] = self.profile_name

        # Create session
        if session_kwargs:
            session = boto3.Session(**session_kwargs)
        else:
            session = boto3.Session()

        # Create client kwargs
        client_kwargs = {"region_name": self.region_name}

        # Add credentials if explicitly provided (not from env)
        if self.aws_access_key_id and self.aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = self.aws_access_key_id
            client_kwargs["aws_secret_access_key"] = self.aws_secret_access_key
            if self.aws_session_token:
                client_kwargs["aws_session_token"] = self.aws_session_token

        # Override with any additional kwargs
        client_kwargs.update(kwargs)

        # Initialize client
        self.client = session.client("secretsmanager", **client_kwargs)

        # Verify connection by listing secrets (will fail if credentials are invalid)
        try:
            self.client.list_secrets(MaxResults=1)
            logger.info(
                f"Connected to AWS Secrets Manager in region {self.region_name}"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to connect to AWS Secrets Manager: {e}") from e

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret by key.

        Args:
            key: The secret key/identifier

        Returns:
            The secret value or None if not found
        """
        try:
            # Try to get the secret by its name/ARN
            response = self.client.get_secret_value(SecretId=key)

            if "SecretString" in response:
                secret_string = response["SecretString"]
                # Try to parse as JSON first
                try:
                    secret_data = json.loads(secret_string)
                    # If it's a simple key-value pair with a single key, return the value
                    if len(secret_data) == 1:
                        return next(iter(secret_data.values()))
                    # Otherwise return the entire JSON string
                    return secret_string
                except json.JSONDecodeError:
                    # Not JSON, return as is
                    return secret_string
            elif "SecretBinary" in response:
                return response["SecretBinary"]

            return None
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.debug(f"Secret {key} not found in AWS Secrets Manager")
                return None
            logger.error(
                f"Failed to retrieve secret {key} from AWS Secrets Manager: {e}"
            )
            return None

    def get_service_credentials(self, service: str) -> Dict[str, str]:
        """Retrieve all credentials for a service.

        Args:
            service: The service name (e.g., 'alpaca', 'ib_async')

        Returns:
            Dictionary containing the service's credentials
        """
        try:
            secret_name = f"quantchain/{service}"
            response = self.client.get_secret_value(SecretId=secret_name)

            if "SecretString" in response:
                secret_string = response["SecretString"]
                try:
                    # Parse as JSON and return as dict
                    return json.loads(secret_string)
                except json.JSONDecodeError:
                    # Not JSON, treat entire string as a single credential
                    return {"value": secret_string}

            return {}
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.debug(
                    f"Credentials for {service} not found in AWS Secrets Manager"
                )
                return {}
            logger.error(
                f"Failed to retrieve credentials for {service} from AWS Secrets Manager: {e}"
            )
            return {}

    def validate_service(self, service: str) -> bool:
        """Validate if credentials exist for a service.

        Args:
            service: The service name

        Returns:
            True if credentials are available, False otherwise
        """
        try:
            secret_name = f"quantchain/{service}"
            # Try to get the secret value to validate it exists and is accessible
            response = self.client.get_secret_value(SecretId=secret_name)
            return response is not None and "SecretString" in response
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return False
            logger.debug(f"Service {service} validation failed: {e}")
            return False
