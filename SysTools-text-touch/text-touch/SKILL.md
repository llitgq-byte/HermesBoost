---
name: text-touch
description: 基于正则匹配的 Gateway 入口消息拦截/路由框架。通过 Python Plugin 注册 pre_gateway_dispatch hook，在用户消息到达 Agent 之前进行 rewrite，实现零误判的精准意图路由。
version: "2.1.0"
triggers:
  - 消息路由 hook
  - pre_gateway_dispatch
  - 拦截用户消息
  - gateway hook plugin
  - 消息重写 rewrite
  - text-touch
  - 用户短指令识别不准
  - agent猜不准意图
  - 简短命令自动路由
  - 输入消息拦截
  - 用户消息预处理
related_skills: []
---

# Text-Touch — Gateway 入口消息拦截/路由框架

在 Gateway 入口处拦截用户消息，通过正则匹配将短消息 rewrite 为明确的 skill 指令，让 Agent 无需"猜"用户意图，实现 100% 确定性路由。

---

## 第零部分：什么时候需要用 Text-Touch

**适用场景：** 用户经常发送简短的指令（如 `601138 S`、`#12 done`、`报警`），Agent 难以准确判断该调用哪个 skill 或执行什么操作。

**不适用的场景：** 用户消息本身已经很明确（如"帮我查一下茅台的财报"、"把这段代码格式化"），Agent 能直接理解意图。

### 怎么判断你的 Agent 是否需要 Text-Touch

如果你的 Agent 满足以下**全部条件**，就应该使用 Text-Touch：

1. **有多个 skill**，每个 skill 处理不同类型的任务
2. **用户习惯发短指令**（几个字、几个数字、代号），而不是完整的自然语言句子
3. **短指令的模式是可预测的**（有固定格式，可以用正则表达）
4. **Agent 经常猜错意图**，把短指令分配给了错误的 skill

### 一个例子说明问题

```
没有 Text-Touch：
  用户：601138 S
  Agent 心想："601138"是个数字，"S"是个字母...用户要干嘛？
  → 可能触发个股分析（猜对），也可能返回"请详细说明您的需求"（猜错）

有 Text-Touch：
  用户：601138 S
  Text-Touch 匹配到 S 模式 → rewrite 为：
  "请加载 stock-chromeJJ skill，对 601138 执行诊股+巨潮测评+F10全景"
  Agent 心想："明确指令，执行！"
  → 100% 准确，零误判
```

---

## 第一部分：原理与架构

### 1.1 Hermes 消息流水线

用户消息从飞书/Telegram 等平台发出后，经过以下链路：

```
平台 WebSocket 收到消息
    ↓
Gateway (gateway/run.py)
    ↓
┌─────────────────────────────────────────────┐
│  ① pre_gateway_dispatch hook                │  ← Text-Touch 在这里拦截
│     Plugin 回调函数接收 MessageEvent           │
│     返回 rewrite/skip/allow                   │
└─────────────────────────────────────────────┘
    ↓ (不匹配则原样放行)
Agent (agent/conversation_loop.py)
    ↓
LLM 推理 + 工具调用
    ↓
┌─────────────────────────────────────────────┐
│  ② transform_llm_output hook               │  ← 飞书卡片等在这里拦截
│     Agent 回复发出前，可改写输出内容            │
└─────────────────────────────────────────────┘
    ↓
平台推送回复给用户
```

**两个 hook 在流水线上完全不同的阶段，互不冲突：**
- `pre_gateway_dispatch` — **入口**，改写用户输入（Text-Touch）
- `transform_llm_output` — **出口**，改写 Agent 输出（如飞书卡片）

### 1.2 Text-Touch 的核心思想

在消息到达 Agent **之前**，通过正则匹配将短消息 rewrite 成明确的指令。Agent 收到的是明确的指令，不再需要猜测意图。

### 1.3 为什么用 Python Plugin 而不是 Shell Hook

| 方式 | 注册路径 | 回调执行 | 对 rewrite 的支持 |
|------|---------|---------|-----------------|
| **Shell Hook** | config.yaml `hooks.pre_gateway_dispatch` | bash 子进程 → stdout JSON → `_parse_response()` | ❌ **不支持** `_parse_response()` 只认识 `pre_tool_call` 的 `block` 和通用 `context`，不认识 `pre_gateway_dispatch` 的 `rewrite`/`skip` |
| **Python Plugin** | Plugin 的 `register(ctx)` | `PluginManager.invoke_hook()` 直接调用 Python 函数 | ✅ **完整支持** 返回值直接被 `gateway/run.py` 消费，无中间解析 |

