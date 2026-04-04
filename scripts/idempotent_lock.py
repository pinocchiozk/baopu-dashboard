#!/usr/bin/env python3
"""
幂等锁机制
防止重复调用API，节省token，避免副作用

原理：
- 用文件的 mtime 作为时间戳
- 任务开始时记录开始时间
- 任务完成后删除记录
- 下次检查：如果文件存在且时间在阈值内，跳过
"""

import os
import time
from pathlib import Path

LOCK_DIR = "/tmp/kaipanla/locks"
Path(LOCK_DIR).mkdir(parents=True, exist_ok=True)


def acquire_lock(lock_name: str, timeout_seconds: int = 300) -> bool:
    """
    获取幂等锁
    
    Args:
        lock_name: 锁名称（任务标识）
        timeout_seconds: 锁超时时间（防止死锁）
    
    Returns:
        True: 获取锁成功，可以执行任务
        False: 已有任务在执行，跳过
    """
    lock_file = os.path.join(LOCK_DIR, f"{lock_name}.lock")
    
    # 检查锁是否存在
    if os.path.exists(lock_file):
        # 检查是否超时
        mtime = os.path.getmtime(lock_file)
        if time.time() - mtime < timeout_seconds:
            # 锁有效期内，不重复执行
            return False
        else:
            # 锁已超时，删除旧锁
            os.remove(lock_file)
    
    # 创建锁文件
    Path(lock_file).touch()
    return True


def release_lock(lock_name: str):
    """释放锁"""
    lock_file = os.path.join(LOCK_DIR, f"{lock_name}.lock")
    if os.path.exists(lock_file):
        os.remove(lock_file)


def is_locked(lock_name: str) -> bool:
    """检查是否被锁定"""
    lock_file = os.path.join(LOCK_DIR, f"{lock_name}.lock")
    return os.path.exists(lock_file)


# ==================== 示例用法 ====================

if __name__ == "__main__":
    # 示例：情绪采集幂等锁
    lock_name = "sentiment_collection"
    
    if acquire_lock(lock_name, timeout_seconds=600):
        print("获取锁成功，执行任务...")
        # TODO: 执行实际任务
        # ... 采集逻辑 ...
        print("任务完成，释放锁")
        release_lock(lock_name)
    else:
        print("任务已在执行中，跳过本次")
