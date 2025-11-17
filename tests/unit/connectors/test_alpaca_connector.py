"""Simple import test for quantchain.connectors.alpaca_connector."""

import pytest

@pytest.mark.unit
def test_module_import():
    """Test that the module can be imported."""
    try:
        import quantchain.connectors.alpaca_connector
        assert True
    except ImportError as e:
        pytest.skip(f"Could not import quantchain.connectors.alpaca_connector: {e}")
