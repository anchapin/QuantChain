"""Retry utilities for data connectors."""

import time
from typing import Callable, Type, Any, Optional, TypeVar
from functools import wraps

from .exceptions import DataSourceError


T = TypeVar("T")


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    logger: Optional[Any] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to add retry logic with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for exponential backoff
        exceptions: Tuple of exception types to catch and retry on
        logger: Optional logger instance for logging retry attempts

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        if logger:
                            logger.error(
                                f"Failed after {max_retries} attempts in "
                                f"{func.__name__}: {str(e)}"
                            )
                        raise DataSourceError(
                            f"Failed after {max_retries} attempts in "
                            f"{func.__name__}: {str(e)}"
                        ) from e

                    delay = base_delay * (backoff_factor**attempt)
                    if logger:
                        logger.warning(
                            f"Attempt {attempt + 1} failed in {func.__name__}: "
                            f"{str(e)}. Retrying in {delay:.2f} seconds..."
                        )
                    time.sleep(delay)

            # This should never be reached, but type checkers like it
            raise DataSourceError("Unexpected error in retry logic") from last_exception

        return wrapper

    return decorator


class RetryHandler:
    """Utility class for retry operations without decorator."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        backoff_factor: float = 2.0,
        logger: Optional[Any] = None,
    ) -> None:
        """Initialize retry handler.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries in seconds
            backoff_factor: Multiplier for exponential backoff
            logger: Optional logger instance
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor
        self.logger = logger

    def execute(
        self,
        func: Callable[..., T],
        *args: Any,
        exceptions: tuple[Type[Exception], ...] = (Exception,),
        **kwargs: Any,
    ) -> T:
        """Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            exceptions: Exception types to catch and retry on
            **kwargs: Keyword arguments for the function

        Returns:
            Function result

        Raises:
            DataSourceError: If all retries are exhausted
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if attempt == self.max_retries - 1:
                    if self.logger:
                        self.logger.error(
                            f"Failed after {self.max_retries} attempts: {str(e)}"
                        )
                    raise DataSourceError(
                        f"Failed after {self.max_retries} attempts: {str(e)}"
                    ) from e

                delay = self.base_delay * (self.backoff_factor**attempt)
                if self.logger:
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed: {str(e)}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                time.sleep(delay)

        # This should never be reached, but type checkers like it
        raise DataSourceError("Unexpected error in retry logic") from last_exception
