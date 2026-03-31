"""任务队列系统"""
import logging
import json
from typing import Any, Callable
from datetime import datetime
import redis
from redis.exceptions import RedisError

from config_new import SETTINGS


logger = logging.getLogger(__name__)


class TaskQueue:
    """简单的任务队列（基于 Redis）"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        queue_name: str = "auto_publisher_tasks",
    ):
        self.queue_name = queue_name
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info(f"Redis 连接成功: {redis_url}")
        except RedisError as e:
            logger.warning(f"Redis 连接失败，使用内存队列: {e}")
            self.redis_client = None
            self._memory_queue = []

    def enqueue(
        self,
        task_name: str,
        task_data: dict[str, Any],
        priority: int = 0,
    ) -> bool:
        """将任务加入队列"""
        task = {
            "task_name": task_name,
            "task_data": task_data,
            "priority": priority,
            "enqueued_at": datetime.utcnow().isoformat(),
            "status": "pendingQUEUED",
        }

        try:
            if self.redis_client:
                # 使用有序集合实现优先级队列
                score = -priority  # 负值使得高优先级排在前面
                self.redis_client.zadd(self.queue_name, {json.dumps(task): score})
                logger.info(f"任务已加入队列: {task_name}")
                return True
            else:
                # 使用内存队列
                self._memory_queue.append(task)
                self._memory_queue.sort(key=lambda x: -x["priority"])
                logger.info(f"任务已加入内存队列: {task_name}")
                return True
        except Exception as e:
            logger.error(f"任务入队失败: {e}")
            return False

    def dequeue(self) -> dict[str, Any] | None:
        """从队列中取出任务"""
        try:
            if self.redis_client:
                # 从有序集合中取出最高优先级的任务
                result = self.redis_client.zpopmax(self.queue_name)
                if result:
                    task_json = result[0][0]
                    return json.loads(task_json)
                return None
            else:
                if self._memory_queue:
                    return self._memory_queue.pop(0)
                return None
        except Exception as e:
            logger.error(f"任务出队失败: {e}")
            return None

    def get_queue_size(self) -> int:
        """获取队列大小"""
        try:
            if self.redis_client:
                return self.redis_client.zcard(self.queue_name)
            else:
                return len(self._memory_queue)
        except Exception as e:
            logger.error(f"获取队列大小失败: {e}")
            return 0

    def clear(self) -> bool:
        """清空队列"""
        try:
            if self.redis_client:
                self.redis_client.delete(self.queue_name)
            else:
                self._memory_queue.clear()
            logger.info("队列已清空")
            return True
        except Exception as e:
            logger.error(f"清空队列失败: {e}")
            return False


class TaskWorker:
    """任务工作器"""

    def __init__(
        self,
        task_queue: TaskQueue,
        task_handlers: dict[str, Callable],
    ):
        self.task_queue = task_queue
        self.task_handlers = task_handlers
        self.is_running = False

    def register_handler(self, task_name: str, handler: Callable) -> None:
        """注册任务处理器"""
        self.task_handlers[task_name] = handler
        logger.info(f"已注册任务处理器: {task_name}")

    def start(self) -> None:
        """启动工作器"""
        self.is_running = True
        logger.info("任务工作器已启动")

        while self.is_running:
            task = self.task_queue.dequeue()
            if task:
                self._process_task(task)
            else:
                import time
                time.sleep(1)  # 没有任务时休眠

    def stop(self) -> None:
        """停止工作器"""
        self.is_running = False
        logger.info("任务工作器已停止")

    def _process_task(self, task: dict[str, Any]) -> None:
        """处理任务"""
        task_name = task["task_name"]
        task_data = task["task_data"]

        logger.info(f"开始处理任务: {task_name}")

        try:
            handler = self.task_handlers.get(task_name)
            if not handler:
                logger.error(f"未找到任务处理器: {task_name}")
                return

            # 执行任务
            result = handler(**task_data)
            logger.info(f"任务处理成功: {task_name}")
            return result
        except Exception as e:
            logger.error(f"任务处理失败: {task_name}, 错误: {e}", exc_info=True)
            return None
