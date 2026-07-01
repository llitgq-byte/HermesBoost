# Memory File Guard

**🇨🇳 中文** · [English](README.md)

---

一个 Hermes Agent 插件，**拦截 memory 和 user 文件的写入操作**，要求用户明确批准后才能提交更改。作为安全防护网，防止 AI 在未经你同意的情况下静默覆写你的持久记忆文件。

> **⚡ 复制这段给你的 Agent → Agent 会自动完成全部配置：**
>
> ```
> 从 https://github.com/llitgq-byte/HermesBoost/tree/main/auxiliary/memory-file-guard/bundled/plugins/memory-file-guard 下载 plugin.yaml 和 __init__.py，放到 $HERMES_HOME/plugins/memory-file-guard/ 目录下，然后在 config.yaml 的 plugins.enabled 中添加 memory-file-guard，最后重启 gateway。这是一个 Memory File Guard 插件，拦截 Hermes Agent 对 memory 和 user 文件的写入操作，要求用户明确批准后才允许更改，防止 AI 静默覆写持久记忆。
> ```

## 为什么需要它？

Hermes Agent 使用两个文件 —— `MEMORY.md` 和 `USER.md` —— 来存储跨会话的持久知识。这些文件至关重要：它们决定了 Agent 的行为方式、对你的记忆内容，以及它在未来对话中的响应方式。

问题在于：Agent 随时可以写入这些文件，无需询问。一次幻觉或推理失误就可能破坏你的整个记忆库。

**Memory File Guard** 通过强制要求人工审批来解决这一问题。每次写入尝试都会被拦截，直到你明确批准。

## 核心特性

- **硬拦截** —— 插件级 hook 在 `memory` 工具调用执行前将其阻断。Agent 无法绕过。
- **零依赖** —— 纯 Python 标准库。无需 pip 安装，无外部包。
- **跨平台** —— 同时支持 macOS（`uchg`/`xattr`）和 Linux（`chattr +i`）文件锁。
- **基于标记文件的审批机制** —— 120 秒 TTL 标记文件，确保审批即时有效且一次性使用。
- **自包含** —— 所需的一切都打包在本目录中。复制到任何 Hermes 实例即可使用。

## 工作原理

```
Agent 想写入 memory
        ↓
   调用 memory 工具
        ↓
   Plugin 拦截（pre_tool_call hook）
        ↓
   无审批标记？→ 阻断 → 向 Agent 返回操作指引
        ↓
   Agent 读取当前文件内容
   Agent 通过 clarify() 询问用户 → 展示将要变更的内容
        ↓
   用户批准 → Agent 创建标记文件 + 解锁文件
        ↓
   Agent 重新调用 memory 工具
        ↓
   Plugin 检测到标记 → 放行 → 消费（删除）标记
        ↓
   写入成功 → Agent 重新上锁文件
   Agent 展示完整内容 + 新旧对比
```

两层防护：

| 层级 | 机制 | 用途 |
|------|------|------|
| **Plugin 拦截** | `pre_tool_call` hook | 硬拦截 —— 未经批准，memory 写入不可能执行 |
| **OS 文件锁**（可选） | `uchg` / `chattr +i` | 二次保险 —— 即使插件失效，操作系统层面也会阻止写入 |

## 安装

### 前置条件

- Hermes Agent v0.15.0+（支持 Plugin）
- Python 3.9+（仅标准库）

### 第一步：复制插件

```bash
# 确定 HERMES_HOME
# 默认 profile：~/.hermes
# 子 Agent profile：~/.hermes/profiles/<name>

PLUGIN_SRC=<本目录>/bundled/plugins/memory-file-guard
PLUGIN_DST=$HERMES_HOME/plugins/memory-file-guard

cp -r "$PLUGIN_SRC" "$PLUGIN_DST"
```

### 第二步：在 config.yaml 中启用

在 Hermes 的 `config.yaml` 中添加：

```yaml
plugins:
  enabled:
    - memory-file-guard
```

### 第三步：重启 Gateway

```bash
hermes gateway restart
# 子 Agent：
# hermes gateway restart --profile <name>
```

### 第四步：验证

在 Agent 日志中查看：

```
plugins.memory-file-guard: memory-file-guard plugin registered (pre_tool_call)
```

## 使用方式

无需学习任何特殊命令。插件透明运行：

1. **你不需要改变任何使用习惯** —— 正常使用 Hermes 即可。
2. 当 Agent 尝试写入 `MEMORY.md` 或 `USER.md` 时，插件自动拦截。
3. Agent 会收到指引，向你展示**具体的变更内容**并请求批准。
4. 你说同意或拒绝。只有你的批准才能让写入通过。

### Agent 被拦截后做了什么

Agent 在被拦截时会收到一套结构化的操作指引：

1. 读取当前文件内容
2. 调用 `clarify()` 向你展示：操作类型（add/replace/remove）、目标文件、旧内容、新内容
3. 等待你的确认
4. 批准后：解锁文件 → 创建标记 → 重新调用 memory 工具 → 重新上锁文件
5. 向你展示更新后的完整内容和新旧对比

### 如果你拒绝了怎么办

Agent 直接停止。不会有任何更改。Memory 文件保持原样。

## 配置说明

### 必须配置

| 配置项 | 位置 | 值 |
|--------|------|----|
| 插件路径 | `$HERMES_HOME/plugins/memory-file-guard/` | 必须存在 |
| config.yaml 条目 | `plugins.enabled` | 必须包含 `memory-file-guard` |

### 可选：OS 级文件锁

为了纵深防御，你可以在操作系统层面锁定 memory 文件。即使插件意外失效，操作系统也会阻止修改。

**macOS：**

```bash
# 上锁
chflags uchg ~/.hermes/memories/MEMORY.md
chflags uchg ~/.hermes/memories/USER.md

# 解锁（Agent 在批准写入时会自动执行）
chflags nouchg ~/.hermes/memories/MEMORY.md
```

**Linux：**

```bash
# 上锁
chattr +i ~/.hermes/memories/MEMORY.md
chattr +i ~/.hermes/memories/USER.md

# 解锁
chattr -i ~/.hermes/memories/MEMORY.md
```

### 标记文件

| 属性 | 值 |
|------|---|
| 路径 | `/tmp/hermes-memory-guard-approved` |
| 有效期 | 120 秒 |
| 行为 | 首次使用后被消费（删除） |

## 文件结构

```
memory-file-guard/
├── README.md                          # 本文件（中文）
├── README.zh.md                       # 本文件（中文）
└── bundled/
    └── plugins/
        └── memory-file-guard/
            ├── __init__.py            # 插件源码
            └── plugin.yaml            # 插件声明
```

## 故障排查

| 症状 | 原因 | 解决方法 |
|------|------|---------|
| 插件未加载 | 放错目录或未在 config.yaml 中启用 | 检查插件路径和 `config.yaml` |
| 标记文件已创建但仍被拦截 | 标记过期（>120s） | 重新执行 `touch /tmp/hermes-memory-guard-approved` |
| 解锁失败 | 文件权限不足 | 检查文件属主和权限 |
| 写入成功后重新上锁失败 | 文件被其他进程占用 | 检查是否有其他进程访问文件 |

## 许可证

MIT
