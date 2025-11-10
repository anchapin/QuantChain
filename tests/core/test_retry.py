"""Tests for retry utilities."""

from unittest.mock import Mock, patch

import pytest

from quantchain.core.exceptions import DataSourceError
from quantchain.core.retry import RetryHandler, with_retry


@pytest.mark.unit
class TestWithRetryDecorator:
    """Test suite for with_retry decorator."""

    def test_successful_execution_no_retry(self) -> None:
        """Test that successful function doesn't retry."""
        mock_func = Mock(return_value="success")

        @with_retry(max_retries=3)
        def test_func() -> str:
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_on_exception(self) -> None:
        """Test retry behavior on exception."""
        mock_func = Mock(
            side_effect=[ValueError("fail"), ValueError("fail"), "success"]
        )

        @with_retry(max_retries=3, base_delay=0.01)
        def test_func() -> str:
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 3

    def test_max_retries_exceeded(self) -> None:
        """Test behavior when max retries exceeded."""
        mock_func = Mock(side_effect=ValueError("always fails"))

        @with_retry(max_retries=2, base_delay=0.01)
        def test_func() -> str:
            return mock_func()

        with pytest.raises(
            DataSourceError, match="Failed after 2 attempts"
        ) as exc_info:
            test_func()

        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ValueError)
        assert mock_func.call_count == 2

    def test_specific_exception_types(self) -> None:
        """Test retry on specific exception types only."""
        mock_func = Mock(side_effect=[ValueError("fail"), TypeError("fail"), "success"])

        @with_retry(max_retries=3, base_delay=0.01, exceptions=(ValueError,))
        def test_func() -> str:
            return mock_func()

        # Should fail on TypeError (not in exceptions tuple)
        with pytest.raises(TypeError):
            test_func()

        assert (
            mock_func.call_count == 2
        )  # One retry on ValueError, then fail on TypeError

    def test_exponential_backoff(self) -> None:
        """Test exponential backoff delay calculation."""
        mock_func = Mock(side_effect=[ValueError("fail")] * 4 + ["success"])
        delays: list[float] = []

        @with_retry(max_retries=5, base_delay=0.1, backoff_factor=2.0)
        def test_func() -> str:
            return mock_func()

        with patch("time.sleep") as mock_sleep:
            test_func()
            # Capture delay arguments from sleep calls
            delays.extend(call.args[0] for call in mock_sleep.call_args_list)

        expected_delays: list[float] = [0.1, 0.2, 0.4, 0.8]  # base * (factor^attempt)
        assert delays == expected_delays

    def test_retry_with_logging(self) -> None:
        """Test retry behavior with logger."""
        mock_func = Mock(
            side_effect=[ValueError("fail"), ValueError("fail"), "success"]
        )
        mock_logger = Mock()

        @with_retry(max_retries=3, base_delay=0.01, logger=mock_logger)
        def test_func() -> str:
            return mock_func()

        result = test_func()

        assert result == "success"

        # Check warning logs for retries
        assert mock_logger.warning.call_count == 2
        warning_calls = [
            str(call.args[0]) for call in mock_logger.warning.call_args_list
        ]
        assert all("Attempt" in call and "failed" in call for call in warning_calls)

    def test_retry_logging_on_final_failure(self) -> None:
        """Test error logging when all retries exhausted."""
        mock_func = Mock(side_effect=ValueError("always fails"))
        mock_logger = Mock()

        @with_retry(max_retries=2, base_delay=0.01, logger=mock_logger)
        def test_func() -> str:
            return mock_func()

        with pytest.raises(DataSourceError):
            test_func()

        # Check error log for final failure
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args[0][0]
        assert "Failed after 2 attempts" in error_call

    def test_default_parameters(self) -> None:
        """Test with default parameters."""
        mock_func = Mock(return_value="success")

        @with_retry()
        def test_func() -> str:
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 1

    def test_function_args_and_kwargs(self) -> None:
        """Test that function arguments are passed correctly."""
        mock_func = Mock(return_value="success")

        @with_retry(max_retries=2)
        def test_func(arg1: str, arg2: int, kwarg1: float = 1.0) -> str:
            return mock_func(arg1, arg2, kwarg1=kwarg1)

        result = test_func("test", 42, kwarg1=3.14)

        assert result == "success"
        mock_func.assert_called_once_with("test", 42, kwarg1=3.14)

    def test_function_metadata_preserved(self) -> None:
        """Test that function metadata is preserved."""

        @with_retry(max_retries=2)
        def test_func(x: int) -> int:
            """Test function docstring."""
            return x * 2

        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test function docstring."

    def test_no_retry_on_success_first_attempt(self) -> None:
        """Test that no delay occurs on successful first attempt."""
        mock_func = Mock(return_value="success")

        @with_retry(max_retries=3, base_delay=1.0)
        def test_func() -> str:
            return mock_func()

        with patch("time.sleep") as mock_sleep:
            result = test_func()

        assert result == "success"
        mock_sleep.assert_not_called()


