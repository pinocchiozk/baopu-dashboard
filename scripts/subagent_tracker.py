#!/usr/bin/env python3
"""
Subagent 状态追踪器 (claw-code 风格)
基于 claw-code 的 worker_boot.rs 设计

状态机：
  spawning → ready → running → completed / failed
                         ↓
                    blocked (trust/delay)
"""

import os
import json
import time
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict
from pathlib import Path


STATE_DIR = "/tmp/kaipanla/subagent_states"
Path(STATE_DIR).mkdir(parents=True, exist_ok=True)


class SubagentStatus(Enum):
    SPAWNING = "spawning"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class FailureKind(Enum):
    TRUST_GATE = "trust_gate"
    PROMPT_DELIVERY = "prompt_delivery"
    TIMEOUT = "timeout"
    PROVIDER = "provider"
    UNKNOWN = "unknown"


@dataclass
class SubagentEvent:
    seq: int
    kind: str
    status: str
    detail: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SubagentState:
    subagent_id: str
    task_name: str
    status: SubagentStatus
    trust_auto_resolve: bool = False
    trust_gate_cleared: bool = False
    prompt_delivery_attempts: int = 0
    prompt_in_flight: bool = False
    last_error: Optional[str] = None
    last_error_kind: Optional[FailureKind] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    events: List[SubagentEvent] = field(default_factory=list)
    
    def to_dict(self):
        return {
            'subagent_id': self.subagent_id,
            'task_name': self.task_name,
            'status': self.status.value,
            'trust_auto_resolve': self.trust_auto_resolve,
            'trust_gate_cleared': self.trust_gate_cleared,
            'prompt_delivery_attempts': self.prompt_delivery_attempts,
            'prompt_in_flight': self.prompt_in_flight,
            'last_error': self.last_error,
            'last_error_kind': self.last_error_kind.value if self.last_error_kind else None,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'events': [asdict(e) for e in self.events]
        }


