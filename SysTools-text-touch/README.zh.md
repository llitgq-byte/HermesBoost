# SysTools-text-touch

**[English](README.md)** · 🇨🇳 中文

---

<p align="center">
  <strong>⚡ 复制以下内容给你的 Agent → Agent 自动配置一切：</strong>
</p>

<p align="center">
  <code>下载 https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-text-touch/text-touch/ 下的所有文件。完整阅读 SKILL.md。帮我基于正则构建消息路由 Plugin。问我三个问题：(1) 当前是 default 还是子 Agent profile？(2) 哪些短消息被误路由？(3) 每条模式应改写成什么 skill 指令？然后把 templates/ 复制到正确的 plugins/ 目录，按优先级顺序（长模式在前）填入正则规则，在 config.yaml 启用 plugin，最后重启 gateway。这是 Text-Touch — 入口消息拦截/路由框架，把确定性短消息改写成明确的 skill 指令。</code>
</p>

---

## 为什么需要？

用户在飞书里发短指令（代码、ID、状态词），LLM 经常路由到错的 skill 或者多问一句确认。Text-Touch 让路由 **100% 确定** → 先匹配、再改写、最后 Agent 执行。

### 没有 Text-Touch

```
用户：601138 S
Agent："嗯，601138 是个数字，S 是字母……我该做什么？"
       → 可能猜错，或者要求确认
```

### 有 Text-Touch

```
用户：601138 S
Text-Touch 匹配 → 改写成：
  "加载股票诊断 skill，对 601138 运行诊断"
Agent："明白，执行中。"
       → 100% 准确，零歧义
```

## 核心特性

- **零依赖 Python Plugin** — 纯 stdlib（`re`、`logging`），无需 pip 安装
- **优先命中** — 长模式排前面，不会被短模式截断
- **支持 3 种动作**：`rewrite`（改写）、`skip`（拦截）、`allow`（放行）
- **Profile 隔离** — plugin 放在 `$HERMES_HOME/plugins/`（默认）或 `$HERMES_HOME/profiles/<name>/plugins/`
- **重启 Gateway 即可热更** → 改完规则 `hermes gateway restart`
- **自带 Walkthrough + 维护指南** — 覆盖人工修改和 Agent 修改两种场景
- **可复制模板** — `__init__.py` + `plugin.yaml` 直接套用
- **700 行 SKILL.md** — 完整参考（11 部分），含 task-router 详细 walkthrough

## 工作原理

```
平台 WebSocket 接收消息
    ↓
Gateway (gateway/run.py)
    ↓
┌──────────────────────────────┐
│ pre_gateway_dispatch hook    │  ← Text-Touch 在这里拦截
│   接收 MessageEvent          │
│   返回 rewrite/skip/allow    │
└──────────────────────────────┘
    ↓
Agent (LLM + 工具链)
    ↓
┌──────────────────────────────┐
│ transform_llm_output hook    │  ← 飞书卡片等在这里拦截
└──────────────────────────────┘
    ↓
平台回复用户
```

返回值：

| 返回值 | 效果 |
|--------|------|
| `None` | 原样放行 |
| `{"action": "rewrite", "text": "..."}` | 替换消息文本，继续处理 |
| `{"action": "skip", "reason": "..."}` | 丢弃消息，Agent 看不到 |

## 安装步骤

### Step 1：定位 plugins 目录

```bash
# Default profile
$HERMES_HOME/plugins/

# 子 Agent profile
$HERMES_HOME/profiles/<your-profile>/plugins/
```

### Step 2：创建 plugin 目录

```bash
mkdir -p $HERMES_HOME/plugins/my-router
```

### Step 3：复制模板

```bash
# 先从 GitHub 下载，然后：
cp SysTools-text-touch/text-touch/templates/* $HERMES_HOME/plugins/my-router/
```

### Step 4：编辑 plugin.yaml

```yaml
name: my-router
version: "1.0.0"
description: "我的自定义消息路由"
enabled: true
```

### Step 5：编辑 `__init__.py` 填写规则

打开 `$HERMES_HOME/plugins/my-router/__init__.py`，填入正则规则：

