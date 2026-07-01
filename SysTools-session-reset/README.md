# SysTools-session-reset

[🇨🇳 中文](README.zh.md) · **English**

---

<p align="center">
  <strong>⚠️ This skill modifies Hermes Agent's core source code. Backup before installing.</strong>
</p>

<p align="center">
  <strong>⚡ Copy this to your Agent → Agent will auto-configure everything:</strong>
</p>

<p align="center">
  <code>Download all files from https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-session-reset/session-reset. Read SKILL.md + references/patches.md + references/README.md + references/session_reset_tool.py. Backup $HERMES_HOME/hermes-agent/ first. Then apply the 6 patches from references/patches.md (4 core files modified, 1 new tool file added). Restart all gateways with 'hermes gateway restart --profile &lt;name&gt;'. This is the Session Reset skill — defer session context reset until after reply delivery, so cards/text/voice are never lost.</code>
</p>

---

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

---

## Why Does This Exist?

Hermes Agent accumulates every chat turn (tool calls, search results, card content, voice transcription) into the session. After a complex multi-step task — analyze 5 stocks, scrape 10 articles, generate a 10-page report — the context can balloon to 30k+ tokens, causing:

- Slower, more expensive API calls
- Model "forgetting" early conversation due to context window truncation
- Next turn inheriting stale data from the previous task

**Session Reset** solves this by letting the Agent defer session clearing until *after* its reply has been delivered to the user. The next user message starts fresh, but the user never loses anything they were shown.

## Core Features

- **Deferred reset timing** — reset happens AFTER cards/text/voice delivery, never loses user-visible output
- **Skill-level control** — opt-in via `## Finishing` instructions in each Skill (per-Skill granularity)
- **Audit-friendly** — `reason` parameter is logged (e.g. "Completed stock analysis for 5 stocks")
- **Toolset-agnostic** — works for any platform (Feishu, CLI, Discord, Telegram) since `session_reset` is in `_HERMES_CORE_TOOLS`
- **Complete patch documentation** — references/patches.md contains 6 fully-formatted patches ready to apply
- **3 disable methods** — delete file, remove from toolset list, remove from `_AGENT_LOOP_TOOLS`

## How It Works

```
User message → Agent loads Skill → executes tool chain → calls session_reset(reason=...)
                                                                    ↓
                                                          Generate final reply
                                                                    ↓
                                                  Feishu delivers card + text (full delivery)
                                                                    ↓
                                                  Gateway checks _pending_session_reset flag
                                                                    ↓
                                                  Executes reset_session() + evict cached agent
                                                                    ↓
                                        Next user message → brand-new session (fresh context)
```

**Two-layer architecture**:
- **System layer** (modifies code) — decides whether `session_reset` tool exists at all (affects ALL agents)
- **Agent layer** (Skill instructions) — decides whether THIS skill calls reset (per-Skill control)

## Installation

### Step 1: Backup

```bash
# Use the built-in backup tool
hermes-backup

# OR manual backup
cp -r $HERMES_HOME/hermes-agent $HERMES_HOME/hermes-agent.bak
```

### Step 2: Install the new tool file

```bash
# Copy the new session_reset tool definition
cp references/session_reset_tool.py $HERMES_HOME/hermes-agent/tools/
```

### Step 3: Apply 4 patches to existing core files

Open [`references/patches.md`](references/patches.md) and apply each patch to the indicated file. Total of 6 patch locations across 4 files:

| File | Patches | Risk Level |
|------|---------|------------|
| `toolsets.py` | 3 changes (`_HERMES_CORE_TOOLS`, `session_reset_tool` def, `hermes-feishu` list) | High |
| `model_tools.py` | 1 change (`_AGENT_LOOP_TOOLS` set) | Medium |
| `agent/tool_executor.py` | 1 change (new `elif` branch for `session_reset`) | Medium |
| `gateway/run.py` | 1 change (deferred-reset check after compression exhaustion) | High |

### Step 4: Restart all gateways

```bash
hermes gateway restart --profile <your-profile>
hermes gateway restart --profile <other-profile>
# ... repeat for every profile that should have session_reset
```

### Step 5: Verify

```bash
# Confirm tool file exists
ls $HERMES_HOME/hermes-agent/tools/session_reset_tool.py

# Confirm toolset registration (should show 3 matches)
grep "session_reset" $HERMES_HOME/hermes-agent/toolsets.py

# Confirm agent-loop registration
grep "session_reset" $HERMES_HOME/hermes-agent/model_tools.py

# In a Feishu chat, send any complex multi-step task.
# The Agent should mention session_reset in its Finishing log.
grep "Deferred session reset" $HERMES_HOME/logs/agent.log
```

## File Structure

```
SysTools-session-reset/
├── README.md                              ← This file (EN, with WARNING + ⚡ prompt)
├── README.zh.md                           ← 中文文档（含警告框 + ⚡ 提示）
└── session-reset/
    ├── SKILL.md                           ← Agent instruction (309 lines, full guide)
    └── references/
        ├── README.md                      ← System-layer intro + enable/disable (184 lines)
        ├── patches.md                     ← 6 patches with full diffs (153 lines)
        └── session_reset_tool.py          ← New tool source (90 lines)
```

## Usage in a Skill

Add a `## Finishing` section to any Skill that does heavy work:

```markdown
## Finishing

After [task output] is delivered, call session_reset tool to clear context.
reason 写「[task description] — context heavy, defer reset」.
```

### When to use vs not use

| Scenario | Use reset? | Reason |
|----------|-----------|--------|
| Multi-step analysis (5 stocks, 10 articles) | ✅ Yes | Context bloat severe |
| Simple Q&A (weather, arithmetic) | ❌ No | Context small |
| Single tool call (calendar, message) | ❌ No | Unnecessary overhead |
| Long conversation accumulates history | ✅ Yes | Prevent late-window truncation |
| Skill requires cross-turn memory | ❌ No | Reset would break the skill |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Agent says "session_reset tool not available" | (1) Verify tool file exists (2) Check 3 grep matches in toolsets.py (3) Delete `sessions.json` to force agent rebuild (4) Restart gateway |
| `session_reset` called but session not cleared | Check `grep "Deferred session reset" agent.log` — if log exists but no reset, look for ERROR traceback. If no log, patches may have been overwritten. |
| Patches lost after `hermes upgrade` | Re-apply from `references/patches.md`. Before next upgrade, commit your patched core files or use `hermes-backup`. |
| `_pending_session_reset` not set after tool call | Verify `_AGENT_LOOP_TOOLS` includes `"session_reset"` in `model_tools.py`. Missing this routes the call through standard MCP dispatch instead of the elif branch. |
| Agent rebuilt but doesn't see new tool | Delete `sessions.json` and restart gateway. Old agent object is cached and built before the patch. |

## Upgrade & Maintenance

These patches modify Hermes **core source code** — `hermes upgrade` may overwrite them.

**After every upgrade:**
1. `diff -r $HERMES_HOME/hermes-agent /path/to/backup` to find what changed
2. Re-apply any lost patches from `references/patches.md`
3. Test session_reset still works in a chat
4. Commit your updated core files if you have them in version control

**Backup before upgrading:**
```bash
cp -r $HERMES_HOME/hermes-agent $HERMES_HOME/hermes-agent.v0.15.1.bak
```

## License

MIT — see parent repo for details. The skill files (SKILL.md, references/) are MIT-licensed. The patches modify the Hermes Agent core, which retains its original license.