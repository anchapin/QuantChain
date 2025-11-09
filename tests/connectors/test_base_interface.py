"""Tests for data feed interface."""

import pytest

from quantchain.connectors.base_interface import DataFeedInterface


@pytest.mark.unit
class TestDataFeedInterface:

    def test_data_feed_interface_is_abstract(self) -> None:
        """Test that DataFeedInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DataFeedInterface("key", "secret")

    def test_data_feed_interface_abstract_methods(self) -> None:
        """Test that all abstract methods are defined."""
        # Check that the abstract methods exist
        abstract_methods = [
            "get_historical_data",
            "get_real_time_data",
            "get_quote",
            "get_available_symbols",
            "get_symbol_info",
            "is_market_open",
        ]

        for method in abstract_methods:
            assert hasattr(DataFeedInterface, method)

            # Check that they are abstract
            method_obj = getattr(DataFeedInterface, method)
            assert hasattr(method_obj, "__isabstractmethod__")
            assert method_obj.__isabstractmethod__

    def test_data_feed_interface_init_signature(self) -> None:
        """Test that __init__ has the expected signature."""
        import inspect

        sig = inspect.signature(DataFeedInterface.__init__)
        params = list(sig.parameters.keys())

        assert "self" in params
        assert "api_key" in params
        assert "api_secret" in params
        assert "kwargs" in params

    def test_data_feed_interface_method_signatures(self) -> None:
        """Test that abstract methods have expected signatures."""
        import inspect

        # Test get_historical_data signature
        sig = inspect.signature(DataFeedInterface.get_historical_data)
        params = sig.parameters

        assert "self" in params
        assert "symbol" in params
        assert "timeframe" in params
        assert "start_date" in params
        assert "end_date" in params
        assert "limit" in params

        # Test get_real_time_data signature
        sig = inspect.signature(DataFeedInterface.get_real_time_data)
        params = sig.parameters

        assert "self" in params
        assert "symbol" in params

        # Test get_quote signature
        sig = inspect.signature(DataFeedInterface.get_quote)
        params = sig.parameters

        assert "self" in params
        assert "symbol" in params

        # Test get_available_symbols signature
        sig = inspect.signature(DataFeedInterface.get_available_symbols)
        params = sig.parameters

        assert "self" in params
        assert "market" in params

        # Test get_symbol_info signature
        sig = inspect.signature(DataFeedInterface.get_symbol_info)
        params = sig.parameters

        assert "self" in params
        assert "symbol" in params

        # Test is_market_open signature
        sig = inspect.signature(DataFeedInterface.is_market_open)
        params = sig.parameters

        assert "self" in params
        assert "market" in params
