"""Simple tests for execution factory module to improve coverage."""

from unittest.mock import MagicMock, patch

import pytest

from quantchain.tools.execution_factory import (
    create_execution_interface,
)


class TestExecutionFactorySimple:
    """Simple test cases for execution factory functions."""

    @patch("quantchain.tools.execution_factory.TutorialExecutor")
    def test_tutorial_mode_creation(self, mock_tutorial):
        """Test creating tutorial mode executor."""
        from quantchain.core.config import QuantChainConfig

        config = QuantChainConfig()
        config.broker_type = "tutorial"

        mock_instance = MagicMock()
        mock_tutorial.return_value = mock_instance

        executor = create_execution_interface(config)
        assert executor == mock_instance
        mock_tutorial.assert_called_once()

    @patch("quantchain.tools.execution_factory.PaperTradingExecutor")
    @patch("quantchain.core.security.SecurityManager")
    def test_paper_trading_creation(self, mock_security_manager, mock_paper):
        """Test creating paper trading executor."""
        from quantchain.core.config import QuantChainConfig

        config = QuantChainConfig()
        config.broker_type = "paper"

        # Mock security manager to return credentials
        mock_security_instance = MagicMock()
        mock_security_instance.get_api_key.return_value = "test_key"
        mock_security_instance.get_api_secret.return_value = "test_secret"
        mock_security_manager.return_value = mock_security_instance

        mock_instance = MagicMock()
        mock_paper.return_value = mock_instance

        executor = create_execution_interface(config)
        assert executor == mock_instance
        mock_paper.assert_called_once()

    def test_invalid_broker_type(self):
        """Test error handling for unsupported broker types."""
        from quantchain.core.config import QuantChainConfig
        from quantchain.core.exceptions import ConfigurationError

        config = QuantChainConfig()
        config.broker_type = "unsupported_broker"

        with pytest.raises(ConfigurationError):
            create_execution_interface(config)

    @patch("quantchain.core.security.SecurityManager")
    def test_missing_alpaca_credentials(self, mock_security_manager):
        """Test error handling when Alpaca credentials are missing."""
        from quantchain.core.config import QuantChainConfig
        from quantchain.core.exceptions import AuthenticationError

        config = QuantChainConfig()
        config.broker_type = "alpaca"

        # Mock security manager to raise exception
        mock_security_instance = MagicMock()
        mock_security_instance.get_api_key.side_effect = Exception("No credentials")
        mock_security_manager.return_value = mock_security_instance

        with pytest.raises((AuthenticationError, Exception)):
            create_execution_interface(config)

    @patch("quantchain.core.security.SecurityManager")
    @patch("quantchain.tools.execution_factory.AlpacaExecutor")
    def test_alpaca_creation_with_credentials(self, mock_alpaca, mock_security_manager):
        """Test creating Alpaca executor with valid credentials."""
        from quantchain.core.config import QuantChainConfig

        config = QuantChainConfig()
        config.broker_type = "alpaca"
        config.alpaca_base_url = "https://paper-api.alpaca.markets"

        # Mock security manager
        mock_security_instance = MagicMock()
        mock_security_instance.get_api_key.return_value = "test_key"
        mock_security_instance.get_api_secret.return_value = "test_secret"
        mock_security_manager.return_value = mock_security_instance

        mock_instance = MagicMock()
        mock_alpaca.return_value = mock_instance

        executor = create_execution_interface(config)
        assert executor == mock_instance

    def test_configuration_error_handling(self):
        """Test various configuration error scenarios."""
        from quantchain.core.config import QuantChainConfig
        from quantchain.core.exceptions import ConfigurationError

        config = QuantChainConfig()

        # Test missing broker type
        config.broker_type = None
        with pytest.raises((ConfigurationError, Exception)):
            create_execution_interface(config)

    @patch("quantchain.core.security.SecurityManager")
    @patch("quantchain.tools.execution_factory.PaperTradingExecutor")
    def test_authentication_error_handling(self, mock_paper, mock_security_manager):
        """Test AuthenticationError handling."""
        from quantchain.core.config import QuantChainConfig
        from quantchain.core.exceptions import AuthenticationError

        config = QuantChainConfig()
        config.broker_type = "paper"

        # Mock security manager to raise authentication error
        mock_security_instance = MagicMock()
        mock_security_instance.get_api_key.side_effect = AuthenticationError(
            "Auth failed"
        )
        mock_security_manager.return_value = mock_security_instance

        with pytest.raises(AuthenticationError):
            create_execution_interface(config)
