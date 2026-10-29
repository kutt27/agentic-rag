"""
Retry decorator with exponential backoff.

For resilient operations against transient failures.
"""

import asyncio
import functools
import time
from typing import Callable, TypeVar, Optional

from src.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Retry decorator with exponential backoff for sync functions."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts"
                        )
                        raise

                    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)

            raise last_exception  # type: ignore

        return wrapper  # type: ignore

    return decorator


def async_retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Retry decorator with exponential backoff for async functions."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts"
                        )
                        raise

                    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)

            raise last_exception  # type: ignore

        return wrapper  # type: ignore

    return decorator


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        return min(
            self.base_delay * (self.exponential_base ** (attempt - 1)),
            self.max_delay,
        )


default_retry_config = RetryConfig()


if __name__ == "__main__":
    print("Testing retry decorator...")

    call_count = 0

    @retry_with_backoff(max_attempts=3, base_delay=0.1)
    def flaky_function():
        global call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary error")
        return "success"

    result = flaky_function()
    print(f"Result: {result}")
    print(f"Called {call_count} times")

    print("\nTesting async retry...")

    async_count = 0

    @async_retry_with_backoff(max_attempts=3, base_delay=0.1)
    async def flaky_async():
        global async_count
        async_count += 1
        if async_count < 3:
            raise ValueError("Temporary error")
        return "success"

    import asyncio

    result = asyncio.run(flaky_async())
    print(f"Async result: {result}")
    print(f"Async called {async_count} times")