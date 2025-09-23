"""Resilience and error recovery mechanisms for the offshore leaks server."""

import asyncio
import logging
import time
from collections.abc import Awaitable
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorType(Enum):
    """Types of errors that can occur."""

    DATABASE_CONNECTION = "database_connection"
    QUERY_TIMEOUT = "query_timeout"
    QUERY_ERROR = "query_error"
    VALIDATION_ERROR = "validation_error"
    NETWORK_ERROR = "network_error"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNKNOWN = "unknown"


@dataclass
class RetryConfig:
    """Configuration for retry mechanisms."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    backoff_strategy: str = "exponential"  # "exponential", "linear", "fixed"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: type = Exception


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker pattern implementation."""

    def __init__(self, config: CircuitBreakerConfig):
        """Initialize circuit breaker."""
        self.config = config
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED

    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time >= self.config.recovery_timeout
            ):
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True

    def record_success(self) -> None:
        """Record successful execution."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def record_failure(self) -> None:
        """Record failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class RetryableError(Exception):
    """Base class for retryable errors."""

    def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN):
        super().__init__(message)
        self.error_type = error_type


class NonRetryableError(Exception):
    """Base class for non-retryable errors."""

    def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN):
        super().__init__(message)
        self.error_type = error_type


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay for retry attempt."""
    if config.backoff_strategy == "exponential":
        delay = config.base_delay * (config.exponential_base ** (attempt - 1))
    elif config.backoff_strategy == "linear":
        delay = config.base_delay * attempt
    else:  # fixed
        delay = config.base_delay

    # Apply max delay limit
    delay = min(delay, config.max_delay)

    # Add jitter if enabled
    if config.jitter:
        import random

        delay = delay * (0.5 + random.random() * 0.5)  # nosec B311

    return delay


def retry_async(
    config: RetryConfig,
    retryable_exceptions: tuple = (RetryableError,),
    non_retryable_exceptions: tuple = (NonRetryableError,),
):
    """Decorator for async functions with retry logic."""

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 1:
                        logger.info(f"{func.__name__} succeeded on attempt {attempt}")
                    return result

                except non_retryable_exceptions as e:
                    logger.error(
                        f"{func.__name__} failed with non-retryable error: {e}"
                    )
                    raise

                except retryable_exceptions as e:
                    last_exception = e
                    if attempt == config.max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {config.max_attempts} attempts: {e}"
                        )
                        break

                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)

                except Exception as e:
                    # Unknown exception - treat as non-retryable by default
                    logger.error(f"{func.__name__} failed with unknown error: {e}")
                    raise

            # All retries exhausted
            raise last_exception or Exception("All retry attempts failed")

        return wrapper

    return decorator


def with_circuit_breaker(circuit_breaker: CircuitBreaker):
    """Decorator to add circuit breaker protection."""

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            if not circuit_breaker.can_execute():
                raise Exception(f"Circuit breaker is {circuit_breaker.state.value}")

            try:
                result = await func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except circuit_breaker.config.expected_exception:
                circuit_breaker.record_failure()
                raise

        return wrapper

    return decorator


class ErrorClassifier:
    """Classify errors to determine retry strategy."""

    @staticmethod
    def classify_database_error(error: Exception) -> ErrorType:
        """Classify database-related errors."""
        error_msg = str(error).lower()

        if any(
            keyword in error_msg
            for keyword in [
                "connection refused",
                "connection failed",
                "network error",
                "connection lost",
                "connection timeout",
                "host unreachable",
            ]
        ):
            return ErrorType.DATABASE_CONNECTION

        elif any(
            keyword in error_msg
            for keyword in ["timeout", "timed out", "deadline exceeded"]
        ):
            return ErrorType.QUERY_TIMEOUT

        elif any(
            keyword in error_msg
            for keyword in ["syntax error", "invalid query", "constraint violation"]
        ):
            return ErrorType.QUERY_ERROR

        else:
            return ErrorType.UNKNOWN

    @staticmethod
    def is_retryable(error: Exception, error_type: ErrorType) -> bool:
        """Determine if an error is retryable."""
        if isinstance(error, NonRetryableError):
            return False

        if isinstance(error, RetryableError):
            return True

        # Classification-based retry logic
        retryable_types = {
            ErrorType.DATABASE_CONNECTION,
            ErrorType.QUERY_TIMEOUT,
            ErrorType.NETWORK_ERROR,
            ErrorType.RESOURCE_EXHAUSTION,
        }

        return error_type in retryable_types


class ResilienceManager:
    """Manages resilience mechanisms for the offshore leaks server."""

    def __init__(self):
        """Initialize resilience manager."""
        self.retry_configs = {
            ErrorType.DATABASE_CONNECTION: RetryConfig(
                max_attempts=5, base_delay=2.0, max_delay=30.0, exponential_base=2.0
            ),
            ErrorType.QUERY_TIMEOUT: RetryConfig(
                max_attempts=3, base_delay=1.0, max_delay=10.0, exponential_base=1.5
            ),
            ErrorType.NETWORK_ERROR: RetryConfig(
                max_attempts=4, base_delay=1.5, max_delay=20.0, exponential_base=2.0
            ),
        }

        self.circuit_breakers = {
            "database": CircuitBreaker(
                CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30.0)
            ),
            "query_engine": CircuitBreaker(
                CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0)
            ),
        }

        self.error_counts = dict.fromkeys(ErrorType, 0)
        self.last_errors = {}

    def get_retry_config(self, error_type: ErrorType) -> RetryConfig:
        """Get retry configuration for error type."""
        return self.retry_configs.get(error_type, RetryConfig())

    def record_error(self, error: Exception, error_type: ErrorType = None) -> None:
        """Record error occurrence for monitoring."""
        if error_type is None:
            error_type = ErrorClassifier.classify_database_error(error)

        self.error_counts[error_type] += 1
        self.last_errors[error_type] = {"error": str(error), "timestamp": time.time()}

        logger.warning(f"Error recorded: {error_type.value} - {error}")

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            "error_counts": {
                et.value: count for et, count in self.error_counts.items()
            },
            "circuit_breaker_states": {
                name: cb.state.value for name, cb in self.circuit_breakers.items()
            },
            "last_errors": {et.value: info for et, info in self.last_errors.items()},
        }

    async def execute_with_resilience(
        self,
        func: Callable[..., Awaitable[T]],
        error_type: ErrorType = ErrorType.UNKNOWN,
        circuit_breaker_name: Optional[str] = None,
        *args,
        **kwargs,
    ) -> T:
        """Execute function with full resilience mechanisms."""

        # Get appropriate circuit breaker
        circuit_breaker = None
        if circuit_breaker_name and circuit_breaker_name in self.circuit_breakers:
            circuit_breaker = self.circuit_breakers[circuit_breaker_name]

        # Get retry configuration
        retry_config = self.get_retry_config(error_type)

        # Apply resilience mechanisms
        resilient_func = func

        if circuit_breaker:
            resilient_func = with_circuit_breaker(circuit_breaker)(resilient_func)

        # Add retry logic
        @retry_async(retry_config)
        async def retryable_func(*f_args, **f_kwargs):
            try:
                return await resilient_func(*f_args, **f_kwargs)
            except Exception as e:
                classified_type = ErrorClassifier.classify_database_error(e)
                self.record_error(e, classified_type)

                if ErrorClassifier.is_retryable(e, classified_type):
                    raise RetryableError(str(e), classified_type)
                else:
                    raise NonRetryableError(str(e), classified_type)

        return await retryable_func(*args, **kwargs)


class HealthChecker:
    """Health checking for various system components."""

    def __init__(self):
        """Initialize health checker."""
        self.component_status = {}
        self.last_check_times = {}

    async def check_database_health(self, database) -> Dict[str, Any]:
        """Check database health."""
        try:
            await database.health_check()
            status = {
                "status": "healthy",
                "timestamp": time.time(),
                "connected": database.is_connected,
            }
        except Exception as e:
            status = {
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e),
                "connected": False,
            }

        self.component_status["database"] = status
        self.last_check_times["database"] = time.time()
        return status

    async def check_server_health(self, server) -> Dict[str, Any]:
        """Check server health."""
        try:
            status = {
                "status": "healthy" if server.is_running else "stopped",
                "timestamp": time.time(),
                "running": server.is_running,
            }
        except Exception as e:
            status = {
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e),
                "running": False,
            }

        self.component_status["server"] = status
        self.last_check_times["server"] = time.time()
        return status

    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        all_healthy = all(
            status.get("status") == "healthy"
            for status in self.component_status.values()
        )

        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": time.time(),
            "components": self.component_status,
            "last_check_times": self.last_check_times,
        }


class GracefulShutdown:
    """Handle graceful shutdown of server components."""

    def __init__(self):
        """Initialize graceful shutdown handler."""
        self.shutdown_hooks = []
        self.is_shutting_down = False

    def add_shutdown_hook(self, hook: Callable[[], Awaitable[None]]) -> None:
        """Add a shutdown hook."""
        self.shutdown_hooks.append(hook)

    async def shutdown(self, timeout: float = 30.0) -> None:
        """Perform graceful shutdown."""
        if self.is_shutting_down:
            return

        self.is_shutting_down = True
        logger.info("Initiating graceful shutdown...")

        # Execute shutdown hooks
        for hook in reversed(self.shutdown_hooks):  # Reverse order
            try:
                await asyncio.wait_for(
                    hook(), timeout=timeout / len(self.shutdown_hooks)
                )
                logger.info(f"Shutdown hook {hook.__name__} completed")
            except asyncio.TimeoutError:
                logger.warning(f"Shutdown hook {hook.__name__} timed out")
            except Exception as e:
                logger.error(f"Shutdown hook {hook.__name__} failed: {e}")

        logger.info("Graceful shutdown completed")


# Global resilience manager instance
resilience_manager = ResilienceManager()


# Convenience decorators using global manager
def database_resilient(
    func: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[T]]:
    """Decorator for database operations with resilience."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        return await resilience_manager.execute_with_resilience(
            func, ErrorType.DATABASE_CONNECTION, "database", *args, **kwargs
        )

    return wrapper


def query_resilient(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Decorator for query operations with resilience."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        return await resilience_manager.execute_with_resilience(
            func, ErrorType.QUERY_TIMEOUT, "query_engine", *args, **kwargs
        )

    return wrapper