@pytest.mark.unit
class TestRetryHandler:
    """Test suite for RetryHandler class."""

    def test_handler_initialization(self) -> None:
        """Test RetryHandler initialization."""
        handler = RetryHandler(max_retries=5, base_delay=0.5, backoff_factor=1.5)

        assert handler.max_retries == 5
        assert handler.base_delay == 0.5
        assert handler.backoff_factor == 1.5
        assert handler.logger is None

    def test_handler_successful_execution(self) -> None:
        """Test successful execution through handler."""
        handler = RetryHandler(max_retries=3)
        mock_func = Mock(return_value="success")

        result = handler.execute(mock_func)

        assert result == "success"
        mock_func.assert_called_once()

    def test_handler_retry_logic(self) -> None:
        """Test retry logic through handler."""
        handler = RetryHandler(max_retries=3, base_delay=0.01)
        mock_func = Mock(
            side_effect=[ValueError("fail"), ValueError("fail"), "success"]
        )

        result = handler.execute(mock_func)

        assert result == "success"
        assert mock_func.call_count == 3

    def test_handler_max_retries_exceeded(self) -> None:
        """Test handler behavior when max retries exceeded."""
        handler = RetryHandler(max_retries=2, base_delay=0.01)
        mock_func = Mock(side_effect=ValueError("always fails"))

        with pytest.raises(DataSourceError, match="Failed after 2 attempts"):
            handler.execute(mock_func)

        assert mock_func.call_count == 2

    def test_handler_with_specific_exceptions(self) -> None:
        """Test handler with specific exception types."""
        handler = RetryHandler(max_retries=2, base_delay=0.01)
        mock_func = Mock(side_effect=[ValueError("fail"), TypeError("fail")])

        # Should retry on ValueError but fail immediately on TypeError
        with pytest.raises(TypeError):
            handler.execute(mock_func, exceptions=(ValueError,))

        assert mock_func.call_count == 2

    def test_handler_with_logging(self) -> None:
        """Test handler behavior with logger."""
        mock_logger = Mock()
        handler = RetryHandler(max_retries=3, base_delay=0.01, logger=mock_logger)
        mock_func = Mock(
            side_effect=[ValueError("fail"), ValueError("fail"), "success"]
        )

        result = handler.execute(mock_func)

        assert result == "success"
        assert mock_logger.warning.call_count == 2

    def test_handler_function_arguments(self) -> None:
        """Test handler passes function arguments correctly."""
        handler = RetryHandler(max_retries=2)
        mock_func = Mock(return_value="success")

        result = handler.execute(mock_func, "arg1", "arg2", kwarg1="value")

        assert result == "success"
        mock_func.assert_called_once_with("arg1", "arg2", kwarg1="value")

    def test_handler_exponential_backoff(self) -> None:
        """Test handler exponential backoff."""
        handler = RetryHandler(max_retries=3, base_delay=0.1, backoff_factor=2.0)
        mock_func = Mock(side_effect=[ValueError("fail")] * 4)
        delays: list[float] = []

        with patch("time.sleep") as mock_sleep:
            try:
                handler.execute(mock_func)
            except DataSourceError:
                pass  # Expected

            delays.extend(call.args[0] for call in mock_sleep.call_args_list)

        # With max_retries=3, we get delays for attempts 0, 1, 2 but
        # the handler only sleeps on first 2 failures
        expected_delays: list[float] = [0.1, 0.2]
        assert delays == expected_delays

    def test_handler_no_logger(self) -> None:
        """Test handler behavior without logger."""
        handler = RetryHandler(max_retries=2, base_delay=0.01)
        mock_func = Mock(side_effect=ValueError("always fails"))

        # Should not raise any logging errors
        with pytest.raises(DataSourceError):
            handler.execute(mock_func)

    def test_handler_error_logging(self) -> None:
        """Test handler error logging on final failure."""
        mock_logger = Mock()
        handler = RetryHandler(max_retries=2, base_delay=0.01, logger=mock_logger)
        mock_func = Mock(side_effect=ValueError("always fails"))

        with pytest.raises(DataSourceError):
            handler.execute(mock_func)

        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args[0][0]
        assert "Failed after 2 attempts" in error_call