**结论：必须用 Python Plugin，Shell Hook 方式不可行。**

---

## 第二部分：Hook 协议详解

### 2.1 pre_gateway_dispatch 的调用方式

源码位置：`gateway/run.py` 第 6929-6965 行

```python
_hook_results = _invoke_hook(
    "pre_gateway_dispatch",
    event=event,        # MessageEvent dataclass
    gateway=self,
    session_store=self.session_store,
)

for _result in _hook_results:
    if not isinstance(_result, dict):
        continue
    _action = _result.get("action")
    if _action == "skip":
        return None                          # 丢弃消息，不转发给 Agent
    if _action == "rewrite":
        _new_text = _result.get("text")
        if isinstance(_new_text, str):
            event = dataclasses.replace(event, text=_new_text)  # 替换消息文本
    # "allow" 或 None → 原样放行
```

### 2.2 MessageEvent 对象

```python
# gateway/platforms/base.py
class MessageEvent:
    text: str                           # 用户消息文本 ← 主要匹配目标
    message_type: MessageType            # TEXT / IMAGE / ...
    source: SessionSource                # platform, chat_id, user_id 等
    raw_message: Any                    # 平台原始数据
    message_id: Optional[str]
    platform_update_id: Optional[int]
    media_urls: List[str]
    media_types: List[str]
```

### 2.3 Plugin 回调函数签名

```python
def _on_pre_gateway_dispatch(
    event: Any,                          # MessageEvent 实例
    gateway: Any = None,                 # Gateway 实例
    session_store: Any = None,           # Session 存储实例
    **kwargs,
) -> Optional[Dict[str, str]]:
    text = getattr(event, "text", "")    # 提取用户消息
    if not text:
        return None                       # 放行

    # 正则匹配...
    # 匹配成功：
    return {"action": "rewrite", "text": "改写后的文本"}

    # 匹配失败：
    return None                            # 放行
```

### 2.4 三种返回值

| 返回值 | 效果 |
|--------|------|
| `None` | 原样放行，消息传给 Agent |
| `{"action": "rewrite", "text": "..."}` | 替换 event.text，继续传给 Agent |
| `{"action": "skip", "reason": "..."}` | 丢弃消息，Agent 完全看不到，Gateway 直接 return |

---

## 第三部分：Plugin 目录结构

### 3.1 标准结构

```
<plugins 目录>/<plugin_name>/
├── __init__.py      # Plugin 入口：正则规则 + register() 函数
└── plugin.yaml      # Plugin 声明：名称、版本、provides_hooks
```

### 3.2 plugin.yaml

```yaml
name: <plugin-name>
version: "1.0.0"
description: 简短描述
author: user
provides_hooks:
  - pre_gateway_dispatch
```

### 3.3 Plugin 放在哪个目录

**这是最容易踩的坑。** Plugin 必须放在正确的 plugins 目录下，否则不会被加载。

**如何判断？看你的 Agent 是 default profile 还是子 Agent（profile）：**

```
情况 A：你的 Agent 是 default（即只有一个 Agent，没有创建子 Agent）
  Plugin 放在：$HERMES_HOME/plugins/<plugin_name>/
  config.yaml 位置：$HERMES_HOME/config.yaml

情况 B：你的 Agent 是子 Agent（profile）
  Plugin 放在：$HERMES_HOME/profiles/<profile_name>/plugins/<plugin_name>/
  config.yaml 位置：$HERMES_HOME/profiles/<profile_name>/config.yaml
```

**为什么？** 运行时 `HERMES_HOME` 环境变量指向当前 Agent 的根目录，Plugin 扫描路径是 `HERMES_HOME/plugins/`：
- default profile → `$HERMES_HOME/plugins/`
- 子 Agent profile → `$HERMES_HOME/profiles/<name>/plugins/`

放错位置，config.yaml 里写了对也不会加载，日志里不会有 `registered`。

### 3.4 config.yaml 启用

在对应 config.yaml 中，将 plugin 名称添加到 `plugins.enabled` 列表：

```yaml
plugins:
  enabled:
    - <plugin-name>         # ← 添加你的路由 plugin
```

