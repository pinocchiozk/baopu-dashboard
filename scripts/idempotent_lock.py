#!/usr/bin/env python3
"""
幂等锁机制 V2 (claw-code 风格)
基于 claw-code 的 recovery_recipes.rs 设计

增强功能：
1. 状态机：跟踪任务执行状态
2. 自动重试：失败后自动重试一次
3. 事件系统：状态变化时触发事件
4. 熔断器：连续失败N次后暂时跳过
"""

import os
import sys
import time
import json
import traceback
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Callable, Optional, Any
from dataclasses import dataclass, asdict, field

LOCK_DIR = "/tmp/kaipanla/locks"
EVENT_LOG_DIR = "/tmp/kaipanla/events"
Path(LOCK_DIR).mkdir(parents=True, exist_ok=True)
Path(EVENT_LOG_DIR).mkdir(parents=True, exist_ok=True)


class TaskStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CIRCUIT_OPEN = "circuit_open"


class FailureClass(Enum):
    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error"
    INFRA_ERROR = "infra_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


@dataclass
class TaskEvent:
    event_id: int
    task_name: str
    event: str
    status: str
    detail: Optional[str] = None
    failure_class: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        return asdict(self)


@dataclass
class TaskState:
    name: str
    status: TaskStatus
    attempts: int = 0
    consecutive_failures: int = 0
    last_error: Optional[str] = None
    last_error_class: Optional[FailureClass] = None
    last_success: Optional[str] = None
    events: list = field(default_factory=list)
    
    def to_dict(self):
        return {
            'name': self.name,
            'status': self.status.value,
            'attempts': self.attempts,
            'consecutive_failures': self.consecutive_failures,
            'last_error': self.last_error,
            'failure_class': self.last_error_class.value if self.last_error_class else None,
            'last_success': self.last_success,
            'events': [e.to_dict() for e in self.events]
        }


class EventLogger:
    """事件日志器"""
    
    def __init__(self):
        self.counter = 0
        
    def emit(self, task_name: str, event: str, status: TaskStatus, 
             detail: Optional[str] = None, 
             failure_class: Optional[FailureClass] = None) -> TaskEvent:
        self.counter += 1
        ev = TaskEvent(
            event_id=self.counter,
            task_name=task_name,
            event=event,
            status=status.value,
            detail=detail,
            failure_class=failure_class.value if failure_class else None
        )
        
        # 保存到事件日志
        event_file = os.path.join(EVENT_LOG_DIR, f"{task_name}_events.jsonl")
        with open(event_file, 'a') as f:
            f.write(json.dumps(ev.to_dict(), ensure_ascii=False) + '\n')
        
        return ev


