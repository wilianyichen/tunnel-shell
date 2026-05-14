"""Retry mechanism for tunnel-shell.

Provides configurable retry logic with support for decorator and direct call patterns.
"""

import functools
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Tuple, Type, Union

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior.
    
    Attributes:
        max_attempts: Maximum number of retry attempts (including initial attempt).
        delay: Initial delay between retries in seconds.
        backoff: Backoff strategy - 'linear' or 'exponential'.
        exceptions: Tuple of exception types that should trigger a retry.
        max_delay: Maximum delay cap for exponential backoff.
    """
    max_attempts: int = 3
    delay: float = 1.0
    backoff: str = 'exponential'
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
    max_delay: float = 60.0
    
    def __post_init__(self):
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.delay < 0:
            raise ValueError("delay must be non-negative")
        if self.backoff not in ('linear', 'exponential'):
            raise ValueError("backoff must be 'linear' or 'exponential'")
        if self.max_delay < self.delay:
            raise ValueError("max_delay must be >= delay")
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number.
        
        Args:
            attempt: Current attempt number (0-indexed).
            
        Returns:
            Delay in seconds before next retry.
        """
        if self.backoff == 'linear':
            delay = self.delay * (attempt + 1)
        else:  # exponential
            delay = self.delay * (2 ** attempt)
        
        return min(delay, self.max_delay)


def retry(
    func: Callable = None,
    *,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: str = 'exponential',
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    max_delay: float = 60.0,
    config: RetryConfig = None,
) -> Callable:
    """Retry decorator and direct call function.
    
    Can be used as a decorator:
        @retry(max_attempts=3, delay=1.0, backoff='exponential')
        def connect(): ...
    
    Or called directly:
        result = retry(some_function, max_attempts=3)
        result = retry(some_function, config=RetryConfig(...))
    
    Args:
        func: Function to wrap/call (optional for decorator usage).
        max_attempts: Maximum retry attempts.
        delay: Initial delay between retries in seconds.
        backoff: Backoff strategy ('linear' or 'exponential').
        exceptions: Exception type(s) that trigger retry.
        max_delay: Maximum delay cap for exponential backoff.
        config: RetryConfig instance (overrides other parameters if provided).
        
    Returns:
        Wrapped function or function result.
    """
    # Build config from parameters if not provided
    if config is None:
        if isinstance(exceptions, type) and issubclass(exceptions, Exception):
            exceptions = (exceptions,)
        config = RetryConfig(
            max_attempts=max_attempts,
            delay=delay,
            backoff=backoff,
            exceptions=exceptions,
            max_delay=max_delay,
        )
    
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            return _retry_call(fn, args, kwargs, config)
        return wrapper
    
    # If func is provided, we're being called directly
    if func is not None:
        if callable(func):
            # Direct call: retry(func, ...)()
            decorated = decorator(func)
            return decorated
        # Should not reach here
        raise TypeError("func must be callable")
    
    # Decorator usage: @retry(...)
    return decorator


def _retry_call(
    func: Callable,
    args: tuple,
    kwargs: dict,
    config: RetryConfig,
) -> Any:
    """Execute a function with retry logic.
    
    Args:
        func: Function to call.
        args: Positional arguments for the function.
        kwargs: Keyword arguments for the function.
        config: Retry configuration.
        
    Returns:
        Function result on success.
        
    Raises:
        The last exception if all retries are exhausted.
    """
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            result = func(*args, **kwargs)
            if attempt > 0:
                logger.info(
                    f"Retry succeeded for {func.__name__} on attempt {attempt + 1}"
                )
            return result
            
        except config.exceptions as e:
            last_exception = e
            
            if attempt < config.max_attempts - 1:
                delay = config.get_delay(attempt)
                logger.warning(
                    f"Retry {attempt + 1}/{config.max_attempts} for {func.__name__}: "
                    f"{type(e).__name__}: {e}. Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"All {config.max_attempts} attempts failed for {func.__name__}: "
                    f"{type(e).__name__}: {e}"
                )
    
    # All retries exhausted, raise the last exception
    raise last_exception


def retry_call(
    func: Callable,
    args: tuple = (),
    kwargs: dict = None,
    *,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: str = 'exponential',
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    max_delay: float = 60.0,
    config: RetryConfig = None,
) -> Any:
    """Direct function call with retry logic.
    
    Example:
        result = retry_call(
            connect_to_server,
            args=('localhost', 8080),
            max_attempts=5,
            delay=2.0,
            exceptions=(ConnectionError, TimeoutError)
        )
    
    Args:
        func: Function to call.
        args: Positional arguments for the function.
        kwargs: Keyword arguments for the function.
        max_attempts: Maximum retry attempts.
        delay: Initial delay between retries in seconds.
        backoff: Backoff strategy ('linear' or 'exponential').
        exceptions: Exception type(s) that trigger retry.
        max_delay: Maximum delay cap for exponential backoff.
        config: RetryConfig instance (overrides other parameters if provided).
        
    Returns:
        Function result on success.
        
    Raises:
        The last exception if all retries are exhausted.
    """
    if kwargs is None:
        kwargs = {}
    
    if config is None:
        if isinstance(exceptions, type) and issubclass(exceptions, Exception):
            exceptions = (exceptions,)
        config = RetryConfig(
            max_attempts=max_attempts,
            delay=delay,
            backoff=backoff,
            exceptions=exceptions,
            max_delay=max_delay,
        )
    
    return _retry_call(func, args, kwargs, config)


__all__ = ['RetryConfig', 'retry', 'retry_call']