---

## 第四部分：从零开始的完整 Walkthrough

以一个**任务管理 Agent** 为例，演示如何从零创建一个消息路由 plugin。

**场景：** 用户发送 `#12 done` 表示完成任务 12，发送 `#12 wip` 表示标记进行中，发送纯数字如 `23` 表示查看任务详情。Agent 有 task-manage skill 处理任务操作。

### 4.1 确定你的 plugins 目录

```bash
# 如果是 default profile：
PLUGINS_DIR=$HERMES_HOME/plugins

# 如果是子 Agent（如 my-agent）：
PLUGINS_DIR=$HERMES_HOME/profiles/my-agent/plugins
```

### 4.2 复制模板并创建 plugin

```bash
# 创建目录
mkdir -p $PLUGINS_DIR/task-router

# 从 text-touch skill 复制模板
cp $HERMES_HOME/skills/Always/text-touch/templates/__init__.py $PLUGINS_DIR/task-router/
cp $HERMES_HOME/skills/Always/text-touch/templates/plugin.yaml $PLUGINS_DIR/task-router/
```

### 4.3 修改 plugin.yaml — 填写实际名称

```yaml
name: task-router
version: "1.0.0"
description: Route task commands (#12 done, #12 wip, pure number) to task-manage skill
author: user
provides_hooks:
  - pre_gateway_dispatch
```

### 4.4 修改 __init__.py — 编写匹配规则

打开 `$PLUGINS_DIR/task-router/__init__.py`，修改以下内容：

1. **模块文档** — 改为你的 plugin 描述
2. **logger 名称** — 改为 `plugins.task-router`
3. **`_RULES` 列表** — 删掉示例注释，写你的实际规则
4. **`register()` 日志** — 改为 `task-router plugin registered`

```python
"""
Task Router Plugin
==================
Route task-related short commands to task-manage skill.

Routes (first match wins):
  1. #N done/wip/cancel — task status update
  2. pure number N — view task detail
  Others → pass through
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger("plugins.task-router")

_RULES: list[tuple[str, re.Pattern, str]] = [
    # 1. 任务状态变更 — "#12 done"、"#3 wip"
    ("任务状态",
     re.compile(r"^#(\d+)\s+(done|wip|cancel)$"),
     "请加载 task-manage skill，将任务 #{} 标记为 {}"),

    # 2. 纯数字 — "23"表示查看任务详情
    ("任务详情",
     re.compile(r"^(\d+)$"),
     "请加载 task-manage skill，查看任务 #{} 的详情"),
]


def _on_pre_gateway_dispatch(
    event: Any,
    gateway: Any = None,
    session_store: Any = None,
    **kwargs,
) -> Optional[Dict[str, str]]:
    text = getattr(event, "text", "")
    if not text:
        return None

    for name, pattern, template in _RULES:
        m = pattern.match(text.strip())
        if m:
            rewrite_text = template.format(*m.groups())
            logger.info(
                "matched [%s]: '%s' → '%s'",
                name, text.strip(), rewrite_text,
            )
            return {"action": "rewrite", "text": rewrite_text}

    return None


def register(ctx):
    ctx.register_hook("pre_gateway_dispatch", _on_pre_gateway_dispatch)
    logger.info("task-router plugin registered (pre_gateway_dispatch)")
```

### 4.5 修改 config.yaml — 启用 plugin

```yaml
plugins:
  enabled:
    - task-router
```

### 4.6 重启 Gateway

```bash
# default profile：
hermes gateway restart

# 子 Agent：
hermes gateway restart --profile my-agent
```

### 4.7 验证加载成功

```bash
# 确认日志中出现了 registered
grep "task-router.*registered" <logs目录>/agent.log | tail -3
```

应看到：
```
plugins.task-router: task-router plugin registered (pre_gateway_dispatch)
```

如果没有任何输出，按以下顺序排查：

| 检查项 | 命令 |
|--------|------|
| Plugin 在正确目录？ | `ls <plugins_dir>/task-router/__init__.py` |
| config.yaml 已启用？ | `grep task-router <config.yaml路径>` |
| __init__.py 有 register(ctx)？ | `grep "def register" <plugins_dir>/task-router/__init__.py` |
| Gateway 已重启？ | 看 agent.log 时间戳是否是刚才 |

### 4.8 测试

