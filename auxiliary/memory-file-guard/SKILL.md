---
name: tools-memory-user-file-in
version: "1.0.0"
description: Memory & User 文件写入保护。Plugin 硬拦截 + Skill 工作流，写入前必须用户确认，写入后自动上锁并推送内容对比。自包含设计，跨 Agent/跨系统可移植。
triggers:
  - memory 写入被拦截
  - memory-file-guard block
  - 写入 memory
  - 写入 user
related_skills: []
---

# tools-memory-user-file-in：Memory & User 文件写入保护

## 概述

保护 Hermes 的 MEMORY.md 和 USER.md 两个持久记忆文件。当 Agent 尝试通过 memory 工具写入这两个文件时，Plugin 自动拦截，要求用户确认后才能继续。

设计原则：
- 自包含 — Plugin 源码打包在 bundled/plugins/ 内，Skill 复制到任何 Agent 即可使用
- 跨平台 — Plugin 纯 Python 标准库，macOS/Linux 通用
- 硬拦截 + 软引导 — Plugin 提供硬拦截，Skill 文档引导 Agent 完成确认流程

## 架构流程

Agent 想写 memory → 调用 memory 工具 → Plugin 拦截（pre_tool_call）→ 无标记文件 → block → Agent 加载 Skill → 读取当前内容 → clarify() 询问用户 → 用户确认 → 解锁文件 + 创建标记文件 → 重新调用 memory → Plugin 检测标记 → allow → 删除标记 → 写入成功 → 重新上锁 → 输出对比

两层保护：
1. Plugin 硬拦截 — 没有已确认标记文件，memory 工具调用直接被拒绝
2. 文件锁（可选）— 用户可额外对文件设置 uchg 或 chattr +i 锁

## 部署步骤

1. 确定 HERMES_HOME（default: ~/.hermes，子Agent: ~/.hermes/profiles/<name>）
2. 复制 Plugin：cp -r <skill>/bundled/plugins/memory-file-guard $HERMES_HOME/plugins/memory-file-guard
3. 启用 Plugin：config.yaml 中 plugins.enabled 添加 memory-file-guard
4. 重启：hermes gateway restart
5. 验证：查看 agent.log 中 "memory-file-guard plugin registered"

## 工作流（被拦截后）

当 memory 工具调用被拦截时，Agent 必须按以下步骤执行：

### 步骤 1：读取当前文件内容

```bash
MEMORY_FILE=$HERMES_HOME/memories/MEMORY.md
USER_FILE=$HERMES_HOME/memories/USER.md
```

用 read_file 读取目标文件当前内容。

### 步骤 2：询问用户确认

使用 clarify() 向用户展示：
- 动作：add / replace / remove
- 目标：memory 或 user
- 当前内容：文件现有内容
- 变更内容：即将写入的内容

### 步骤 3：处理用户回复

- 用户选"可以"/"确认" → 继续
- 用户选"取消"/"不" → 终止

### 步骤 4：解锁文件 + 创建标记

macOS:
```bash
chflags nouchg <文件路径>
xattr -cr <文件路径>
```

Linux:
```bash
chattr -i <文件路径>
```

创建标记（120秒TTL）：
```bash
touch /tmp/hermes-memory-guard-approved
```

### 步骤 5：重新调用 memory 工具

使用与被拦截时完全相同的参数，重新调用 memory 工具。Plugin 检测到标记后放行。

### 步骤 6：重新上锁

macOS:
```bash
chflags uchg <文件路径>
```

Linux:
```bash
chattr +i <文件路径>
```

### 步骤 7：输出内容对比

读取并推送完整的文件内容，同时展示新旧对比。

## 文件路径速查

| 文件 | default 路径 |
|------|-------------|
| MEMORY.md | ~/.hermes/memories/MEMORY.md |
| USER.md | ~/.hermes/memories/USER.md |

## 标记文件机制

| 属性 | 值 |
|------|---|
| 路径 | /tmp/hermes-memory-guard-approved |
| TTL | 120 秒 |
| 消费方式 | 一次性，检测后自动删除 |

安全设计：
- 临时标记，用完即删
- 120 秒 TTL 防止过期标记被复用
- 不包含任何写入内容信息

## 故障排查

| 症状 | 解决 |
|------|------|
| Plugin 未加载 | 检查 plugins 目录和 config.yaml |
| 写入被 block 但标记已创建 | 标记过期（>120s），重新 touch |
| 解锁失败 | 检查文件属主和权限 |

## 自包含清单

```
tools-memory-user-file-in/
├── SKILL.md（本文）
└── bundled/plugins/memory-file-guard/
    ├── __init__.py（Plugin 源码）
    └── plugin.yaml（Plugin 声明）
```

零外部依赖。所有代码均为 Python 标准库。
