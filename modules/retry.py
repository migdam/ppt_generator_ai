"""
Retry Logic Module
Provides retry decorators and utilities with exponential backoff.
"""

import time
import functools
from typing import Callable, Optional, Tuple, Type
from modules.logger import get_logger

logger = get_logger(__name__)


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


def retry_with_backoff(
    max_retries: int = 4,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator to retry a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (will be exponentially increased)
        max_delay: Maximum delay between retries
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback function called on each retry

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {str(e)}"
                        )
                        raise RetryError(
                            f"Failed after {max_retries} retries: {str(e)}"
                        ) from e

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)

                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    # Call on_retry callback if provided
                    if on_retry:
                        try:
                            on_retry(attempt, e, delay)
                        except Exception as callback_error:
                            logger.warning(f"on_retry callback failed: {callback_error}")

                    time.sleep(delay)

            # This should never be reached, but just in case
            raise RetryError(f"Unexpected retry loop exit") from last_exception

        return wrapper
    return decorator


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""

    def __init__(self, calls_per_minute: int = 60):
        """
        Initialize rate limiter.

        Args:
            calls_per_minute: Maximum number of calls per minute
        """
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute
        self.last_call_time = 0.0

    def wait_if_needed(self) -> None:
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time

        if time_since_last_call < self.min_interval:
            sleep_time = self.min_interval - time_since_last_call
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self.last_call_time = time.time()

    def __call__(self, func: Callable) -> Callable:
        """Use as a decorator."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.wait_if_needed()
            return func(*args, **kwargs)
        return wrapper


def safe_execute(
    func: Callable,
    *args,
    default=None,
    log_errors: bool = True,
    **kwargs
):
    """
    Safely execute a function and return default value on error.

    Args:
        func: Function to execute
        *args: Positional arguments for function
        default: Default value to return on error
        log_errors: Whether to log errors
        **kwargs: Keyword arguments for function

    Returns:
        Function result or default value
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(f"Error in {func.__name__}: {str(e)}")
        return default