```
发送 "#12 done"  → Agent 收到 "请加载 task-manage skill，将任务 #12 标记为 done"
发送 "5"         → Agent 收到 "请加载 task-manage skill，查看任务 #5 的详情"
发送 "你好"       → 原样放行，Agent 正常回复
```

在日志中确认：
```bash
grep "matched\|task-router" <logs目录>/agent.log | tail -10
```

---

## 第五部分：正则规则编写指南

### 5.1 规则格式

```python
_RULES = [
    ("规则名称",
     re.compile(r"正则表达式"),
     "rewrite 模板，用 {} 做占位符"),
]
```

`{}` 的数量必须与正则中捕获组 `()` 的数量一致。

### 5.2 规则顺序——先到先得

**更长的模式必须放在更短的模式前面！**

```python
# ❌ 错误顺序
_RULES = [
    ("两股对比", re.compile(r"^(.+)\s+vs\s+(.+)$"), ...),       # "A vs B vs C" 被截断为 "A vs B"
    ("三股对比", re.compile(r"^(.+)\s+vs\s+(.+)\s+vs\s+(.+)$"), ...),
]

# ✅ 正确顺序
_RULES = [
    ("三股对比", re.compile(r"^(.+)\s+vs\s+(.+)\s+vs\s+(.+)$"), ...),
    ("两股对比", re.compile(r"^(.+)\s+vs\s+(.+)$"), ...),
]
```

### 5.3 正则设计原则

| 原则 | 说明 | 示例 |
|------|------|------|
| 宁可漏匹配，不要误匹配 | 漏匹配 → Agent 自行处理；误匹配 → 普通对话被改写 | ❌ `买茅台` 匹配 → ✅ `茅台 买入 100, 1800` 才匹配 |
| 用 `^` 和 `$` 锚定整条消息 | 避免部分匹配导致误判 | `^(.+)\s+vs\s+(.+)$` 而非 `\s+vs\s+` |
| 纯数字类限定位数 | 避免"今天买了2杯咖啡"被匹配 | `^(\d{6})$` 匹配 6 位股票代码 |
| 可用中文匹配 | 支持中文动词/状态词 | `买入\|卖出`、`done\|wip` |

### 5.4 调试日志

Plugin 中使用标准 logging：

```python
import logging
logger = logging.getLogger("plugins.<plugin-name>")

# 匹配成功时记录（便于排查问题）
logger.info("matched [%s]: '%s' → '%s'", name, original_text, rewrite_text)
```

日志查看位置：`$HERMES_HOME/logs/agent.log`（default）或 `$HERMES_HOME/profiles/<name>/logs/agent.log`（子 Agent）。

---

## 第六部分：完整案例 — stock-router

### 6.1 需求背景

<your-profile>（<stock-agent>）Agent 有多个 skill：
- `stock-view` — 个股分析、两股对比、三股对比
- `stock-chromeJJ` — 诊股 + 巨潮测评 + F10 全景
- `stock-trading` — 交易记录

用户希望发送简短指令（如 `601138 S`、`茅台 vs 五粮液`）就能自动路由到正确的 skill。

### 6.2 匹配规则

| 输入 | 匹配规则 | rewrite 为 |
|------|---------|-----------|
| 茅台 vs 五粮液 vs 泸州老窖 | 三股对比 | 请加载 stock-view skill，使用三股对比模板分析 茅台 vs 五粮液 vs 泸州老窖 |
| 茅台 vs 五粮液 | 两股对比 | 请加载 stock-view skill，使用两股对比模板分析 茅台 vs 五粮液 |
| 601138 S / 茅台s | S模式 | 请加载 stock-chromeJJ skill，对 601138 执行诊股+巨潮测评+F10全景 |
| 茅台 买入 100, 1800 | 交易指令 | 请加载 stock-trading skill，记录交易：茅台 买入 100 1800 |
| 600519 | 个股（6位代码） | 请加载 stock-view skill，使用个股分析模板分析 600519 |
| 你好啊 | 无匹配 | 原样放行 |

### 6.3 正则表达式详解

