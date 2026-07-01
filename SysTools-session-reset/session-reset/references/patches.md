# Session Reset 源码改动 Patch 集合

> 适用于 Hermes Agent 核心代码 `$HERMES_HOME/hermes-agent/`
> 
> 升级后如果改动被覆盖，按以下 patch 重新应用即可。

---

## Patch 1: toolsets.py — 3 处改动

**文件路径**: `$HERMES_HOME/hermes-agent/toolsets.py`

### 改动 A: `_HERMES_CORE_TOOLS` 加入 session_reset（约 L53-54）

在 `"session_search",` 之后加入：

```python
    # Session history search
    "session_search",
    # Deferred session reset (after response delivery)
    "session_reset",
    # Clarifying questions
    "clarify",
```

### 改动 B: 新增 `session_reset_tool` toolset 定义（约 L232-237）

在 `"session_search"` toolset 定义之后加入：

```python
    "session_reset_tool": {
        "description": "Deferred session reset — clear context after response delivery",
        "tools": ["session_reset"],
        "includes": []
    },
```

### 改动 C: `hermes-feishu` 的 tools 列表加入 session_reset（约 L501）

```python
    "hermes-feishu": {
        "description": "Feishu/Lark bot toolset - enterprise messaging via Feishu/Lark (full access)",
        "tools": _HERMES_CORE_TOOLS + [
            "feishu_doc_read",
            "feishu_drive_list_comments",
            "feishu_drive_list_comment_replies",
            "feishu_drive_reply_comment",
            "feishu_drive_add_comment",
            "session_reset",      # ← 新增这一行
        ],
        "includes": []
    },
```

---

## Patch 2: model_tools.py — 1 处改动

**文件路径**: `$HERMES_HOME/hermes-agent/model_tools.py`

在 `_AGENT_LOOP_TOOLS` 集合中加入 `"session_reset"`（约 L556）：

```python
_AGENT_LOOP_TOOLS = {"todo", "memory", "session_search", "delegate_task", "session_reset"}
```

---

## Patch 3: agent/tool_executor.py — 1 处改动

**文件路径**: `$HERMES_HOME/hermes-agent/agent/tool_executor.py`

在 `delegate_task` 分支之后（约 L778），`context_engine_tool_names` 分支之前，加入：

```python
        elif function_name == "session_reset":
            # Deferred session reset — set flag, actual reset happens in
            # gateway run.py after all messages are delivered.
            _reason = function_args.get("reason", "no reason provided")
            agent._pending_session_reset = True
            agent._pending_reset_reason = _reason[:500]
            function_result = json.dumps({
                "status": "ok",
                "message": (
                    "Session reset scheduled. It will take effect after this "
                    "reply is delivered. The next message will start fresh."
                ),
                "reason": _reason[:200],
            })
            tool_duration = time.time() - tool_start_time
            if agent._should_emit_quiet_tool_messages():
                agent._vprint(
                    f"  {_get_cute_tool_message_impl('session_reset', function_args, tool_duration, result=function_result)}"
                )
```

---

## Patch 4: gateway/run.py — 1 处改动

**文件路径**: `$HERMES_HOME/hermes-agent/gateway/run.py`

在 compression exhaustion 块结束之后（约 L9226-9271），加入延迟 reset 检查逻辑：

```python
            # --- Deferred session reset (requested by session_reset tool) ---
            # Check if the agent called session_reset during its tool loop.
            # The tool handler sets agent._pending_session_reset = True;
            # we execute the actual reset here, AFTER all messages (cards,
            # text replies, voice) have been delivered.
            _cached_agent_for_reset = self._running_agents.get(session_key)
            if getattr(_cached_agent_for_reset, "_pending_session_reset", False):
                _reset_reason = getattr(
                    _cached_agent_for_reset, "_pending_reset_reason", "tool request"
                )
                logger.info(
                    "Deferred session reset for %s (reason: %s)",
                    session_key,
                    _reset_reason,
                )
                try:
                    self.session_store.reset_session(session_key)
                    self._evict_cached_agent(session_key)
                    self._session_model_overrides.pop(session_key, None)
                    self._set_session_reasoning_override(session_key, None)
                    self._clear_session_boundary_security_state(session_key)
                    if hasattr(self, "_pending_model_notes"):
                        self._pending_model_notes.pop(session_key, None)
                    # Fire session hooks
                    try:
                        await self.hooks.emit("session:end", {
                            "platform": source.platform.value if source.platform else "",
                            "user_id": source.user_id,
                            "session_key": session_key,
                        })
                        await self.hooks.emit("session:reset", {
                            "platform": source.platform.value if source.platform else "",
                            "user_id": source.user_id,
                            "session_key": session_key,
                        })
                    except Exception:
                        logger.debug("Failed to emit session hooks on deferred reset", exc_info=True)
                    logger.info(
                        "Deferred session reset completed for %s", session_key,
                    )
                except Exception as _reset_err:
                    logger.error(
                        "Deferred session reset FAILED for %s: %s",
                        session_key, _reset_err,
                    )
```

> ⚠️ 注意：这段代码插入位置的标志——在 compression exhaustion 的 `except` 块结束之后，`ts = datetime.now().isoformat()` 之前。搜索 `compression exhaustion` 或 `at maximum context capacity` 可以定位。