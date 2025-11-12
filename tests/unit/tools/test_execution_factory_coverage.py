"""Additional tests for execution factory to improve coverage."""

from typing import Any
from unittest.mock import Mock

import pytest

from quantchain.core.config import QuantChainConfig
from quantchain.core.exceptions import AuthenticationError


class TestExecutionFactoryCoverage:
    """Additional test cases for execution factory coverage."""

    @pytest.fixture
    def mock_config(self) -> Mock:
        """Create a mock QuantChainConfig."""
        return Mock(spec=QuantChainConfig)

    def test_create_alpaca_missing_paper_credentials(self, mock_config: Mock) -> None:
        """Test error when Alpaca credentials missing for paper trading."""
        import os

        # Clear environment variables to simulate missing API credentials
        for env_var in ["ALPACA_API_KEY", "ALPACA_API_SECRET"]:
            if env_var in os.environ:
                del os.environ[env_var]

        def mock_get(key: str, default: Any = None) -> Any:
            mock_responses = {
                "trading.default_broker": "alpaca",
                "trading.paper_trading": True,
            }
            return mock_responses.get(key, default)

        mock_config.get.side_effect = mock_get

        # Mock APISecurityManager to simulate missing credentials
        from quantchain.core.security import APISecurityManager, CredentialNotFoundError

        original_get_api_key = APISecurityManager.get_api_key
        original_get_api_secret = APISecurityManager.get_api_secret

        def mock_get_api_key(self, service):
            if service == "alpaca":
                raise CredentialNotFoundError(
                    f"No API key found for service: {service}"
                )
            return original_get_api_key(self, service)

        def mock_get_api_secret(self, service):
            if service == "alpaca":
                raise CredentialNotFoundError(
                    f"No API secret found for service: {service}"
                )
            return original_get_api_secret(self, service)

        APISecurityManager.get_api_key = mock_get_api_key
        APISecurityManager.get_api_secret = mock_get_api_secret

        try:
            from quantchain.tools.execution_factory import create_execution_interface

            with pytest.raises(AuthenticationError) as exc_info:
                create_execution_interface(mock_config)
            
            assert "Alpaca API credentials required for paper trading" in str(exc_info.value)
        finally:
            # Restore original methods
            APISecurityManager.get_api_key = original_get_api_key
            APISecurityManager.get_api_secret = original_get_api_secret
