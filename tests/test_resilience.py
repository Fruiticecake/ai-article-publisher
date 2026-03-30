"""测试可靠性和容错"""
import pytest
import asyncio
from infrastructure.resilience import RetryPolicy, CustomCircuitBreaker


class TestRetryPolicy:
    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        async def success_func():
            return "success"

        policy = RetryPolicy(max_attempts=3)
        result = await policy.execute(success_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        call_count = [0]

        async def flaky_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("First attempt fails")
            return "success"

        policy = RetryPolicy(max_attempts=3)
        result = await policy.execute(flaky_func)
        assert result == "success"
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_max_attempts_exceeded(self):
        async def always_fail():
            raise ValueError("Always fails")

        policy = RetryPolicy(max_attempts=2)
        with pytest.raises(ValueError):
            await policy.execute(always_fail)


class TestCircuitBreaker:
    def test_initial_state(self):
        breaker = CustomCircuitBreaker(fail_max=5)
        assert breaker.state == "closed"

    def test_circuit_breaker_error(self):
        import pybreaker
        breaker = CustomCircuitBreaker(fail_max=1)

        async def fail_func():
            raise ValueError("Fail")

        # 触发失败，熔断器打开
        try:
            asyncio.run(breaker.acall(fail_func))
        except ValueError:
            pass

        # 再次调用应该被熔断器阻止
        with pytest.raises(pybreaker.CircuitBreakerError):
            asyncio.run(breaker.acall(fail_func))
