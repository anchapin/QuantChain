"""Additional tests for config module to improve coverage."""

import os
import pytest

from quantchain.core.config import QuantChainConfig


class TestConfigCoverage:
    """Additional test cases for config coverage."""

    def test_ib_environment_variables(self) -> None:
        """Test loading IB configuration from environment variables."""
        # Set environment variables
        os.environ["QUANTCHAIN_IB_HOST"] = "192.168.1.100"
        os.environ["QUANTCHAIN_IB_PORT"] = "4001"
        os.environ["QUANTCHAIN_IB_CLIENT_ID"] = "999"
        os.environ["QUANTCHAIN_IB_TIMEOUT"] = "30"
        os.environ["QUANTCHAIN_IB_ACCOUNT"] = "DU999999"

        # Create config - should load from environment
        config = QuantChainConfig()

        # Check that values were loaded
        assert config.get("trading.ib.host") == "192.168.1.100"
        assert config.get("trading.ib.port") == 4001
        assert config.get("trading.ib.client_id") == 999
        assert config.get("trading.ib.timeout") == 30
        assert config.get("trading.ib.account") == "DU999999"

        # Clean up
        del os.environ["QUANTCHAIN_IB_HOST"]
        del os.environ["QUANTCHAIN_IB_PORT"]
        del os.environ["QUANTCHAIN_IB_CLIENT_ID"]
        del os.environ["QUANTCHAIN_IB_TIMEOUT"]
        del os.environ["QUANTCHAIN_IB_ACCOUNT"]
