"""缓存管理"""
import json
import hashlib
from typing import Any, Callable, TypeVar
from functools import wraps

T = TypeVar("T")


class SimpleCache:
    """简单内存缓存"""

    def __init__(self, ttl: int = 3600):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl

    def get(self, key: str) -> Any | None:
        import time
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        import time
        expiry = time.time() + (ttl or self._ttl)
        self._cache[key] = (value, expiry)

    def invalidate(self, pattern: str | None = None) -> None:
        if pattern:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for k in keys_to_delete:
                del self._cache[k]
        else:
            self._cache.clear()


_global_cache = SimpleCache()


def cache_result(ttl: int = 3600, key_prefix: str = "") -> Callable:
    """缓存装饰器"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # 生成缓存键
            cache_key = key_prefix + hashlib.md5(
                json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True).encode()
            ).hexdigest()

            # 尝试从缓存获取
            cached = _global_cache.get(cache_key)
            if cached is not None:
                return cached

            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            _global_cache.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator


def invalidate_cache(pattern: str) -> None:
    """使缓存失效"""
    _global_cache.invalidate(pattern)
