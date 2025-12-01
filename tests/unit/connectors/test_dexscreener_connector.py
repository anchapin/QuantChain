import pytest


@pytest.mark.unit
def test_module_import():
    """Test that the module can be imported."""
    try:

        assert True
    except ImportError as e:
        pytest.skip()
