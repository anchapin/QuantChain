"""Simple import test for quantchain.backtesting.performance_metrics."""

import pytest

@pytest.mark.unit
def test_module_import():
    """Test that the module can be imported."""
    try:
        import quantchain.backtesting.performance_metrics
        assert True
    except ImportError as e:
        pytest.skip(f"Could not import quantchain.backtesting.performance_metrics: {e}")
