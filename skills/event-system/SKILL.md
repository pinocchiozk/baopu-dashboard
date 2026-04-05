# Event System Skill

基于 claw-code 的 lane_events.rs 设计，事件驱动的通知系统。

## 核心概念

claw-code 的理念：**事件 > 日志**

```
事件流:
  lane.started → lane.running → lane.green/lane.red → lane.finished
                     ↓
              lane.blocked (with failure_class)
```

## 事件命名规范

```
{domain}.{entity}.{action}

示例:
  agent.subagent.spawned
  agent.subagent.completed
  agent.subagent.failed
  heartbeat.sentiment.collected
  heartbeat.kline.updated
  market.alert.triggered
  portfolio.stock.breakstop
```

## 事件结构

```typescript
interface AgentEvent {
  event: string;           // 事件名
  status: 'running' | 'ready' | 'blocked' | 'completed' | 'failed';
  emitted_at: string;       // ISO 时间
  failure_class?: string;   // 失败分类（可选）
  detail?: string;          // 详情（可选）
  data?: object;            // 额外数据（可选）
}
```

## 失败分类（FailureClass）

| 分类 | 说明 |
|------|------|
| `prompt_delivery` | 消息发送失败 |
| `trust_gate` | 权限问题 |
| `branch_divergence` | 分支冲突 |
| `timeout` | 执行超时 |
| `test_failure` | 测试失败 |
| `provider_error` | API/模型错误 |
| `infra_error` | 基础设施错误 |

## 事件发射器

```javascript
class EventEmitter {
  constructor() {
    this.listeners = new Map();
  }
  
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }
  
  off(event, callback) {
    if (!this.listeners.has(event)) return;
    const callbacks = this.listeners.get(event);
    const index = callbacks.indexOf(callback);
    if (index > -1) callbacks.splice(index, 1);
  }
  
  emit(event, data) {
    if (!this.listeners.has(event)) return;
    this.listeners.get(event).forEach(cb => cb(data));
  }
}

const globalEmitter = new EventEmitter();
```

## 事件到飞书推送的映射

```javascript
const EVENT_TO_FEISHU_TEMPLATE = {
  'agent.subagent.completed': {
    title: '✅ Agent 完成',
    template: '{subagent_id} 已完成\n耗时: {duration}秒'
  },
  'agent.subagent.failed': {
    title: '❌ Agent 失败',
    template: '{subagent_id} 失败\n错误: {error}\n建议: {action}'
  },
  'portfolio.stock.breakstop': {
    title: '🚨 止损警报',
    template: '{stock} 跌破 {stop_price}\n当前: {current_price}\n操作: {action}'
  },
  'heartbeat.kline.updated': {
    title: '📊 K线更新',
    template: '情绪K线已更新\n{date}'
  }
};

function handleEvent(event) {
  const mapping = EVENT_TO_FEISHU_TEMPLATE[event.event];
  if (!mapping) return;
  
  const message = fillTemplate(mapping.template, event);
  sendFeishuMessage({
    title: mapping.title,
    content: message
  });
}
```

## Subagent 事件追踪

```javascript
function trackSubagentEvents(subagentId, events) {
  const timeline = [];
  
  for (const event of events) {
    timeline.push({
      event: event.kind,        // spawned, running, blocked, completed, failed
      status: event.status,
      detail: event.detail,
      timestamp: event.timestamp
    });
    
    // 实时推送到飞书（仅关键事件）
    if (['blocked', 'failed', 'completed'].includes(event.kind)) {
      handleEvent({
        event: `agent.subagent.${event.kind}`,
        status: event.status,
        emitted_at: event.timestamp,
        detail: event.detail,
        data: { subagent_id: subagentId }
      });
    }
  }
  
  return timeline;
}
```

## 使用示例

```javascript
// 1. 在 subagent 启动时
globalEmitter.emit('agent.subagent.spawned', {
  event: 'agent.subagent.spawned',
  status: 'running',
  emitted_at: new Date().toISOString(),
  data: { subagent_id: 'macro-analyst', task: '宏观分析' }
});

// 2. subagent 完成时
globalEmitter.emit('agent.subagent.completed', {
  event: 'agent.subagent.completed',
  status: 'completed',
  emitted_at: new Date().toISOString(),
  data: { subagent_id: 'macro-analyst', duration: 180 }
});

// 3. subagent 失败时（触发自动重试逻辑）
globalEmitter.emit('agent.subagent.failed', {
  event: 'agent.subagent.failed',
  status: 'failed',
  emitted_at: new Date().toISOString(),
  failure_class: 'timeout',
  detail: 'subagent 执行超时',
  data: { subagent_id: 'macro-analyst', error: 'timeout after 300s' }
});
```

## 来源

claw-code/rust/crates/runtime/src/lane_events.rs 的事件系统设计
