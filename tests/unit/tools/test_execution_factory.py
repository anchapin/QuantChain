"""Tests for execution interface factory."""

from typing import Any
from unittest.mock import Mock

import pytest

from quantchain.core.config import QuantChainConfig
from quantchain.core.exceptions import AuthenticationError, ConfigurationError


class TestExecutionFactory:
    """Test cases for execution interface factory."""

    @pytest.fixture
    def mock_config(self) -> Mock:
        """Create a mock QuantChainConfig."""
        return Mock(spec=QuantChainConfig)

    def test_create_alpaca_paper_trading(self, mock_config: Mock) -> None:
        """Test creating Alpaca connector in paper trading mode."""
        import os

        # Set up environment variables for API keys
        os.environ["ALPACA_API_KEY"] = "test-key"
        os.environ["ALPACA_API_SECRET"] = "test-secret"

        def mock_get(key: str, default: Any = None) -> Any:
            mock_responses = {
                "trading.default_broker": "alpaca",
                "trading.paper_trading": True,
            }
            return mock_responses.get(key, default)

        mock_config.get.side_effect = mock_get

        from quantchain.tools.execution_factory import create_execution_interface

        executor = create_execution_interface(mock_config)

        assert hasattr(executor, "use_paper")
        assert executor.use_paper is True

    def test_create_alpaca_live_trading(self, mock_config: Mock) -> None:
        """Test creating Alpaca connector in live trading mode."""
        import os

        # Set up environment variables for API keys
        os.environ["ALPACA_API_KEY"] = "test-key"
        os.environ["ALPACA_API_SECRET"] = "test-secret"

        def mock_get(key: str, default: Any = None) -> Any:
            mock_responses = {
                "trading.default_broker": "alpaca",
                "trading.paper_trading": False,
            }
            return mock_responses.get(key, default)

        mock_config.get.side_effect = mock_get

        from quantchain.tools.execution_factory import create_execution_interface

        executor = create_execution_interface(mock_config)

        assert hasattr(executor, "use_paper")
        assert executor.use_paper is False

    def test_create_paper_trading_executor(self, mock_config: Mock) -> None:
        """Test creating standalone paper trading executor."""

        def mock_get(key: str, default: Any = None) -> Any:
            return "paper" if key == "trading.default_broker" else default

        mock_config.get.side_effect = mock_get

        from quantchain.tools.execution_factory import create_execution_interface

        executor = create_execution_interface(mock_config)

        assert hasattr(executor, "initial_cash")
        assert executor.initial_cash == 100000.0

    def test_missing_api_key_for_live_trading(self, mock_config: Mock) -> None:
        """Test error when API key is missing for live trading."""
        import os

        # Clear environment variables to simulate missing API credentials
        for env_var in ["ALPACA_API_KEY", "ALPACA_API_SECRET"]:
            if env_var in os.environ:
                del os.environ[env_var]

        def mock_get(key: str, default: Any = None) -> Any:
            mock_responses = {
                "trading.default_broker": "alpaca",
                "trading.paper_trading": False,
            }
            return mock_responses.get(key, default)

        mock_config.get.side_effect = mock_get

        # Mock the APISecurityManager to simulate missing credentials
        from quantchain.core.security import APISecurityManager, CredentialNotFoundError
        
        original_get_api_key = APISecurityManager.get_api_key
        original_get_api_secret = APISecurityManager.get_api_secret
        
        def mock_get_api_key(self, service):
            if service == "alpaca":
                raise CredentialNotFoundError(f"No API key found for service: {service}")
            return original_get_api_key(self, service)
            
        def mock_get_api_secret(self, service):
            if service == "alpaca":
                raise CredentialNotFoundError(f"No API secret found for service: {service}")
            return original_get_api_secret(self, service)

        APISecurityManager.get_api_key = mock_get_api_key
        APISecurityManager.get_api_secret = mock_get_api_secret

        try:
            from quantchain.tools.execution_factory import create_execution_interface

            with pytest.raises(AuthenticationError):
                create_execution_interface(mock_config)
        finally:
            # Restore original methods
            APISecurityManager.get_api_key = original_get_api_key
            APISecurityManager.get_api_secret = original_get_api_secret

    def test_unsupported_broker(self, mock_config: Mock) -> None:
        """Test error for unsupported broker."""

        def mock_get(key: str, default: Any = None) -> Any:
            if key == "trading.default_broker":
                return "unsupported_broker"
            return default

        mock_config.get.side_effect = mock_get

        from quantchain.tools.execution_factory import create_execution_interface

        with pytest.raises(ConfigurationError):
            create_execution_interface(mock_config)
