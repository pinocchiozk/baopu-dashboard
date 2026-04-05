# Subagent State Machine Skill

跟踪 subagent 的生命周期状态，基于 claw-code 的 worker_boot.rs 设计。

## 状态定义

```
subagent lifecycle:
  spawning → ready → running → completed / failed
                 ↓
            blocked (trust/delay)
```

| 状态 | 说明 |
|------|------|
| `spawning` | Subagent 创建中 |
| `ready` | 等待任务 |
| `running` | 执行中 |
| `blocked` | 被阻塞（等待外部条件） |
| `completed` | 成功完成 |
| `failed` | 失败 |

## 失败分类

| 分类 | 说明 |
|------|------|
| `trust_gate` | 权限/信任问题 |
| `prompt_delivery` | 消息发送失败 |
| `timeout` | 执行超时 |
| `provider_error` | 模型/服务提供商错误 |
| `infra` | 基础设施错误 |

## 事件日志

每次状态转换记录事件：
```json
{
  "event_id": 1,
  "subagent_id": "macro-analyst",
  "kind": "spawned",
  "status": "ready",
  "detail": "subagent spawned",
  "timestamp": "2026-04-05T13:25:00Z"
}
```

## 使用方法

在 spawn subagent 时记录状态：

```javascript
// 状态跟踪示例
const subagentStates = {
  'macro-analyst': {
    status: 'spawning',
    startedAt: Date.now(),
    events: []
  }
};

function emitEvent(subagentId, kind, detail) {
  subagentStates[subagentId].events.push({
    event_id: subagentStates[subagentId].events.length + 1,
    subagent_id: subagentId,
    kind,
    status: subagentStates[subagentId].status,
    detail,
    timestamp: new Date().toISOString()
  });
}
```

## 状态查询

可用 sessions_list 查看 subagent 状态：

```javascript
// 查询当前活跃的 subagent
const active = sessions_list({ activeMinutes: 30 });
```

## 恢复建议

| 状态 | 自动恢复动作 |
|------|------------|
| `trust_gate` | 自动解析信任 |
| `prompt_delivery` | 重发消息 |
| `timeout` | 重试一次 |
| `provider_error` | 等待后重试 |
| `infra` | escalate（上报） |

## 来源

claw-code/rust/crates/runtime/src/worker_boot.rs 的 Python 版本