```python
# 1. 三股对比 — "A vs B vs C"
re.compile(r"^(.+)\s+vs\s+(.+)\s+vs\s+(.+)$")

# 2. 两股对比 — "A vs B"
re.compile(r"^(.+)\s+vs\s+(.+)$")

# 3. S模式 — "代码/名称 + S"（尾部可选空格）
re.compile(r"^(.+)\s+[Ss]\s*$")

# 4. 交易指令 — "代码/名称 + 买入/卖出 + 两个数字"
re.compile(r"^(.+)\s+(买入|卖出)\s+(\d+\.?\d*)\s*[,，\s]+\s*(\d+\.?\d*)$")
# 两个数字不区分价格/数量顺序，交给 Agent 解析

# 5. 个股 — 单个6位纯数字（不支持名称，避免误匹配）
re.compile(r"^(\d{6})$")
```

### 6.4 实际文件位置

```
$HERMES_HOME/profiles/<your-profile>/plugins/stock-router/
├── __init__.py      # 正则规则 + register()
└── plugin.yaml      # 声明
```

config.yaml：
```yaml
plugins:
  enabled:
    - stock-router
```

---

## 第七部分：踩坑记录

### 7.1 Shell Hook 的 _parse_response() 不支持 rewrite（致命）

**症状：** Shell 脚本正确输出了 `{"action": "rewrite", "text": "..."}`，Gateway 日志显示 hook 已注册，但消息被原样放行。

**根因：** `agent/shell_hooks.py` 的 `_parse_response()` 函数：
- `pre_tool_call` → 只处理 `block` action
- 其他事件 → 只检查 `context` 字段
- `pre_gateway_dispatch` 的 `rewrite`/`skip`/`allow` → **完全忽略，返回 None**

**教训：** 想用 `pre_gateway_dispatch` 做 rewrite/skip，必须走 Python Plugin，不能走 Shell Hook。

### 7.2 Profile 的 plugins 目录是本地的

**症状：** Plugin 在 `$HERMES_HOME/plugins/` 下创建，`config.yaml` 已启用，但 agent.log 中没有 `registered` 日志。

**根因：** 子 Agent profile 下 `HERMES_HOME` 指向 profile 目录，Plugin 扫描的是 `$HERMES_HOME/profiles/<name>/plugins/`，不是全局 `$HERMES_HOME/plugins/`。

**教训：** Plugin 必须放在目标 Agent 的 plugins 目录下（见第三部分 3.3 节的判断方法）。

### 7.3 Gateway 日志 vs Agent 日志

| 文件 | 内容 |
|------|------|
| `logs/gateway.log` | 平台连接、消息收发、cron 调度 |
| `logs/agent.log` | **Plugin 加载/注册**、会话、tool 调用、hook 执行 |

验证 Plugin 是否加载成功，看 `agent.log`，不是 `gateway.log`。

### 7.4 多个 hook plugin 共存不会冲突

Text-Touch 类的 plugin 在 `pre_gateway_dispatch`（入口）拦截。如果有其他 plugin 在 `transform_llm_output`（出口）拦截 Agent 回复，两者在流水线上完全不同的阶段，互不干扰。

Text-Touch 本身**不依赖任何其他 plugin**，可以独立部署。

---

## 第八部分：与其他 Hook 类型的对比

| Hook 名称 | 阶段 | 用途 | 返回值 | 典型场景 |
|-----------|------|------|--------|---------|
| `pre_gateway_dispatch` | Gateway 入口 | 拦截/改写用户输入 | dict（skip/rewrite/allow）或 None | **Text-Touch 消息路由** |
| `transform_llm_output` | Agent 出口 | 拦截/改写 Agent 回复 | str（新回复文本）或 None | Markdown 转富文本卡片 |
| `pre_tool_call` | Tool 调用前 | 阻止/修改工具调用 | dict（block/allow/modify）或 None | 敏感操作审批 |
| `post_llm_call` | LLM 完成后 | 记录/持久化 | 无返回值 | 会话数据同步 |

---

## 第九部分：独立性与复制

Text-Touch 是一个**完全独立**的 skill，不依赖任何其他 skill 或 plugin。整个目录可以原样复制到其他 Agent 或其他电脑上使用。

### 复制到另一个 Agent

```bash
# 复制 skill 文件本身
cp -r $HERMES_HOME/skills/Always/text-touch $HERMES_HOME/profiles/<目标profile>/skills/Always/

# 复制模板（可选，如果目标 Agent 需要创建自己的路由 plugin）
# 模板已包含在 skill 目录的 templates/ 下，无需额外复制
```