class SubagentTracker:
    """Subagent 状态追踪器"""
    
    def __init__(self):
        self.states: Dict[str, SubagentState] = {}
        self.counter = 0
        
    def create(self, subagent_id: str, task_name: str,
               trust_auto_resolve: bool = False) -> SubagentState:
        """创建新的 subagent 追踪"""
        self.counter += 1
        
        state = SubagentState(
            subagent_id=subagent_id,
            task_name=task_name,
            status=SubagentStatus.SPAWNING,
            trust_auto_resolve=trust_auto_resolve
        )
        
        self._push_event(state, "spawned", SubagentStatus.SPAWNING, 
                        f"subagent {subagent_id} created for task {task_name}")
        
        self.states[subagent_id] = state
        self._save_state(state)
        
        return state
    
    def transition(self, subagent_id: str, new_status: SubagentStatus,
                  detail: Optional[str] = None,
                  error: Optional[str] = None,
                  error_kind: Optional[FailureKind] = None):
        """状态转换"""
        if subagent_id not in self.states:
            return
        
        state = self.states[subagent_id]
        old_status = state.status
        
        state.status = new_status
        state.updated_at = datetime.now().isoformat()
        
        if error:
            state.last_error = error
            state.last_error_kind = error_kind
        
        # 状态转换事件
        event_map = {
            (SubagentStatus.SPAWNING, SubagentStatus.READY): "ready",
            (SubagentStatus.READY, SubagentStatus.RUNNING): "running",
            (SubagentStatus.RUNNING, SubagentStatus.COMPLETED): "completed",
            (SubagentStatus.RUNNING, SubagentStatus.FAILED): "failed",
            (SubagentStatus.RUNNING, SubagentStatus.BLOCKED): "blocked",
        }
        
        event_kind = event_map.get((old_status, new_status), "status_changed")
        
        self._push_event(state, event_kind, new_status, detail or f"transition to {new_status.value}")
        self._save_state(state)
    
    def set_running(self, subagent_id: str, prompt_in_flight: bool = True):
        """设置为运行中"""
        if subagent_id not in self.states:
            return
        
        state = self.states[subagent_id]
        state.status = SubagentStatus.RUNNING
        state.prompt_in_flight = prompt_in_flight
        state.updated_at = datetime.now().isoformat()
        
        self._push_event(state, "running", SubagentStatus.RUNNING, "task executing")
        self._save_state(state)
    
    def set_completed(self, subagent_id: str, detail: Optional[str] = None):
        """设置为完成"""
        self.transition(subagent_id, SubagentStatus.COMPLETED, 
                       detail or "task completed successfully")
    
    def set_failed(self, subagent_id: str, error: str,
                  error_kind: FailureKind = FailureKind.UNKNOWN):
        """设置为失败"""
        self.transition(subagent_id, SubagentStatus.FAILED,
                       error, error, error_kind)
    
    def increment_attempts(self, subagent_id: str):
        """增加发送尝试次数"""
        if subagent_id in self.states:
            self.states[subagent_id].prompt_delivery_attempts += 1
            self._save_state(self.states[subagent_id])
    
    def get_state(self, subagent_id: str) -> Optional[SubagentState]:
        """获取状态"""
        return self.states.get(subagent_id)
    
    def get_all_states(self) -> Dict[str, dict]:
        """获取所有状态"""
        return {k: v.to_dict() for k, v in self.states.items()}
    
    def _push_event(self, state: SubagentState, kind: str, 
                   status: SubagentStatus, detail: Optional[str] = None):
        """添加事件"""
        event = SubagentEvent(
            seq=len(state.events) + 1,
            kind=kind,
            status=status.value,
            detail=detail
        )
        state.events.append(event)
    
    def _save_state(self, state: SubagentState):
        """保存状态到文件"""
        state_file = os.path.join(STATE_DIR, f"{state.subagent_id}.json")
        with open(state_file, 'w') as f:
            json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)
    
    def load_state(self, subagent_id: str) -> Optional[SubagentState]:
        """从文件加载状态"""
        state_file = os.path.join(STATE_DIR, f"{subagent_id}.json")
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                data = json.load(f)
                state = SubagentState(
                    subagent_id=data['subagent_id'],
                    task_name=data['task_name'],
                    status=SubagentStatus(data['status']),
                    trust_auto_resolve=data.get('trust_auto_resolve', False),
                    trust_gate_cleared=data.get('trust_gate_cleared', False),
                    prompt_delivery_attempts=data.get('prompt_delivery_attempts', 0),
                    prompt_in_flight=data.get('prompt_in_flight', False),
                    last_error=data.get('last_error'),
                    last_error_kind=FailureKind(data['last_error_kind']) if data.get('last_error_kind') else None,
                    created_at=data.get('created_at', datetime.now().isoformat()),
                    updated_at=data.get('updated_at', datetime.now().isoformat()),
                    events=[SubagentEvent(**e) for e in data.get('events', [])]
                )
                self.states[subagent_id] = state
                return state
        return None
    
    def get_timeline(self, subagent_id: str) -> List[dict]:
        """获取事件时间线"""
        state = self.states.get(subagent_id)
        if not state:
            return []
        return [
            {
                'seq': e.seq,
                'event': e.kind,
                'status': e.status,
                'detail': e.detail,
                'timestamp': e.timestamp
            }
            for e in state.events
        ]


# 全局追踪器
global_tracker = SubagentTracker()


# ==================== 使用示例 ====================

if __name__ == "__main__":
    tracker = SubagentTracker()
    
    # 创建追踪
    tracker.create("macro-analyst", "宏观分析", trust_auto_resolve=True)
    print("创建 macro-analyst 追踪")
    
    # 状态转换
    tracker.transition("macro-analyst", SubagentStatus.READY, "等待任务")
    print("→ READY")
    
    tracker.set_running("macro-analyst")
    print("→ RUNNING")
    
    # 模拟执行...
    time.sleep(0.1)
    
    tracker.set_completed("macro-analyst", "分析完成")
    print("→ COMPLETED")
    
    # 打印时间线
    print("\n事件时间线:")
    for event in tracker.get_timeline("macro-analyst"):
        print(f"  [{event['seq']}] {event['event']}: {event['status']} - {event['detail']}")
    
    # 打印当前状态
    print("\n当前状态:")
    print(json.dumps(tracker.get_state("macro-analyst").to_dict(), indent=2, ensure_ascii=False))
