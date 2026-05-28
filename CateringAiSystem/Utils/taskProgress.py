"""内存任务进度跟踪

用于耗时操作的进度查询，任务数据存储在内存中，服务重启后丢失。
"""
import threading
import time
import uuid
from typing import Optional


class TaskProgress:
    """后台任务进度跟踪"""
    _tasks: dict = {}
    _lock = threading.Lock()

    @classmethod
    def create(cls, description: str) -> str:
        """创建任务，返回 task_id"""
        task_id = uuid.uuid4().hex[:12]
        with cls._lock:
            cls._tasks[task_id] = {
                "id": task_id,
                "status": "pending",
                "progress": 0,
                "description": description,
                "message": "等待执行",
                "created_at": time.time(),
                "result": None,
                "error": None,
            }
        return task_id

    @classmethod
    def update(cls, task_id: str, *, progress: int = None, message: str = None, status: str = None):
        """更新任务进度"""
        with cls._lock:
            task = cls._tasks.get(task_id)
            if task:
                if progress is not None:
                    task["progress"] = max(0, min(100, progress))
                if message is not None:
                    task["message"] = message
                if status is not None:
                    task["status"] = status

    @classmethod
    def get(cls, task_id: str) -> Optional[dict]:
        """查询任务状态"""
        with cls._lock:
            task = cls._tasks.get(task_id)
            if task:
                info = dict(task)
                info["elapsed"] = round(time.time() - task["created_at"], 1)
                return info
            return None

    @classmethod
    def complete(cls, task_id: str, result: dict = None):
        """标记任务完成"""
        with cls._lock:
            task = cls._tasks.get(task_id)
            if task:
                task["status"] = "completed"
                task["progress"] = 100
                task["message"] = "完成"
                task["result"] = result

    @classmethod
    def fail(cls, task_id: str, error: str):
        """标记任务失败"""
        with cls._lock:
            task = cls._tasks.get(task_id)
            if task:
                task["status"] = "failed"
                task["error"] = error
                task["message"] = error

    @classmethod
    def cleanup(cls, task_id: str):
        """清理任务数据"""
        with cls._lock:
            cls._tasks.pop(task_id, None)

    @classmethod
    def cleanup_old(cls, max_age: int = 3600):
        """清理超过 max_age 秒的已完成/失败任务"""
        now = time.time()
        with cls._lock:
            expired = [
                tid for tid, t in cls._tasks.items()
                if t["status"] in ("completed", "failed") and now - t["created_at"] > max_age
            ]
            for tid in expired:
                cls._tasks.pop(tid, None)
