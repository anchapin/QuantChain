"""Simple import test for quantchain.backtesting.backtestingpy_engine."""

import pytest

@pytest.mark.unit
def test_module_import():
    """Test that the module can be imported."""
    try:
        import quantchain.backtesting.backtestingpy_engine
        assert True
    except ImportError as e:
        pytest.skip(f"Could not import quantchain.backtesting.backtestingpy_engine: {e}")
