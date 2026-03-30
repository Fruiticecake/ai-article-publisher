"""监控和指标收集"""
import logging
import time
from functools import wraps
from typing import Callable, TypeVar

from prometheus_client import Counter, Histogram, Gauge, start_http_server


logger = logging.getLogger(__name__)
T = TypeVar("T")


# Prometheus 指标定义
request_count = Counter(
    'auto_publisher_requests_total',
    'Total number of requests',
    ['endpoint', 'method', 'status']
)

request_duration = Histogram(
    'auto_publisher_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint', 'method']
)

projects_processed = Counter(
    'auto_publisher_projects_processed_total',
    'Total number of projects processed',
    ['source']
)

publish_success = Counter(
    'auto_publisher_publish_success_total',
    'Total number of successful publishes',
    ['platform']
)

publish_failed = Counter(
    'auto_publisher_publish_failed_total',
    'Total number of failed publishes',
    ['platform', 'error']
)

active_tasks = Gauge(
    'auto_publisher_active_tasks',
    'Number of currently active tasks'
)

github_api_calls = Counter(
    'auto_publisher_github_api_calls_total',
    'Total number of GitHub API calls',
    ['endpoint']
)

github_api_errors = Counter(
    'auto_publisher_github_api_errors_total',
    'Total number of GitHub API errors',
    ['endpoint', 'status_code']
)


def monitor_request(endpoint: str, method: str = "GET"):
    """请求监控装饰器"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logger.error(f"Request failed: {e}")
                raise
            finally:
                duration = time.time() - start_time
                request_count.labels(endpoint=endpoint, method=method, status=status).inc()
                request_duration.labels(endpoint=endpoint, method=method).observe(duration)

        return wrapper
    return decorator


def track_active_tasks(func: Callable[..., T]) -> Callable[..., T]:
    """追踪活跃任务"""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        active_tasks.inc()
        try:
            return await func(*args, **kwargs)
        finally:
            active_tasks.dec()
    return wrapper


class MetricsCollector:
    """指标收集器"""

    def __init__(self, metrics_port: int = 8000):
        self.metrics_port = metrics_port
        self._started = False

    def start(self) -> None:
        """启动指标服务器"""
        if not self._started:
            start_http_server(self.metrics_port)
            self._started = True
            logger.info(f"Metrics server started on port {self.metrics_port}")

    def record_project_processed(self, source: str) -> None:
        """记录处理的项目"""
        projects_processed.labels(source=source).inc()

    def record_publish_success(self, platform: str) -> None:
        """记录成功的发布"""
        publish_success.labels(platform=platform).inc()

    def record_publish_failed(self, platform: str, error: str) -> None:
        """记录失败的发布"""
        publish_failed.labels(platform=platform, error=error[:50]).inc()

    def record_github_api_call(self, endpoint: str) -> None:
        """记录 GitHub API 调用"""
        github_api_calls.labels(endpoint=endpoint).inc()

    def record_github_api_error(self, endpoint: str, status_code: int) -> None:
        """记录 GitHub API 错误"""
        github_api_errors.labels(endpoint=endpoint, status_code=str(status_code)).inc()


# 全局指标收集器实例
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    return _metrics_collector
