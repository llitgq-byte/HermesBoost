---
name: session-reset
description: Hermes session_reset 延迟重置功能 — 完整配置指南。记录所有源码改动、部署步骤、启用/关闭方法、Skill 触发写法。适用于所有 Hermes Agent profile。
---

# Session Reset Tool — 延迟重置功能

让 Agent 在完成复杂 Skill 后自动清除 session 上下文，**不影响当前回复的投递**（飞书卡片、文字、语音等全部正常发送后，才清 session）。

## 工作原理（时序图）

```
用户消息 → Agent 加载 Skill → 执行工具链 → 调用 session_reset → 生成最终回复
                                                              ↓
                                                    飞书发送卡片+文字（完整投递）
                                                              ↓
                                                    Gateway 检查 pending 标志
                                                              ↓
                                                    执行 session reset
                                                              ↓
                                                    下一条用户消息 → 全新 session
```

关键：`session_reset` 是**延迟执行**——tool 只设一个 flag，真正的 reset 在 gateway 投递完所有消息后才触发。

---

## 源码改动清单

所有改动位于 Hermes 核心代码目录 `$HERMES_HOME/hermes-agent/`，属于**全局生效**（所有 profile 共享）。

### 1. 新建工具文件

**文件**: `$HERMES_HOME/hermes-agent/tools/session_reset_tool.py`

新建文件，97 行。定义了 `session_reset` 工具的 schema 和 registry 注册。

核心结构：
- `SESSION_RESET_SCHEMA` — OpenAI function calling 格式的 schema，含一个 `reason` 参数
- `session_reset_tool()` — handler 函数（实际 dispatch 在 tool_executor.py 里）
- `registry.register(name="session_reset", toolset="hermes-cli", ...)` — 注册到 hermes-cli toolset

### 2. toolsets.py — 注册到工具分组

**文件**: `$HERMES_HOME/hermes-agent/toolsets.py`

**改动 A** — `_HERMES_CORE_TOOLS` 列表加入 `"session_reset"`（约 L54）：

```python
    # Deferred session reset (after response delivery)
    "session_reset",
```

**改动 B** — 新增 `session_reset_tool` toolset 定义（约 L233）：

```python
    "session_reset_tool": {
        "description": "Deferred session context reset after response delivery",
        "tools": ["session_reset"],
        "includes": []
    },
```

**改动 C** — `hermes-feishu` 的 tools 列表加入 `"session_reset"`（约 L501）：

```python
    "hermes-feishu": {
        "tools": _HERMES_CORE_TOOLS + [
            ...,
            "session_reset",   # ← 新增
            ...
        ],
    }
```

> **原理**：`hermes-feishu` 是飞书平台的默认 toolset，所有通过飞书交互的 Agent 都自动获得 `session_reset` 工具。其他平台（如 CLI、Discord）如果在 `hermes-cli` toolset 下也能用，因为 `session_reset` 已在 `_HERMES_CORE_TOOLS` 里。

### 3. model_tools.py — 标记为 Agent-Loop 工具

**文件**: `$HERMES_HOME/hermes-agent/model_tools.py`

**改动** — `_AGENT_LOOP_TOOLS` 集合加入 `"session_reset"`（L556）：

```python
_AGENT_LOOP_TOOLS = {"todo", "memory", "session_search", "delegate_task", "session_reset"}
```

> **原理**：Agent-Loop 工具不通过标准 MCP dispatch，而是在 `tool_executor.py` 里有专属分支处理，可以直接访问 agent 实例。

### 4. tool_executor.py — 设延迟标志

**文件**: `$HERMES_HOME/hermes-agent/agent/tool_executor.py`

**改动** — 新增 `session_reset` 分支（约 L778-796）：

```python
elif function_name == "session_reset":
    _reason = function_args.get("reason", "no reason provided")
    agent._pending_session_reset = True
    agent._pending_reset_reason = _reason[:500]
    function_result = json.dumps({
        "status": "ok",
        "message": "Session reset scheduled. It will take effect after this reply is delivered.",
        "reason": _reason[:200],
    })
```

> **原理**：只设两个 flag（`_pending_session_reset` 和 `_pending_reset_reason`），不做实际 reset。Agent 继续生成最终回复。

