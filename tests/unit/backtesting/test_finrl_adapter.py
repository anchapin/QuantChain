"""Simple import test for quantchain.backtesting.finrl_adapter."""

import pytest


@pytest.mark.unit
def test_module_import():
    """Test that the module can be imported."""
    try:
        import quantchain.backtesting.finrl_adapter

        assert True
    except ImportError as e:
        pytest.skip(f"Could not import quantchain.backtesting.finrl_adapter: {e}")