class CircuitBreaker:
    """熔断器 - 连续失败后暂时跳过"""
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def is_open(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "HALF_OPEN"
                return False
            return True
        return False
    
    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"
        
    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"


class TaskRunner:
    """任务运行器 - 带状态追踪、自动重试、熔断器"""
    
    def __init__(self, task_name: str):
        self.task_name = task_name
        self.state = TaskState(name=task_name, status=TaskStatus.IDLE)
        self.event_logger = EventLogger()
        self.circuit_breaker = CircuitBreaker()
        
    def emit(self, event: str, status: TaskStatus, 
             detail: Optional[str] = None,
             failure_class: Optional[FailureClass] = None):
        """发射事件"""
        ev = self.event_logger.emit(
            self.task_name, event, status, detail, failure_class
        )
        self.state.events.append(ev)
        self.state.status = status
        print(f"[{self.task_name}] {event}: {status.value} {detail or ''}")
        
    def run_with_lock(self, fn: Callable, 
                     lock_timeout: int = 300,
                     max_retries: int = 1,
                     retry_delay: float = 5.0) -> bool:
        """
        运行任务（带幂等锁 + 自动重试 + 熔断器）
        
        Args:
            fn: 要执行的任务函数
            lock_timeout: 锁超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
            
        Returns:
            True: 任务成功
            False: 任务失败
        """
        # 检查熔断器
        if self.circuit_breaker.is_open():
            self.emit("circuit_open", TaskStatus.CIRCUIT_OPEN, 
                     f"熔断器开启，跳过本次执行")
            return False
        
        # 获取锁
        lock_file = os.path.join(LOCK_DIR, f"{self.task_name}.lock")
        
        if os.path.exists(lock_file):
            mtime = os.path.getmtime(lock_file)
            if time.time() - mtime < lock_timeout:
                self.emit("lock_blocked", TaskStatus.IDLE, "锁文件存在，任务正在执行")
                return False
            else:
                os.remove(lock_file)
        
        # 创建锁文件
        Path(lock_file).touch()
        self.state.attempts = 0
        
        try:
            self.emit("task_started", TaskStatus.RUNNING, "任务开始执行")
            
            for attempt in range(max_retries + 1):
                self.state.attempts = attempt + 1
                
                try:
                    if attempt > 0:
                        self.emit("task_retry", TaskStatus.RETRYING, 
                                f"第{attempt}次重试")
                        time.sleep(retry_delay * attempt)  # 指数退避
                    
                    result = fn()
                    
                    # 成功
                    self.state.consecutive_failures = 0
                    self.circuit_breaker.record_success()
                    self.state.last_success = datetime.now().isoformat()
                    self.emit("task_completed", TaskStatus.COMPLETED, 
                             f"尝试{attempt + 1}次后成功")
                    return True
                    
                except Exception as e:
                    self.state.last_error = str(e)
                    self.state.last_error_class = self._classify_error(e)
                    self.emit("task_error", TaskStatus.FAILED, 
                             f"{type(e).__name__}: {str(e)}",
                             self.state.last_error_class)
                    
                    # 判断是否可重试
                    if not self._is_retryable(e) or attempt >= max_retries:
                        break
                    
            # 最终失败
            self.state.consecutive_failures += 1
            self.circuit_breaker.record_failure()
            self.emit("task_failed", TaskStatus.FAILED, 
                     f"连续失败{self.state.consecutive_failures}次")
            return False
            
        finally:
            # 释放锁
            if os.path.exists(lock_file):
                os.remove(lock_file)
    
    def _classify_error(self, error: Exception) -> FailureClass:
        """错误分类"""
        error_str = str(error).lower()
        
        if any(x in error_str for x in ['timeout', 'timed out']):
            return FailureClass.TIMEOUT
        elif any(x in error_str for x in ['connection', 'network', 'dns', 'econnrefused']):
            return FailureClass.NETWORK_ERROR
        elif any(x in error_str for x in ['api', 'provider', 'model']):
            return FailureClass.PROVIDER_ERROR
        elif any(x in error_str for x in ['permission', 'denied', 'auth']):
            return FailureClass.INFRA_ERROR
        else:
            return FailureClass.UNKNOWN
    
    def _is_retryable(self, error: Exception) -> bool:
        """判断错误是否可重试"""
        # 网络错误、超时可重试
        # 权限错误、逻辑错误不可重试
        unretryable = ['permission', 'denied', 'auth', 'invalid']
        error_str = str(error).lower()
        return not any(x in error_str for x in unretryable)
    
    def get_state(self) -> dict:
        """获取任务状态"""
        return self.state.to_dict()


def run_task(task_name: str, fn: Callable, 
             lock_timeout: int = 300,
             max_retries: int = 1) -> bool:
    """快捷函数：运行单个任务"""
    runner = TaskRunner(task_name)
    return runner.run_with_lock(fn, lock_timeout, max_retries)


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 示例1: 基本用法
    def my_task():
        print("执行任务中...")
        # import random
        # if random.random() < 0.5:
        #     raise TimeoutError("模拟超时")
        return True
    
    success = run_task(
        "test_task",           # 任务名
        my_task,              # 任务函数
        lock_timeout=300,     # 锁超时（秒）
        max_retries=1         # 最多重试1次
    )
    print(f"任务结果: {'成功' if success else '失败'}")
    
    # 示例2: 获取任务状态
    runner = TaskRunner("test_task")
    print(json.dumps(runner.get_state(), indent=2, ensure_ascii=False))