### 5. run.py — 延迟执行 Reset

**文件**: `$HERMES_HOME/hermes-agent/gateway/run.py`

**改动** — 在 compression exhaustion 块之后，新增延迟 reset 检查（约 L9227-9271）：

```python
# --- Deferred session reset (requested by session_reset tool) ---
_cached_agent_for_reset = self._running_agents.get(session_key)
if getattr(_cached_agent_for_reset, "_pending_session_reset", False):
    _reset_reason = getattr(_cached_agent_for_reset, "_pending_reset_reason", "tool request")
    logger.info("Deferred session reset for %s (reason: %s)", session_key, _reset_reason)
    try:
        self.session_store.reset_session(session_key)
        self._evict_cached_agent(session_key)
        self._session_model_overrides.pop(session_key, None)
        self._set_session_reasoning_override(session_key, None)
        self._clear_session_boundary_security_state(session_key)
        if hasattr(self, "_pending_model_notes"):
            self._pending_model_notes.pop(session_key, None)
        # Fire session hooks
        await self.hooks.emit("session:end", {...})
        await self.hooks.emit("session:reset", {...})
    except Exception as _reset_err:
        logger.error("Deferred session reset FAILED for %s: %s", session_key, _reset_err)
```

> **原理**：这段代码在 agent 回复**完全投递后**才执行。`reset_session()` 清除 session 数据，`_evict_cached_agent()` 驱逐缓存确保下次消息创建全新 agent。

---

## 已部署的 Agent

当前已验证可用的 Agent：

| Agent | Profile | 平台 | 状态 |
|-------|---------|------|------|
| <main-agent> | <your-profile> | 飞书 | ✅ 已验证 |
| <main-agent> | <your-profile> | 飞书 | ✅ 共享核心代码，开箱可用 |
| <life-agent> | <your-profile> | 飞书 | ✅ 共享核心代码，开箱可用 |
| <stock-agent> | <your-profile> | 飞书 | ✅ 共享核心代码，开箱可用 |

所有 Agent 共享同一套核心代码（`$HERMES_HOME/hermes-agent/`），只要平台 toolset 包含 `hermes-feishu` 或 `hermes-cli`，`session_reset` 就自动可用。

---

## 启用与关闭

### 功能已全局开启

由于改动在核心代码层，`session_reset` 工具对所有 Agent **默认可用**，无需任何额外配置。

### 让 Agent 使用它

Agent 是否调用 `session_reset` 完全由 **Skill 指令** 控制：

- **启用**：在 Skill 的 `## Finishing` 部分写明调用指令
- **关闭**：不写调用指令，Agent 就不会调
- **选择性启用**：只在需要的 Skill 里写，其他 Skill 不受影响

### 如果需要临时禁用（不重建代码）

删掉 tool 文件或从 toolsets.py 移除，然后重启所有 gateway：

```bash
# 临时禁用：从 hermes-feishu 和 _HERMES_CORE_TOOLS 中移除 session_reset
# 然后重启所有 profile 的 gateway
hermes gateway restart --profile <your-profile>
hermes gateway restart --profile <your-profile>
# ... 其他 profile
```

---

## 如何在 Skill 里触发

### 基本写法

在 Skill 的 `## Finishing` 段落加入指令：

```markdown
## Finishing

任务完成后，调用 session_reset tool 清除上下文。
reason 写「<具体任务描述>」。
```

### 示例：股票分析 Skill

```markdown
---
name: stock-analysis
description: 分析指定股票的技术面和基本面
triggers:
  - 用户要求分析股票
---

# 股票分析

执行以下步骤：

1. 使用搜索工具获取目标股票的最新行情数据
2. 分析技术指标（MA、MACD、RSI 等）
3. 用飞书卡片输出分析报告
4. 给出操作建议

## Finishing

分析报告输出完成后，调用 session_reset tool 清除上下文。
reason 写「股票分析完成：<股票名称> 技术面+基本面综合分析」。
```

### 关键要点

