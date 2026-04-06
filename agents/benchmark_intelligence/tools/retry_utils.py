"""
Retry utilities with exponential backoff for Benchmark Intelligence System.

Provides generic retry wrapper with configurable exponential backoff
for handling transient failures in document fetching, API calls, etc.
"""

import logging
import time
from typing import Callable, Any, Optional, Dict
from functools import wraps

logger = logging.getLogger(__name__)


def retry_with_exponential_backoff(
    func: Callable,
    config: Dict[str, Any],
    *args,
    **kwargs
) -> Any:
    """
    Execute a function with exponential backoff retry logic.

    Retries the function on failure with increasing delays between attempts.
    Uses exponential backoff: delay = initial_delay * (backoff_multiplier ^ attempt)

    Args:
        func: Function to execute
        config: Retry configuration dict containing:
            - max_attempts: Maximum number of retry attempts (default: 3)
            - initial_delay_seconds: Initial delay in seconds (default: 1)
            - backoff_multiplier: Multiplier for exponential backoff (default: 2)
            - max_delay_seconds: Maximum delay cap in seconds (default: 60)
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result of successful function execution

    Raises:
        Last exception raised if all retries fail

    Example:
        >>> config = {
        ...     "max_attempts": 3,
        ...     "initial_delay_seconds": 1,
        ...     "backoff_multiplier": 2,
        ...     "max_delay_seconds": 60
        ... }
        >>> result = retry_with_exponential_backoff(
        ...     fetch_document,
        ...     config,
        ...     url="https://example.com"
        ... )
    """
    max_attempts = config.get("max_attempts", 3)
    initial_delay = config.get("initial_delay_seconds", 1)
    backoff_multiplier = config.get("backoff_multiplier", 2)
    max_delay = config.get("max_delay_seconds", 60)

    last_exception = None

    for attempt in range(max_attempts):
        try:
            # Execute the function
            result = func(*args, **kwargs)

            # Success - return immediately
            if attempt > 0:
                logger.info(f"Succeeded on attempt {attempt + 1}/{max_attempts}")
            return result

        except Exception as e:
            last_exception = e

            # If this was the last attempt, don't retry
            if attempt == max_attempts - 1:
                logger.error(
                    f"Failed after {max_attempts} attempts: {e}"
                )
                break

            # Calculate delay with exponential backoff
            delay = min(
                initial_delay * (backoff_multiplier ** attempt),
                max_delay
            )

            logger.warning(
                f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                f"Retrying in {delay}s..."
            )

            # Wait before retrying
            time.sleep(delay)

    # All retries failed - raise the last exception
    raise last_exception


def with_retry(config: Optional[Dict[str, Any]] = None):
    """
    Decorator to add retry logic with exponential backoff to a function.

    Args:
        config: Retry configuration dict (see retry_with_exponential_backoff for keys)
                If None, uses default configuration

    Returns:
        Decorator function

    Example:
        >>> @with_retry({"max_attempts": 3, "initial_delay_seconds": 1})
        ... def fetch_data(url):
        ...     return requests.get(url)
        >>>
        >>> data = fetch_data("https://example.com")
    """
    # Default configuration
    default_config = {
        "max_attempts": 3,
        "initial_delay_seconds": 1,
        "backoff_multiplier": 2,
        "max_delay_seconds": 60
    }

    # Merge with provided config
    retry_config = {**default_config, **(config or {})}

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_with_exponential_backoff(
                func,
                retry_config,
                *args,
                **kwargs
            )
        return wrapper

    return decorator


def retry_on_rate_limit(
    func: Callable,
    config: Dict[str, Any],
    rate_limit_exceptions: tuple = (Exception,),
    *args,
    **kwargs
) -> Any:
    """
    Retry function specifically for rate limit scenarios.

    Similar to retry_with_exponential_backoff but specifically designed
    for rate limiting scenarios. Only retries on specific exception types.

    Args:
        func: Function to execute
        config: Retry configuration dict
        rate_limit_exceptions: Tuple of exception types to retry on
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result of successful function execution

    Raises:
        Exception if not a rate limit error or all retries fail

    Example:
        >>> result = retry_on_rate_limit(
        ...     api_call,
        ...     config,
        ...     rate_limit_exceptions=(RateLimitError, TimeoutError),
        ...     endpoint="/models"
        ... )
    """
    max_attempts = config.get("max_attempts", 3)
    initial_delay = config.get("initial_delay_seconds", 1)
    backoff_multiplier = config.get("backoff_multiplier", 2)
    max_delay = config.get("max_delay_seconds", 60)

    last_exception = None

    for attempt in range(max_attempts):
        try:
            result = func(*args, **kwargs)

            if attempt > 0:
                logger.info(
                    f"Rate limit retry succeeded on attempt {attempt + 1}/{max_attempts}"
                )
            return result

        except rate_limit_exceptions as e:
            last_exception = e

            # If this was the last attempt, don't retry
            if attempt == max_attempts - 1:
                logger.error(
                    f"Rate limit retry failed after {max_attempts} attempts: {e}"
                )
                break

            # Calculate delay with exponential backoff
            delay = min(
                initial_delay * (backoff_multiplier ** attempt),
                max_delay
            )

            logger.warning(
                f"Rate limit hit (attempt {attempt + 1}/{max_attempts}): {e}. "
                f"Backing off for {delay}s..."
            )

            time.sleep(delay)

        except Exception as e:
            # Not a rate limit error - fail immediately
            logger.error(f"Non-rate-limit error occurred: {e}")
            raise

    # All retries failed - raise the last exception
    raise last_exception
