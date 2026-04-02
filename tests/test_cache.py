"""测试缓存模块"""
import pytest
import time
from infrastructure.cache import SimpleCache, cache_result, invalidate_cache, _global_cache


class TestSimpleCache:
    """测试简单内存缓存"""

    def test_cache_set_and_get(self):
        """测试设置和获取缓存"""
        cache = SimpleCache(ttl=3600)
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

    def test_cache_get_not_exists(self):
        """测试获取不存在的缓存"""
        cache = SimpleCache()
        assert cache.get("not_exists") is None

    def test_cache_expiration(self):
        """测试缓存过期"""
        cache = SimpleCache(ttl=1)  # 1秒过期
        cache.set("quick_expire", "value")
        assert cache.get("quick_expire") == "value"
        time.sleep(1.1)
        assert cache.get("quick_expire") is None

    def test_cache_custom_ttl_override(self):
        """测试自定义 TTL 覆盖默认值"""
        cache = SimpleCache(ttl=3600)
        cache.set("short_ttl", "value", ttl=1)
        assert cache.get("short_ttl") == "value"
        time.sleep(1.1)
        assert cache.get("short_ttl") is None

    def test_invalidate_all(self):
        """测试清空所有缓存"""
        cache = SimpleCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.invalidate()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_invalidate_by_pattern(self):
        """测试按模式清空缓存"""
        cache = SimpleCache()
        cache.set("github:repo1", "value1")
        cache.set("github:repo2", "value2")
        cache.set("other:key", "value3")
        cache.invalidate("github:")
        assert cache.get("github:repo1") is None
        assert cache.get("github:repo2") is None
        assert cache.get("other:key") == "value3"


class TestCacheDecorator:
    """测试缓存装饰器"""

    @pytest.mark.asyncio
    async def test_cache_result_decorator(self):
        """测试缓存装饰器缓存结果"""
        call_count = []

        @cache_result(ttl=10)
        async def expensive_computation(x: int, y: int) -> int:
            call_count.append(1)
            return x + y

        # 第一次调用
        result1 = await expensive_computation(1, 2)
        assert result1 == 3
        assert len(call_count) == 1

        # 第二次调用应该命中缓存
        result2 = await expensive_computation(1, 2)
        assert result2 == 3
        assert len(call_count) == 1  # 还是1，说明缓存命中

    @pytest.mark.asyncio
    async def test_cache_different_args_different_cache(self):
        """测试不同参数不同缓存"""
        from infrastructure.cache import _global_cache
        _global_cache.invalidate()  # 清空缓存确保测试干净
        call_count = []

        @cache_result(ttl=10)
        async def add(a: int, b: int) -> int:
            call_count.append(1)
            return a + b

        await add(1, 2)
        await add(3, 4)
        assert len(call_count) == 2

    def test_invalidate_cache_global(self):
        """测试清空全局缓存"""
        # 清空所有缓存确保测试干净
        invalidate_cache(None)
        assert _global_cache.get("any_key") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