```python
import re
import logging

logger = logging.getLogger(__name__)

_RULES = [
    # (正则模式, 动作, 改写文本 / 拦截原因)
    # 长模式放前面！
    (r"^(\d{6})\s*S$", "rewrite", "加载股票诊断 skill，对 \1 做诊断"),
    (r"^#(\d+)\s+done$", "rewrite", "标记任务 #\1 为完成"),
    (r"^(done|finished)$", "rewrite", "标记当前任务完成"),
    (r"^(雨|晴|天气)$", "skip", "被 text-touch 忽略"),
    (r"^(hello|hi|你好)$", "allow", None),
]

def _process(message: str) -> dict | None:
    if not message or not message.strip():
        return None
    message = message.strip()
    for pattern, action, replacement in _RULES:
        match = re.match(pattern, message, re.IGNORECASE)
        if match:
            if action == "allow":
                return None
            result = {"action": action}
            if action == "rewrite" and replacement:
                result["text"] = replacement
            elif action == "skip":
                result["reason"] = replacement or "命中过滤规则"
            logger.info(f"[my-router] '{message}' → {result}")
            return result
    return None

def pre_gateway_dispatch(event: dict) -> dict | None:
    message = event.get("message", "")
    return _process(message)
```

### Step 6：config.yaml 启用 plugin

```yaml
# config.yaml
plugins:
  enabled:
    - my-router
```

### Step 7：重启 Gateway

```bash
hermes gateway restart
```

### Step 8：验证

```bash
# 检查 agent.log 是否加载了 plugin
grep "text-touch\|my-router" $HERMES_HOME/logs/agent.log

# 在飞书里发条测试短消息 → Agent 应执行改写后的指令
```

## 文件结构

```
SysTools-text-touch/
├── README.md                              ← 本文件（英文，含 ⚡ 提示）
├── README.zh.md                           ← 中文文档（含 ⚡ 提示）
└── text-touch/
    ├── SKILL.md                           ← Agent 完整指令（700 行，11 部分）
    └── templates/
        ├── __init__.py                    ← 可直接复制的 Plugin 模板（带注释）
        └── plugin.yaml                     ← 可直接复制的 Plugin 清单模板
```

## 关键：Shell Hook vs Python Plugin

Hermes 有 Shell Hook 也能挂 `pre_gateway_dispatch`，**但 `_parse_response()` 只识别 `pre_tool_call` 的 `action: block`，不识别 `rewrite` / `skip`**。要做消息改写 → **必须用 Python Plugin**。详见 SKILL.md 第 7 部分。

## 故障排查

| 问题 | 解决 |
|------|------|
| Plugin 没加载 | (1) 确认 `$HERMES_HOME/plugins/my-router/__init__.py` 存在 (2) `config.yaml` 里有 `plugins.enabled: [my-router]` (3) 重启 gateway (4) 看 `agent.log` 的 import 错误 |
| 加载了但没改写 | (1) 正则和实际消息对比 (2) 确认长模式在前 (3) 看 `agent.log` 的 `[my-router]` 调试日志 (4) 确认 `__init__.py` 导出了 `pre_gateway_dispatch` |
| `rewrite` 不生效 | Shell Hook 不能做 `rewrite` → 必须 Python Plugin。确认 `_process` 返回 `{"action": "rewrite", "text": "..."}` 且函数已注册为 `pre_gateway_dispatch` |
| 改规则后不更新 | 重启 gateway → Plugin 代码在启动时加载，不热更 |
| 多个 Plugin 冲突 | 按优先命中 — 高优先级的 plugin（长模式）应先被加载 |

## 升级与维护

Text-Touch 本体在 `$HERMES_HOME/skills/Always/text-touch/` — 是你本地 Hermes 副本。GitHub 版本是用于分享的快照。

更新流程：
1. GitHub 拉取最新
2. 替换掉 `$HERMES_HOME/skills/Always/text-touch/` 旧文件
3. 如果你定制过模板，重新复制
4. 重启 gateway

## 许可证

MIT —— 详见父仓库。