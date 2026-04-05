# HEARTBEAT.md - 定时检查任务

## 🔒 幂等锁机制

所有定时任务使用幂等锁防止重复执行：
- 锁文件目录：`/tmp/kaipanla/locks/`
- 锁超时：300-600秒（防止死锁）
- 获取锁成功才执行，失败则跳过

---

## 📊 A 股市场情绪监控（交易时段）

**执行时间：** 交易日 9:15-11:30、13:00-15:00，每 5 分钟检查一次

**幂等锁：** `sentiment_collection`（超时600秒）

**采集时间点：**
- 9:15（竞价开盘）
- 9:20、9:25、9:30...11:30（上午）
- 13:00...14:55、15:00（下午）

**检查逻辑：**
1. 当前时间是否在交易时段？
2. 距离上次采集是否≥30分钟？
3. **获取幂等锁是否成功？**
4. 如果是 → 执行采集脚本
5. 如果否 → 跳过

---

## 📈 情绪 K 线图自动更新

**执行时间：** 每天 15:05（收盘后5分钟）

**幂等锁：** `kline_update`（超时300秒）

---

## ⚠️ 幂等锁原理

```
任务触发
    ↓
检查锁文件是否存在
    ↓
是 → 检查是否超时
    ↓ ↓
  是（超时）  否（在有效期内）
    ↓         ↓
  删除旧锁   跳过本次
    ↓
创建新锁
    ↓
执行任务
    ↓
删除锁文件
```

**好处：**
- 避免重复调用API（省token）
- 避免副作用（如重复写入数据库）
- 防止死锁（超时自动释放）

---

## 🗑️ 截图定期清理

**执行时间：** 每周五收盘后（或每月最后一个交易日）

**清理规则：**
- `screenshots/emotion-kline/`：数据提取完成后，保留最近7天
- `screenshots/comprehensive/`：数据提取完成后，保留最近7天
- `screenshots/others/`：数据提取完成后，保留最近3天

**幂等锁：** `screenshots_cleanup`（超时120秒）

**操作：**
```bash
# 清理7天前的截图
find /workspace/screenshots/emotion-kline -name "*.png" -mtime +7 -delete
find /workspace/screenshots/comprehensive -name "*.png" -mtime +7 -delete
find /workspace/screenshots/others -name "*.png" -mtime +3 -delete
```

---

## 🔄 自动重试机制（claw-code 风格）

基于 claw-code 的 recovery_recipes.rs 设计：

> "known failure → auto-heal once → then escalate"

**核心原则：失败后先自动恢复一次，再上报**

### 重试食谱

| 任务 | 重试次数 | 恢复动作 |
|------|---------|---------|
| sentiment_collection | 1次 | 等待30秒后重试 |
| kline_update | 1次 | 等待1分钟后重试 |
| screenshots_cleanup | 0次 | 直接跳过（不关键） |
| feishu_push | 2次 | 指数退避重试 |

### 实现代码模板

```javascript
async function executeWithAutoRetry(taskName, fn, options = {}) {
  const recipes = {
    'sentiment_collection': { retries: 1, delay: 30000 },
    'kline_update': { retries: 1, delay: 60000 },
    'feishu_push': { retries: 2, delay: 5000 },
  };
  
  const recipe = recipes[taskName] || { retries: 0, delay: 0 };
  let lastError;
  
  for (let attempt = 0; attempt <= recipe.retries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (attempt < recipe.retries) {
        console.log(`[${taskName}] 第${attempt + 1}次失败，${recipe.delay}ms后重试...`);
        await new Promise(r => setTimeout(r, recipe.delay));
      }
    }
  }
  
  // 所有重试都失败，上报
  emitEvent({
    event: `heartbeat.${taskName}.failed`,
    status: 'failed',
    failure_class: 'timeout',
    detail: lastError.message
  });
  throw lastError;
}
```

### 熔断器（可选）

连续失败5次后，熔断60秒不再尝试。

---

## 📡 事件系统（claw-code 风格）

基于 claw-code 的 lane_events.rs 设计：

> "events over scraped prose"

### 事件命名规范

```
{domain}.{entity}.{action}

示例：
  agent.subagent.spawned
  agent.subagent.completed
  heartbeat.sentiment.collected
  market.alert.breakstop
```

### 关键事件（触发飞书推送）

| 事件 | 触发条件 | 推送内容 |
|------|---------|---------|
| `agent.subagent.failed` | subagent失败 | 错误详情 + 建议 |
| `market.alert.breakstop` | 股票跌破止损 | 股票名 + 止损价 + 当前价 |
| `heartbeat.kline.updated` | K线更新 | 更新完成 |

---

*最后更新：2026-04-05（加入自动重试+事件系统）*
