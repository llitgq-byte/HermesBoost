# SysTools-session-reset

> ⚠️ **WARNING — System-Level Modification**
>
> This skill modifies Hermes Agent's **core source code** (5 files in `$HERMES_HOME/hermes-agent/`). It is NOT a sandboxed plugin — patches persist at the framework level and affect ALL profiles on the machine.
>
> **Tested on**: Hermes Agent **v0.15.1** (June 2026)
> **Affected files**:
> - `$HERMES_HOME/hermes-agent/tools/session_reset_tool.py` *(new)*
> - `$HERMES_HOME/hermes-agent/toolsets.py`
> - `$HERMES_HOME/hermes-agent/model_tools.py`
> - `$HERMES_HOME/hermes-agent/agent/tool_executor.py`
> - `$HERMES_HOME/hermes-agent/gateway/run.py`
>
> **Upgrade behavior**: `hermes upgrade` may overwrite the 4 modified files. Re-apply patches from `references/patches.md` afterward, then restart all gateways.
>
> **Backup before installing**: `hermes-backup` or `cp -r $HERMES_HOME/hermes-agent $HERMES_HOME/hermes-agent.bak`
>
> ---

## What It Does

**Session Reset** lets a Hermes Agent **defer clearing its conversation context** until *after* its current reply has been fully delivered to the user (Feishu cards, text, voice, etc.). The next user message then starts with a fresh session.

This solves three common problems:

| Problem | Without reset | With session_reset |
|---------|--------------|-------------------|
| Context bloat after multi-step analysis (e.g. 5-stock deep-dive) | Next turn inherits 30k tokens of stale context | Next turn starts clean |
| Model "forgetting" early conversation due to context truncation | Hits `max_tokens` limit, drops earlier turns | Clears before hitting limit |
| Accumulat...[truncated]