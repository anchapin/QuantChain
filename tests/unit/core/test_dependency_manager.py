"""Comprehensive tests for the dependency manager module."""

import sys
import pytest
import importlib
from unittest.mock import patch, MagicMock
from quantchain.core.dependency_manager import (
    DependencyManager,
    get_dependency_manager,
    require_optional,
    get_safe_import,
    has_plotly,
    has_streamlit,
    has_torch,
    has_transformers,
    has_ml,
    has_visualization,
    has_trading_connectors,
    init_dependencies,
    import_plotly,
    import_streamlit,
    import_torch,
    import_transformers,
)


class TestDependencyManager:
    """Test cases for DependencyManager class."""

    def test_initialization(self):
        """Test DependencyManager initialization."""
        manager = DependencyManager()
        assert isinstance(manager._available, dict)
        assert isinstance(manager._modules, dict)
        assert len(manager._available) > 0

    def test_singleton_pattern(self):
        """Test that get_dependency_manager returns singleton instance."""
        manager1 = get_dependency_manager()
        manager2 = get_dependency_manager()
        assert manager1 is manager2

    @patch("builtins.__import__")
    def test_check_dependencies_available(self, mock_import):
        """Test dependency checking when modules are available."""
        mock_import.return_value = MagicMock()

        manager = DependencyManager()
        manager._check_dependencies()

        # Should have checked various dependencies
        assert mock_import.called

    @patch("builtins.__import__")
    def test_check_dependencies_not_available(self, mock_import):
        """Test dependency checking when modules are not available."""
        mock_import.side_effect = ImportError("Module not found")

        manager = DependencyManager()
        manager._check_dependencies()

        # Should have checked dependencies and marked as unavailable
        assert any(not available for available in manager._available.values())

    def test_is_available(self):
        """Test checking if dependency is available."""
        manager = DependencyManager()

        # Test known dependency
        result = manager.is_available("sys")
        assert isinstance(result, bool)

        # Test unknown dependency
        result = manager.is_available("nonexistent_dependency_12345")
        assert result is False

    def test_get_module_available(self):
        """Test getting an available module."""
        manager = DependencyManager()

        # Test getting sys module (should always be available)
        module = manager.get_module("sys")
        assert module is sys

        # Test that module is cached
        module2 = manager.get_module("sys")
        assert module is module2

    def test_get_module_not_available(self):
        """Test getting a non-available module."""
        manager = DependencyManager()

        # Test getting non-existent module
        module = manager.get_module("nonexistent_module_12345")
        assert module is None

    def test_get_module_with_fallback(self):
        """Test getting module with fallback value."""
        manager = DependencyManager()
        fallback = object()

        # Test with non-existent module
        module = manager.get_module("nonexistent_module_12345", fallback)
        assert module is fallback

    def test_require_available(self):
        """Test requiring an available dependency."""
        manager = DependencyManager()

        # This should not raise an exception for sys module
        result = manager.require("sys")
        assert result is True

    def test_require_not_available(self):
        """Test requiring a non-available dependency."""
        manager = DependencyManager()

        with pytest.raises(ImportError):
            manager.require("nonexistent_dependency_12345")

    def test_require_with_custom_message(self):
        """Test requiring dependency with custom error message."""
        manager = DependencyManager()
        custom_message = "Custom error message"

        with pytest.raises(ImportError) as exc_info:
            manager.require("nonexistent_dependency_12345", custom_message)

        assert custom_message in str(exc_info.value)

    def test_get_status(self):
        """Test getting dependency status."""
        manager = DependencyManager()
        status = manager.get_status()

        assert isinstance(status, dict)
        # Should have entries for known dependency categories
        expected_categories = ["plotly", "streamlit", "torch", "transformers"]
        for category in expected_categories:
            assert category in status
            assert isinstance(status[category], bool)

    def test_log_status(self, caplog):
        """Test logging dependency status."""
        manager = DependencyManager()

        with caplog.at_level("INFO"):
            manager.log_status()

        # Should have logged status for each dependency
        assert any(
            "Optional Dependencies Status:" in record.message
            for record in caplog.records
        )


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    @patch("quantchain.core.dependency_manager.get_dependency_manager")
    def test_has_plotly(self, mock_get_manager):
        """Test has_plotly function."""
        mock_manager = MagicMock()
        mock_manager.is_available.return_value = True
        mock_get_manager.return_value = mock_manager

        result = has_plotly()
        assert result is True
        mock_manager.is_available.assert_called_with("plotly")

    @patch("quantchain.core.dependency_manager.get_dependency_manager")
    def test_has_streamlit(self, mock_get_manager):
        """Test has_streamlit function."""
        mock_manager = MagicMock()
        mock_manager.is_available.return_value = False
        mock_get_manager.return_value = mock_manager

        result = has_streamlit()
        assert result is False
        mock_manager.is_available.assert_called_with("streamlit")

    @patch("quantchain.core.dependency_manager.get_dependency_manager")
    def test_has_torch(self, mock_get_manager):
        """Test has_torch function."""
        mock_manager = MagicMock()
        mock_manager.is_available.return_value = True
        mock_get_manager.return_value = mock_manager

        result = has_torch()
        assert result is True
        mock_manager.is_available.assert_called_with("torch")

    @patch("quantchain.core.dependency_manager.get_dependency_manager")
    def test_has_transformers(self, mock_get_manager):
        """Test has_transformers function."""
        mock_manager = MagicMock()
        mock_manager.is_available.return_value = False
        mock_get_manager.return_value = mock_manager

        result = has_transformers()
        assert result is False
        mock_manager.is_available.assert_called_with("transformers")

    @patch("quantchain.core.dependency_manager.has_torch")
    @patch("quantchain.core.dependency_manager.has_transformers")
    def test_has_ml(self, mock_transformers, mock_torch):
        """Test has_ml function."""
        mock_torch.return_value = True
        mock_transformers.return_value = True

        result = has_ml()
        assert result is True

        mock_torch.return_value = False
        result = has_ml()
        assert result is False

    @patch("quantchain.core.dependency_manager.has_plotly")
    @patch("quantchain.core.dependency_manager.has_streamlit")
    def test_has_visualization(self, mock_streamlit, mock_plotly):
        """Test has_visualization function."""
        mock_plotly.return_value = True
        mock_streamlit.return_value = True

        result = has_visualization()
        assert result is True

        mock_plotly.return_value = False
        result = has_visualization()
        assert result is False

    @patch("quantchain.core.dependency_manager.get_dependency_manager")
    def test_has_trading_connectors(self, mock_get_manager):
        """Test has_trading_connectors function."""
        mock_manager = MagicMock()
        mock_manager.is_available.return_value = True
        mock_get_manager.return_value = mock_manager

        result = has_trading_connectors()
        assert result is True
        mock_manager.is_available.assert_called_with("ib_async")


