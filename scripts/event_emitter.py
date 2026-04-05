#!/usr/bin/env python3
"""
事件系统 (claw-code 风格)
基于 claw-code 的 lane_events.rs 设计

事件 > 日志

核心概念：
- 所有状态变化都是事件
- 事件可以触发通知（飞书）
- 事件存储用于追踪
"""

import os
import json
import time
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict, field
from typing import Optional, Callable, Dict, List
from pathlib import Path


EVENT_LOG_DIR = "/tmp/kaipanla/events"
Path(EVENT_LOG_DIR).mkdir(parents=True, exist_ok=True)


class EventName(Enum):
    """事件名（基于 claw-code lane_events）"""
    # Agent 事件
    AGENT_SPAWNED = "agent.subagent.spawned"
    AGENT_STARTED = "agent.subagent.started"
    AGENT_BLOCKED = "agent.subagent.blocked"
    AGENT_COMPLETED = "agent.subagent.completed"
    AGENT_FAILED = "agent.subagent.failed"
    
    # 心跳事件
    HEARTBEAT_STARTED = "heartbeat.started"
    HEARTBEAT_COMPLETED = "heartbeat.completed"
    HEARTBEAT_FAILED = "heartbeat.failed"
    
    # 市场事件
    MARKET_ALERT = "market.alert.triggered"
    STOCK_BREAKSTOP = "portfolio.stock.breakstop"
    
    # 系统事件
    SYSTEM_ERROR = "system.error"
    SYSTEM_CIRCUIT_OPEN = "system.circuit_open"


class EventStatus(Enum):
    RUNNING = "running"
    READY = "ready"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class FailureClass(Enum):
    """失败分类"""
    PROMPT_DELIVERY = "prompt_delivery"
    TRUST_GATE = "trust_gate"
    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error"
    INFRA_ERROR = "infra_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


@dataclass
class AgentEvent:
    """事件结构（兼容 claw-code 的 LaneEvent）"""
    event: str
    status: str
    emitted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    failure_class: Optional[str] = None
    detail: Optional[str] = None
    data: Optional[dict] = None
    
    def to_dict(self):
        return asdict(self)


class EventEmitter:
    """事件发射器"""
    
    # 类级别订阅者
    _subscribers: Dict[str, List[Callable]] = {}
    
    def __init__(self, component: str = "system"):
        self.component = component
        self.events: List[AgentEvent] = []
        
    @classmethod
    def subscribe(cls, event_pattern: str, callback: Callable):
        """订阅事件（支持通配符）"""
        if event_pattern not in cls._subscribers:
            cls._subscribers[event_pattern] = []
        cls._subscribers[event_pattern].append(callback)
    
    @classmethod
    def unsubscribe(cls, event_pattern: str, callback: Callable):
        """取消订阅"""
        if event_pattern in cls._subscribers:
            cls._subscribers[event_pattern].remove(callback)
    
    def emit(self, event_name: str, status: EventStatus,
             detail: Optional[str] = None,
             failure_class: Optional[FailureClass] = None,
             data: Optional[dict] = None) -> AgentEvent:
        """发射事件"""
        event = AgentEvent(
            event=f"{self.component}.{event_name}",
            status=status.value,
            detail=detail,
            failure_class=failure_class.value if failure_class else None,
            data=data
        )
        
        self.events.append(event)
        
        # 保存到事件日志
        self._save_event(event)
        
        # 通知订阅者
        self._notify_subscribers(event)
        
        return event
    
    def _save_event(self, event: AgentEvent):
        """保存事件到文件"""
        event_file = os.path.join(EVENT_LOG_DIR, f"{self.component}_events.jsonl")
        with open(event_file, 'a') as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + '\n')
    
    def _notify_subscribers(self, event: AgentEvent):
        """通知订阅者"""
        for pattern, callbacks in self._subscribers.items():
            if self._match_event(event.event, pattern):
                for callback in callbacks:
                    try:
                        callback(event)
                    except Exception as e:
                        print(f"[EventEmitter] 订阅者执行错误: {e}")
    
    def _match_event(self, event_name: str, pattern: str) -> bool:
        """匹配事件（支持 * 通配符）"""
        if pattern == "*":
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return event_name.startswith(prefix + ".")
        return event_name == pattern
    
    def get_recent_events(self, limit: int = 10) -> List[AgentEvent]:
        """获取最近的事件"""
        return self.events[-limit:]


class FeishuNotifier:
    """飞书通知器"""
    
    def __init__(self):
        self.enabled = False  # 需要配置后才启用
        
    def notify(self, event: AgentEvent):
        """发送飞书通知"""
        if not self.enabled:
            return
        
        # 根据事件类型构造消息
        message = self._format_message(event)
        if message:
            self._send_to_feishu(message)
    
    def _format_message(self, event: AgentEvent) -> Optional[str]:
        """格式化消息"""
        templates = {
            "agent.subagent.completed": "✅ Agent 完成\n{detail}",
            "agent.subagent.failed": "❌ Agent 失败\n{detail}\n分类: {failure_class}",
            "portfolio.stock.breakstop": "🚨 止损警报\n股票: {stock}\n当前价: {price}\n止损价: {stop_price}",
            "system.circuit_open": "⚠️ 熔断器开启\n任务: {task}\n连续失败: {failures}",
        }
        
        template = templates.get(event.event)
        if not template:
            return None
        
        data = event.data or {}
        detail = event.detail or ""
        failure_class = event.failure_class or ""
        
        message = template.format(
            detail=detail,
            failure_class=failure_class,
            stock=data.get("stock", ""),
            price=data.get("price", ""),
            stop_price=data.get("stop_price", ""),
            task=data.get("task", ""),
            failures=data.get("failures", "")
        )
        
        return message
    
    def _send_to_feishu(self, message: str):
        """发送飞书消息（需要配置 webhook）"""
        # TODO: 实现飞书 webhook 发送
        print(f"[FeishuNotifier] 发送通知: {message}")


# 全局通知器
feishu_notifier = FeishuNotifier()


# 事件订阅：重要事件自动飞书通知
def on_important_event(event: AgentEvent):
    """重要事件自动飞书通知"""
    important_events = [
        "agent.subagent.failed",
        "portfolio.stock.breakstop",
        "system.circuit_open",
        "heartbeat.failed"
    ]
    
    if event.event in important_events:
        feishu_notifier.notify(event)


EventEmitter.subscribe("*", on_important_event)


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 创建事件发射器
    emitter = EventEmitter("test")
    
    # 发射事件
    emitter.emit(
        "subagent.spawned",
        EventStatus.RUNNING,
        detail="开始执行任务"
    )
    
    emitter.emit(
        "subagent.completed",
        EventStatus.COMPLETED,
        detail="任务执行完成"
    )
    
    emitter.emit(
        "subagent.failed",
        EventStatus.FAILED,
        detail="连接超时",
        failure_class=FailureClass.NETWORK_ERROR
    )
    
    # 打印最近事件
    print("\n最近事件:")
    for event in emitter.get_recent_events():
        print(f"  {event.event}: {event.status} ({event.detail})")
