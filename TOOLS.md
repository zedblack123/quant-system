# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## 🤖 模型使用规则

### 任务类型与模型选择

| 任务类型 | 优先模型 | 说明 |
|----------|----------|------|
| **选股** | DeepSeek | 股票筛选、量化分析 |
| **策略分析** | DeepSeek | 投资策略、周期研判 |
| **推理分析** | DeepSeek | 市场推理、逻辑分析 |
| **代码编写** | DeepSeek | Python/量化策略开发 |
| **日常对话** | MiniMax | 闲聊、常规问答 |
| **信息推送** | MiniMax | 定时报告、舆情推送 |
| **飞书操作** | MiniMax | 消息发送、文档操作 |

### 模型别名
- **DeepSeek**: `deepseek/deepseek-chat`
- **MiniMax**: `minimax-portal/MiniMax-M2.7`

### 使用方式
- 使用 `sessions_spawn` 创建子agent时，通过 `model` 参数指定
- 主会话默认使用 MiniMax，但会自动识别任务类型切换

### 触发 DeepSeek 的关键词
- "选股"、"筛选"、"量化"
- "策略"、"战法"、"分析"
- "推理"、"判断"、"预判"
- "代码"、"Python"、"编程"
- "回测"、"数据处理"

---

Add whatever helps you do your job. This is your cheat sheet.