class TestDecorators:
    """Test cases for decorators and utility functions."""

    def test_require_optional_decorator_available(self):
        """Test require_optional decorator when dependency is available."""
        with patch(
            "quantchain.core.dependency_manager.get_dependency_manager"
        ) as mock_get:
            mock_manager = MagicMock()
            mock_manager.is_available.return_value = True
            mock_get.return_value = mock_manager

            @require_optional("sys")
            def test_func():
                return "success"

            result = test_func()
            assert result == "success"

    def test_require_optional_decorator_not_available(self):
        """Test require_optional decorator when dependency is not available."""
        with patch(
            "quantchain.core.dependency_manager.get_dependency_manager"
        ) as mock_get:
            mock_manager = MagicMock()
            mock_manager.is_available.return_value = False
            mock_get.return_value = mock_manager

            @require_optional("nonexistent_dependency")
            def test_func():
                return "success"

            with pytest.raises(ImportError):
                test_func()

    def test_require_optional_decorator_with_fallback(self):
        """Test require_optional decorator with fallback."""
        with patch(
            "quantchain.core.dependency_manager.get_dependency_manager"
        ) as mock_get:
            mock_manager = MagicMock()
            mock_manager.is_available.return_value = False
            mock_get.return_value = mock_manager

            fallback_value = "fallback"

            @require_optional("nonexistent_dependency", fallback=fallback_value)
            def test_func():
                return "success"

            result = test_func()
            assert result == fallback_value

    def test_get_safe_import(self):
        """Test get_safe_import function."""
        with patch(
            "quantchain.core.dependency_manager.get_dependency_manager"
        ) as mock_get:
            mock_manager = MagicMock()
            mock_manager.get_module.return_value = sys
            mock_get.return_value = mock_manager

            result = get_safe_import("sys")
            assert result is sys
            mock_manager.get_module.assert_called_with("sys", None)


