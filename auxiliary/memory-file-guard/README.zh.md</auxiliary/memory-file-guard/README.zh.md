# Memory & User 文件守卫

**中文** · [**English**](README.md)

---

Hermes Agent 的防御性工具 — 确保 memory 和 user 文件不会被悄悄修改。启用后，每次对 `MEMORY.md` 或 `USER.md` 的写入都会被拦截。Agent 必须先请求用户确认，确认后才执行写入。写入完成后文件立即重新锁定，并展示变更前后的对比。

## 核心特性

- **硬拦截** — Plugin 在 `pre_tool_call` 层面运作。无有效标记文件时，memory 写入直接被拒绝。
- **用户确认工作流** — 被拦截后，Agent 按 Skill 流程执行：读取当前内容 → 请求确认 → 创建标记 → 重试写入 → 重新锁定 → 展示对比。
- **限时标记** — 120 秒 TTL，过期作废，防止旧标记被复用。
- **跨平台** — 纯 Python 标准库实现。macOS 使用 `uchg`/`nouchg`/`xattr`，Linux 使用 `chattr+i`/`chattr-i`。
- **自包含** — 零外部依赖，一个 Skill 文件夹加一个 Plugin 文件夹，复制即用。
- **纵深防护** — 可与 OS 级不可变标志（uchg/chattr+i）组合使用，双重保险。

---

## 1. 项目描述

本工具**不是** Hermes 的增强，而是一道安全网。正常使用中，Hermes Agent 会写入 MEMORY.md 和 USER.md 以保留上下文。但配置不当的 Agent 可能静默覆盖重要数据。这个守卫确保没有人工确认，任何写入都不会发生。

保护目标：
- `MEMORY.md` — 持久化系统记忆（事实、偏好、约定）
- `USER.md` — 用户档案条目

针对这两个文件的 `add`、`replace`、`remove` 操作均会触发确认流程。

---

## 2. 安装方法

` ` `bash
# 1. 克隆仓库
git clone https://github.com/llitgq-byte/HermesBoost.git
cd HermesBoost/auxiliary/memory-file-guard

# 2. 复制 Skill 到目标 Hermes 配置
cp -r tools-memory-user-file-in ~/.hermes/skills/Always/

# 3. 复制 Plugin 到目标 Hermes 配置
cp -r tools-memory-user-file-in/bundled/plugins/memory-file-guard ~/.hermes/plugins/

# 4. 启用 Plugin — 编辑 ~/.hermes/config.yaml
#    （追加到 plugins.enabled 列表）

# 5. 重启 Hermes Gateway
hermes gateway restart
` ` `

---

## 3. 工作流程

Agent 调用 memory → Plugin 检查标记 → 无标记 → BLOCK → Agent 加载 Skill 流程 → 读取 → clarify() → 用户确认 → 创建标记+解锁 → 重试 → ALLOW → 重新锁定 → 展示对比。

**文件锁命令（macOS）：**

` ` `bash
chflags uchg ~/.hermes/memories/MEMORY.md
chflags uchg ~/.hermes/memories/USER.md
` ` `

**标记文件：** `/tmp/hermes-memory-guard-approved`，120 秒 TTL，一次性，不泄露数据。

---

## 4. 使用方式

用户**无需学习任何特殊命令或 API**，守卫以透明方式工作。

---

## 5. 配置说明

**config.yaml：**
` ` `yaml
plugins:
  enabled:
    - memory-file-guard
` ` `

---

## 许可证

MIT