复制后，目标 Agent 的用户只需按照第四部分的 walkthrough 创建自己的 plugin 即可。

### 复制到另一台电脑

```bash
# 整个 skill 目录复制过去即可
scp -r $HERMES_HOME/skills/Always/text-touch user@other:$HERMES_HOME/skills/Always/
```

---

## 第十部分：维护指南 — 部署后如何管理

以下内容面向**已部署了 Text-Touch 路由 plugin 的 Agent 用户**。你可以直接把这些操作告诉你的 Agent，Agent 会帮你执行。

### 10.1 增加一条匹配规则

**你可以说：**
> "在 `<plugin-name>` plugin 里增加一条规则：用户发送 `xxx` 时，rewrite 为 `请加载 yyy skill，执行 zzz`"

Agent 会：
1. 读取 `__init__.py` 中的 `_RULES` 列表
2. 按照规则顺序要求，将新规则插入到合适的位置（注意先长后短）
3. 重启 gateway
4. 测试新规则是否生效

**示例：**
> "在 stock-router 里增加一条规则：用户发送 `股票名 评级` 时，rewrite 为加载 stock-chromeJJ skill 对该股票进行评级"

### 10.2 删除/禁用一条匹配规则

**你可以说：**
> "在 `<plugin-name>` plugin 里删除 `规则名称` 这条规则"

Agent 会：
1. 从 `_RULES` 列表中移除该规则
2. 重启 gateway
3. 确认删除

**注意：** 如果只剩一条规则，删除后 plugin 仍然存在但不做任何 rewrite（所有消息原样放行）。此时建议直接关闭 plugin（见 10.3）。

### 10.3 临时关闭 plugin（不删除，随时可恢复）

**你可以说：**
> "关闭 `<plugin-name>` plugin"

Agent 会：
1. 从 `config.yaml` 的 `plugins.enabled` 列表中移除该 plugin 名称
2. 重启 gateway

恢复时：
> "重新启用 `<plugin-name>` plugin"

Agent 会把名称加回 `plugins.enabled` 并重启。

### 10.4 彻底卸载 plugin

**你可以说：**
> "卸载 `<plugin-name>` plugin"

Agent 会执行以下步骤：

**第一步：从 config.yaml 中移除**
```yaml
# 从 plugins.enabled 列表中删除 <plugin-name>
plugins:
  enabled:
    # - <plugin-name>  ← 删除这行
```

**第二步：重启 gateway**
```bash
hermes gateway restart --profile <profile>
# 或
hermes gateway restart  # default profile
```

**第三步：删除 plugin 文件**
```bash
rm -rf <plugins目录>/<plugin-name>
```

**第四步：验证**
```bash
grep "<plugin-name>" <config.yaml路径>  # 应无输出
ls <plugins目录>/<plugin-name>            # 应报错 file not found
```

### 10.5 修改现有规则

**你可以说：**
> "修改 `<plugin-name>` plugin 里 `规则名称` 的 rewrite 模板为 `新的模板文本`"

或：
> "修改 `<plugin-name>` plugin 里 `规则名称` 的正则表达式为 `新的正则`"

Agent 会更新 `_RULES` 中对应条目的 `template` 或 `pattern`，然后重启 gateway。

### 10.6 查看当前所有规则

**你可以说：**
> "列出 `<plugin-name>` plugin 的所有匹配规则"

Agent 会读取 `__init__.py` 并以表格形式展示所有规则名称、正则表达式和 rewrite 模板。

### 10.7 快速参考卡

| 你想做的事 | 怎么跟 Agent 说 |
|-----------|----------------|
| 加规则 | "在 xxx plugin 里增加一条规则：用户发 abc 时 rewrite 为 xxx" |
| 删规则 | "在 xxx plugin 里删除 yyy 这条规则" |
| 改规则 | "修改 xxx plugin 里 yyy 的正则/模板为 zzz" |
| 查规则 | "列出 xxx plugin 的所有匹配规则" |
| 暂时关闭 | "关闭 xxx plugin" |
| 重新开启 | "启用 xxx plugin" |
| 彻底删除 | "卸载 xxx plugin" |

---

## 第十一部分：相关文件索引

| 文件 | 说明 |
|------|------|
| `templates/__init__.py` | 可复制的 Plugin 开发模板（含注释和示例） |
| `templates/plugin.yaml` | 可复制的 Plugin 声明模板 |
