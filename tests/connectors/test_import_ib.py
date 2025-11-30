import pytest


def test_import():
    try:
        import ib_async

        print("ib_async imported successfully")
        # Reference the module to avoid unused import warning
        assert hasattr(ib_async, "__version__") or ib_async.__name__ == "ib_async"
    except ImportError as e:
        pytest.fail(f"Failed to import ib_async: {e}")