class TestImportFunctions:
    """Test cases for import functions."""

    @patch("quantchain.core.dependency_manager.has_plotly")
    def test_import_plotly_available(self, mock_has_plotly):
        """Test import_plotly when plotly is available."""
        mock_has_plotly.return_value = True

        with patch("plotly.graph_objects") as mock_go, patch(
            "plotly.express"
        ) as mock_px, patch("plotly.subplots.make_subplots") as mock_subplots:

            go, px, subplots = import_plotly()
            assert go is not None
            assert px is not None
            assert subplots is not None

    @patch("quantchain.core.dependency_manager.has_plotly")
    def test_import_plotly_not_available(self, mock_has_plotly):
        """Test import_plotly when plotly is not available."""
        mock_has_plotly.return_value = False

        go, px, subplots = import_plotly()
        assert go is None
        assert px is None
        assert subplots is None

    @patch("quantchain.core.dependency_manager.has_streamlit")
    def test_import_streamlit_available(self, mock_has_streamlit):
        """Test import_streamlit when streamlit is available."""
        mock_has_streamlit.return_value = True

        with patch("streamlit") as mock_st, patch(
            "streamlit.components.v1.html"
        ) as mock_html:

            st, html = import_streamlit()
            assert st is not None
            assert html is not None

    @patch("quantchain.core.dependency_manager.has_streamlit")
    def test_import_streamlit_not_available(self, mock_has_streamlit):
        """Test import_streamlit when streamlit is not available."""
        mock_has_streamlit.return_value = False

        st, html = import_streamlit()
        assert st is None
        assert html is None

    @patch("quantchain.core.dependency_manager.has_torch")
    def test_import_torch_available(self, mock_has_torch):
        """Test import_torch when torch is available."""
        mock_has_torch.return_value = True

        with patch("torch") as mock_torch, patch("torch.nn") as mock_nn, patch(
            "torch.optim"
        ) as mock_optim:

            torch_module, nn, optim = import_torch()
            assert torch_module is not None
            assert nn is not None
            assert optim is not None

    @patch("quantchain.core.dependency_manager.has_torch")
    def test_import_torch_not_available(self, mock_has_torch):
        """Test import_torch when torch is not available."""
        mock_has_torch.return_value = False

        torch_module, nn, optim = import_torch()
        assert torch_module is None
        assert nn is None
        assert optim is None

    @patch("quantchain.core.dependency_manager.has_transformers")
    def test_import_transformers_available(self, mock_has_transformers):
        """Test import_transformers when transformers is available."""
        mock_has_transformers.return_value = True

        with patch("transformers") as mock_transformers, patch(
            "transformers.AutoTokenizer"
        ) as mock_tokenizer, patch("transformers.AutoModel") as mock_model:

            transformers_module, tokenizer, model = import_transformers()
            assert transformers_module is not None
            assert tokenizer is not None
            assert model is not None

    @patch("quantchain.core.dependency_manager.has_transformers")
    def test_import_transformers_not_available(self, mock_has_transformers):
        """Test import_transformers when transformers is not available."""
        mock_has_transformers.return_value = False

        transformers_module, tokenizer, model = import_transformers()
        assert transformers_module is None
        assert tokenizer is None
        assert model is None


class TestInitDependencies:
    """Test cases for init_dependencies function."""

    @patch("quantchain.core.dependency_manager.get_dependency_manager")
    def test_init_dependencies(self, mock_get_manager):
        """Test init_dependencies function."""
        mock_manager = MagicMock()
        mock_get_manager.return_value = mock_manager

        result = init_dependencies()

        assert result is mock_manager
        mock_manager.log_status.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_dependency_manager_with_empty_dependencies(self):
        """Test DependencyManager with empty dependencies list."""
        with patch(
            "quantchain.core.dependency_manager.DependencyManager._check_dependencies"
        ):
            manager = DependencyManager()
            manager._available = {}
            manager._modules = {}

            assert manager.get_status() == {}
            assert manager.is_available("anything") is False

    def test_module_caching(self):
        """Test that modules are properly cached."""
        manager = DependencyManager()

        # First import
        module1 = manager.get_module("sys")

        # Second import should return cached version
        module2 = manager.get_module("sys")

        assert module1 is module2
        assert "sys" in manager._modules

    def test_multiple_dependency_managers(self):
        """Test creating multiple DependencyManager instances."""
        manager1 = DependencyManager()
        manager2 = DependencyManager()

        # They should be independent instances
        assert manager1 is not manager2
        assert manager1._available is not manager2._available

    def test_require_decorator_with_exception_in_function(self):
        """Test require_optional decorator when function raises exception."""
        with patch(
            "quantchain.core.dependency_manager.get_dependency_manager"
        ) as mock_get:
            mock_manager = MagicMock()
            mock_manager.is_available.return_value = True
            mock_get.return_value = mock_manager

            @require_optional("sys")
            def test_func():
                raise ValueError("Test exception")

            with pytest.raises(ValueError):
                test_func()
