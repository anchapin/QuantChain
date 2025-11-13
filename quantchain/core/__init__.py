"""
Core module initialization for QuantChain.
"""

from .config import Config
from .exceptions import (
    QuantChainError,
    ConfigurationError,
    DataError,
    ModelError,
    ConnectorError,
    SecurityError,
)
from .dependency_manager import (
    get_dependency_manager,
    init_dependencies,
    has_plotly,
    has_streamlit,
    has_torch,
    has_transformers,
    has_ml,
    has_visualization,
    has_trading_connectors,
    require_optional,
    get_safe_import,
)

# Initialize dependencies and log status
_dependency_manager = None


def get_core_dependency_manager():
    """Get core dependency manager instance."""
    global _dependency_manager
    if _dependency_manager is None:
        from .dependency_manager import DependencyManager

        _dependency_manager = DependencyManager()
    return _dependency_manager


# Export public API
__all__ = [
    "Config",
    "QuantChainError",
    "ConfigurationError",
    "DataError",
    "ModelError",
    "ConnectorError",
    "SecurityError",
    "get_dependency_manager",
    "init_dependencies",
    "has_plotly",
    "has_streamlit",
    "has_torch",
    "has_transformers",
    "has_ml",
    "has_visualization",
    "has_trading_connectors",
    "require_optional",
    "get_safe_import",
]
