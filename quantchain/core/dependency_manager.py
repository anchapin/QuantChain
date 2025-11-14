"""
Dependency Manager for QuantChain
Handles optional imports and provides graceful fallbacks.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DependencyManager:
    """Manages optional dependencies with graceful fallbacks."""

    def __init__(self) -> None:
        """Initialize dependency manager."""
        self._available: Dict[str, bool] = {}
        self._modules: Dict[str, Any] = {}
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Check availability of optional dependencies."""
        dependencies: Dict[str, Any] = {
            "plotly": ["plotly", "plotly.graph_objects", "plotly.express"],
            "streamlit": ["streamlit", "streamlit.components.v1"],
            "torch": ["torch", "torch.nn", "torch.optim"],
            "transformers": ["transformers", "transformers.models"],
            "sentence_transformers": ["sentence_transformers"],
            "finrl": ["finrl"],
            "ib_async": ["ib_async"],
            "dash": ["dash"],
            "seaborn": ["seaborn"],
            "jupyter": ["jupyter", "notebook"],
        }

        for category, modules in dependencies.items():
            self._available[category] = True
            for module in modules:
                try:
                    __import__(module)
                except ImportError:
                    self._available[category] = False
                    break

    def is_available(self, dependency_name: str) -> bool:
        """Check if a dependency is available."""
        return self._available.get(dependency_name, False)

    def get_module(self, module_name: str, fallback: Optional[Any] = None) -> Any:
        """Get a module with optional fallback."""
        if module_name in self._modules:
            return self._modules[module_name]

        try:
            module = __import__(module_name)
            self._modules[module_name] = module
            return module
        except ImportError:
            if fallback is not None:
                return fallback
            logger.warning(f"Module {module_name} not available")
            return None

    def require(self, dependency: str, message: Optional[str] = None) -> bool:
        """Require a dependency to be available."""
        if not self.is_available(dependency):
            error_msg = (
                message or f"Required dependency '{dependency}' is not available"
            )
            raise ImportError(error_msg)
        return True

    def get_status(self) -> Dict[str, bool]:
        """Get status of all dependencies."""
        return self._available.copy()

    def log_status(self) -> None:
        """Log the status of all dependencies."""
        logger.info("Optional Dependencies Status:")
        for dep, available in self._available.items():
            status = "✓ Available" if available else "✗ Not Available"
            logger.info(f"  {dep}: {status}")


# Global dependency manager instance
_dependency_manager = None


def get_dependency_manager() -> DependencyManager:
    """Get the global dependency manager instance."""
    global _dependency_manager
    if _dependency_manager is None:
        _dependency_manager = DependencyManager()
    return _dependency_manager


def require_optional(dependency: str, fallback: Optional[Any] = None):
    """Decorator to require optional dependency for a function or class."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_dependency_manager()
            if not manager.is_available(dependency):
                if fallback:
                    return fallback
                raise ImportError(
                    f"Optional dependency '{dependency}' is required for {func.__name__}"
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_safe_import(module_name: str, fallback: Optional[Any] = None) -> Any:
    """Safely import a module with fallback."""
    manager = get_dependency_manager()
    return manager.get_module(module_name, fallback)


# Convenience functions for common dependencies
def has_plotly() -> bool:
    """Check if plotly is available."""
    return get_dependency_manager().is_available("plotly")


def has_streamlit() -> bool:
    """Check if streamlit is available."""
    return get_dependency_manager().is_available("streamlit")


def has_torch() -> bool:
    """Check if torch is available."""
    return get_dependency_manager().is_available("torch")


def has_transformers() -> bool:
    """Check if transformers is available."""
    return get_dependency_manager().is_available("transformers")


def has_ml() -> bool:
    """Check if ML libraries are available."""
    return has_torch() and has_transformers()


def has_visualization() -> bool:
    """Check if visualization libraries are available."""
    return has_plotly() and has_streamlit()


def has_trading_connectors() -> bool:
    """Check if trading connectors are available."""
    return get_dependency_manager().is_available("ib_async")


# Auto-initialize and log status
def init_dependencies() -> DependencyManager:
    """Initialize dependency manager and log status."""
    manager = get_dependency_manager()
    manager.log_status()
    return manager


# Import commonly needed optional modules with fallbacks
def import_plotly():
    """Import plotly modules with fallback."""
    if has_plotly():
        import plotly.graph_objects as go
        import plotly.express as px
        from plotly.subplots import make_subplots

        return go, px, make_subplots
    else:
        return None, None, None


def import_streamlit():
    """Import streamlit modules with fallback."""
    if has_streamlit():
        import streamlit as st
        from streamlit.components.v1 import html

        return st, html
    else:
        return None, None


def import_torch():
    """Import torch modules with fallback."""
    if has_torch():
        import torch
        import torch.nn as nn
        import torch.optim as optim

        return torch, nn, optim
    else:
        return None, None, None


def import_transformers():
    """Import transformers modules with fallback."""
    if has_transformers():
        import transformers
        from transformers import AutoTokenizer, AutoModel

        return transformers, AutoTokenizer, AutoModel
    else:
        return None, None, None
