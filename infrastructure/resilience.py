"""可靠性和容错处理"""
import asyncio
import logging
from typing import Callable, TypeVar
from functools import wraps

import pybreaker


T = TypeVar("T")
logger = logging.getLogger(__name__)


class CustomCircuitBreaker:
    """自定义熔断器"""

    def __init__(
        self,
        fail_max: int = 5,
        timeout: int = 60,
        name: str = "default"
    ):
        self.fail_max = fail_max
        self.timeout = timeout
        self.name = name
        self._breaker = pybreaker.CircuitBreaker(
            fail_max=fail_max,
            reset_timeout=timeout
        )

    @property
    def state(self) -> str:
        return self._breaker.current_state

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        try:
            return self._breaker.call(func, *args, **kwargs)
        except pybreaker.CircuitBreakerError:
            logger.warning(f"熔断器 {self.name} 已开启，拒绝调用")
            raise

    async def acall(self, func: Callable[..., T], *args, **kwargs) -> T:
        try:
            return await self._breaker.call_async(func, *args, **kwargs)
        except pybreaker.CircuitBreakerError:
            logger.warning(f"熔断器 {self.name} 已开启，拒绝调用")
            raise


class RetryPolicy:
    """重试策略"""

    def __init__(
        self,
        max_attempts: int = 3,
        backoff_base: float = 2.0,
        initial_delay: float = 1.0,
        exceptions: tuple[type[Exception], ...] = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.backoff_base = backoff_base
        self.initial_delay = initial_delay
        self.exceptions = exceptions

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """执行函数并应用重试策略"""
        last_exception = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except self.exceptions as e:
                last_exception = e
                if attempt == self.max_attempts:
                    logger.error(
                        f"函数 {func.__name__} 重试 {self.max_attempts} 次后仍然失败: {e}"
                    )
                    raise
                delay = self.initial_delay * (self.backoff_base ** (attempt - 1))
                logger.warning(
                    f"函数 {func.__name__} 第 {attempt} 次调用失败，{delay:.2f}秒后重试: {e}"
                )
                await asyncio.sleep(delay)

        raise last_exception


def retry_on_failure(
    max_attempts: int = 3,
    backoff_base: float = 2.0,
    initial_delay: float = 1.0
) -> Callable:
    """重试装饰器"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        policy = RetryPolicy(max_attempts, backoff_base, initial_delay)

        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await policy.execute(func, *args, **kwargs)

        return wrapper
    return decorator


def with_circuit_breaker(
    fail_max: int = 5,
    timeout: int = 60,
    name: str = "default"
) -> Callable:
    """熔断器装饰器"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        breaker = CustomCircuitBreaker(fail_max, timeout, name)

        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await breaker.acall(func, *args, **kwargs)

        return wrapper
    return decorator