1. **调用时机**：放在 `## Finishing` 段落，确保所有工具调用和输出都完成后才触发
2. **reason 参数**：写清楚重置原因，方便日志审计。格式建议：`<任务类型>完成：<具体内容>`
3. **不要滥用**：只在**消耗大量 context 的复杂任务**后使用。简单对话保留上下文更重要
4. **飞书卡片安全**：reset 发生在回复投递之后，卡片和文字不会丢失
5. **选择性使用**：不是每个 Skill 都需要 reset，按需添加即可

### 最佳实践

| 场景 | 建议 |
|------|------|
| 简单问答（查天气、算数） | ❌ 不需要 reset |
| 多步搜索+分析（股票分析、新闻摘要） | ✅ 需要 reset |
| 单次工具调用（查日历、发消息） | ❌ 不需要 reset |
| 长对话积累大量 context | ✅ 建议定期 reset |
| 需要跨轮对话记忆的 skill | ❌ 不要 reset |

---

## 故障排查

### 问题：模型说"session_reset 工具不可用"

**排查步骤**：

1. **确认 tool 文件存在**：`ls $HERMES_HOME/hermes-agent/tools/session_reset_tool.py`
2. **确认 toolset 注册**：`grep "session_reset" $HERMES_HOME/hermes-agent/toolsets.py`（应有 3 处）
3. **确认 agent-loop 注册**：`grep "session_reset" $HERMES_HOME/hermes-agent/model_tools.py`
4. **确认 tool_executor 分支**：`grep "session_reset" $HERMES_HOME/hermes-agent/agent/tool_executor.py`
5. **确认 run.py 延迟逻辑**：`grep "pending_session_reset" $HERMES_HOME/hermes-agent/gateway/run.py`

如果代码都正确但模型仍说不可用，**删除旧 session 再重启 gateway**：

```bash
# 删除 session 缓存（强制重建 agent）
rm <profile>/sessions/sessions.json

# 重启 gateway
hermes gateway restart --profile <name>
```

### 问题：调用了 session_reset 但 session 没清

检查 gateway 日志：

```bash
grep "Deferred session reset" <profile>/logs/agent.log
```

如果有日志但没清成功，说明 `reset_session()` 抛异常。看 ERROR 日志。

---

## 排查经验记录

### 踩坑 1：Agent 缓存

Gateway 有 agent 缓存机制（`_agent_config_signature`），重启 gateway 后如果旧 session 还在，会复用旧 agent 对象。**旧 agent 构建时还没有 session_reset tool**，所以模型看不到它。

**解决**：删掉 `sessions.json` 强制创建新 session，或用户发 `/new`。

### 踩坑 2：toolset 匹配

`session_reset` 必须出现在**平台 toolset 解析后的工具名列表**里。光注册到 registry 不够——还需要在 `toolsets.py` 里把工具名加入对应平台的 toolset 定义。

`hermes-feishu` 是飞书平台默认 toolset，包含 `_HERMES_CORE_TOOLS + [额外工具]`。所以把 `session_reset` 加到 `_HERMES_CORE_TOOLS` 就能覆盖所有平台。

### 踩坑 3：agent-loop 工具注册

`session_reset` 不是普通 MCP 工具，而是 agent-loop 工具（直接在 tool_executor.py 分支处理）。必须：
- 在 `model_tools.py` 的 `_AGENT_LOOP_TOOLS` 集合中加入
- 在 `tool_executor.py` 的 elif 链里加专属分支
- 不能走标准的 registry dispatch（否则无法设置 agent 实例的 flag）

---

## 升级风险提醒

这些改动修改了 Hermes 核心代码。如果 `hermes upgrade` 更新了以下文件，改动会被覆盖：

- `tools/registry.py` — 不太可能影响（我们新建了独立文件）
- `toolsets.py` — **高风险**（`_HERMES_CORE_TOOLS` 和 `hermes-feishu` 都在这里）
- `model_tools.py` — **中风险**（`_AGENT_LOOP_TOOLS` 可能被重构）
- `agent/tool_executor.py` — **中风险**（elif 链可能被重构）
- `gateway/run.py` — **高风险**（核心逻辑变动频繁）

**升级后**：重新检查上述 5 处改动是否还在，如被覆盖需重新 patch。升级前建议备份：`hermes-backup`。
