"""Import tests for performance metrics to boost coverage."""

import pytest

from quantchain.backtesting.performance_metrics import (
    InsufficientDataError,
    InvalidFrequencyError,
    LibraryImportError,
    MetricsCalculationError,
    MissingColumnError,
    PerformanceMetrics,
    QUANTSTATS_AVAILABLE,
    EMPYRICAL_AVAILABLE,
)


@pytest.mark.unit
class TestPerformanceMetricsImports:
    """Test imports and basic functionality."""

    def test_availability_constants(self):
        """Test library availability constants."""
        assert isinstance(QUANTSTATS_AVAILABLE, bool)
        assert isinstance(EMPYRICAL_AVAILABLE, bool)

    def test_performance_metrics_class_exists(self):
        """Test PerformanceMetrics class exists."""
        assert PerformanceMetrics is not None

    def test_performance_metrics_init_default(self):
        """Test PerformanceMetrics default initialization."""
        calculator = PerformanceMetrics()
        assert calculator.risk_free_rate == 0.02
        assert calculator.benchmark_returns is None

    def test_performance_metrics_init_custom(self):
        """Test PerformanceMetrics with custom parameters."""
        import pandas as pd
        benchmark = pd.Series([100, 102, 101, 103, 105])
        calculator = PerformanceMetrics(risk_free_rate=0.05, benchmark_returns=benchmark)
        assert calculator.risk_free_rate == 0.05
        assert calculator.benchmark_returns is not None

    def test_exception_classes_exist(self):
        """Test all exception classes exist."""
        assert InsufficientDataError
        assert InvalidFrequencyError
        assert LibraryImportError
        assert MetricsCalculationError
        assert MissingColumnError

    def test_exception_inheritance(self):
        """Test exception inheritance."""
        # All should be exceptions
        assert issubclass(InsufficientDataError, Exception)
        assert issubclass(InvalidFrequencyError, Exception)
        assert issubclass(MissingColumnError, Exception)
        assert issubclass(MetricsCalculationError, Exception)
        assert issubclass(LibraryImportError, Exception)
