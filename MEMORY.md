# MEMORY.md - 长期记忆索引

*这是精简索引，详细内容在 memory/topics/*

---

## 📂 主题索引

| 主题 | 文件 |
|------|------|
| 投研体系 | memory/topics/trading-systems.md |
| 自我优化 | memory/topics/self-optimization.md |
| 投研Agent | memory/topics/research-agents.md |
| 并行研究 | memory/topics/parallel-research.md |
| Self-Check | memory/topics/self-check.md |

---

## 📅 每日日志

- memory/2026-04-04.md
- memory/2026-03-31.md
- memory/2026-03-28.md
- memory/2026-03-27.md

---

## 🔑 核心原则

**投资研究数据原则：**
- 数据必须来自真实来源
- 有工具（QVeris等）必须使用
- 无法获取数据时明确告知

---

## 📊 记忆系统（L2 分层）

- **L1：** MEMORY.md（长期记忆，精简版）
- **L2：** `memory/topics/*.md`（按需读取的专题档案）
- **L3：** sessions_history（原始对话记录）

**原则：** 每笔重要决策后更新对应 topic 文件；每周从日记录提炼至 MEMORY.md

---

## 📈 投研 Dashboard

- **部署地址：** https://x2qior3wl6vn.space.minimaxi.com
- **对应文件：** /workspace/docs/dashboard/index.html

---

## 🛡️ 安全机制

- **压缩攻击防御：** skills/prompt-hygiene/filter.js
- **预测日志：** memory/_prediction-log.md
- **错误模式：** memory/_mistake-patterns.md

---

## ⏳ 待执行任务

1. launchd定时任务加载（开盘啦采集）
2. 冰点ETF策略每日信号推送
3. 回测数据积累（需30天+）
4. Cron每周自动化记忆整理

---

## 🔧 技术栈

| 技术 | 状态 |
|------|------|
| QVeris API | ✅ 已配置 |
| 飞书推送 | ✅ 已配置 |
| 开盘啦采集 | 🔄 部分完成 |
| Cron定时任务 | ⏳ 待设置 |

---

*最后更新：2026-04-05*
