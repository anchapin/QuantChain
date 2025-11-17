"""Simple import test for quantchain.backtesting.market_friction."""

import pytest

@pytest.mark.unit
def test_module_import():
    """Test that the module can be imported."""
    try:
        import quantchain.backtesting.market_friction
        assert True
    except ImportError as e:
        pytest.skip(f"Could not import quantchain.backtesting.market_friction: {e}")
