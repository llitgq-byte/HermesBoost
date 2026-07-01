# SysTools-text-touch

[🇨🇳 中文](README.zh.md) · **English**

---

<p align="center">
  <strong>⚡ Copy this to your Agent → Agent will auto-configure everything:</strong>
</p>

<p align="center">
  <code>Download all files from https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-text-touch/text-touch/. Read SKILL.md in full. Help me build a regex-based message router plugin for my Hermes Agent. Ask me: (1) Which profile I'm working in (default or sub-Agent)? (2) Which short messages users currently send that get misrouted? (3) Which skill should each pattern rewrite to? Then copy the templates from templates/ to the right plugins/ directory, fill in the regex rules following the priority-first ordering (longer patterns before shorter), enable the plugin in config.yaml, and restart the gateway. This is the Text-Touch skill — gateway message interception/routing framework that rewrites deterministic short messages into explicit skill commands.</code>
</p>

---

## Why Does This Exist?

When users send short commands (codes, ticker symbols, IDs, status words) via Feishu, the LLM often routes them to the wrong skill or asks for clarification. Text-Touch makes routing **100% deterministic** — it matches first, rewrites second, Agent executes third.

### Without Text-Touch

```
User: 601138 S
Agent: "Hmm, 601138 is a number, S is a letter… what should I do?"
       → May guess wrong, or ask for clarification
```

### With Text-Touch

```
User: 601138 S
Text-Touch matches → rewrites to:
  "Load stock-diagnosis skill, run diagnosis on 601138"
Agent: "Clear command, executing."
       → 100% accurate, zero ambiguity
```

## Core Features

- **Zero-dependency Python Plugin** — pure stdlib (`re`, `logging`), no pip installs
- **First-match-wins priority** — longer patterns placed first to avoid truncation
- **3 actions supported**: `rewrite` (transform), `skip` (drop), `allow` (pass through)
- **Per-Agent isolation** — plugins live in `$HERMES_HOME/plugins/` (default) or `$HERMES_HOME/profiles/<name>/plugins/`
- **Hot reload via Gateway restart** — change rules, `hermes gateway restart`, done
- **Built-in walkthrough & maintenance guide** — covers both human and Agent-driven rule edits
- **Copyable templates** — `__init__.py` + `plugin.yaml` ready to drop in
- **700-line SKILL.md** — complete reference (11 sections) with task-router detailed walkthrough

## How It Works

```
Platform WebSocket receive
    ↓
Gateway (gateway/run.py)
    ↓
┌──────────────────────────────────┐
│ pre_gateway_dispatch hook        │  ← Text-Touch intercepts here
│   Receives MessageEvent          │
│   Returns rewrite/skip/allow     │
└──────────────────────────────────┘
    ↓
Agent (LLM + tools)
    ↓
┌──────────────────────────────────┐
│ transform_llm_output hook        │  ← Feishu cards / etc. intercept here
└──────────────────────────────────┘
    ↓
Platform reply to user
```

Return values:

| Return | Effect |
|--------|--------|
| `None` | Pass through unchanged |
| `{"action": "rewrite", "text": "..."}` | Replace message text, continue |
| `{"action": "skip", "reason": "..."}` | Drop message, Agent never sees it |

## Installation

### Step 1: Locate your plugins directory

```bash
# Default profile
$HERMES_HOME/plugins/

# Sub-Agent profile
$HERMES_HOME/profiles/<your-profile>/plugins/
```

### Step 2: Create plugin directory

```bash
mkdir -p $HERMES_HOME/plugins/my-router
```

### Step 3: Copy templates

```bash
# Download from GitHub first, then:
cp SysTools-text-touch/text-touch/templates/* $HERMES_HOME/plugins/my-router/
```

### Step 4: Edit plugin.yaml

```yaml
name: my-router
version: "1.0.0"
description: "My custom message router"
enabled: true
```

### Step 5: Edit `__init__.py`

Open `$HERMES_HOME/plugins/my-router/__init__.py` and fill in your regex rules:

```python
import re
import logging

logger = logging.getLogger(__name__)

_RULES = [
    # (regex_pattern, action, replacement_text_or_reason)
    # Longer patterns first!
    (r"^(\d{6})\s*S$", "rewrite", "Load stock-diagnosis skill, run diagnosis on \1"),
    (r"^#(\d+)\s+done$", "rewrite", "Mark task #\1 as done"),
    (r"^(done|finished)$", "rewrite", "Mark current task as complete"),
    (r"^(weather|雨|晴)$", "skip", "Ignored by text-touch"),
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
                result["reason"] = replacement or "Matched filter rule"
            logger.info(f"[my-router] '{message}' → {result}")
            return result
    return None

def pre_gateway_dispatch(event: dict) -> dict | None:
    message = event.get("message", "")
    return _process(message)
```

### Step 6: Enable plugin in config.yaml

```yaml
# config.yaml
plugins:
  enabled:
    - my-router
```

### Step 7: Restart Gateway

```bash
hermes gateway restart
```

### Step 8: Verify

```bash
# Check agent.log for plugin load confirmation
grep "text-touch\|my-router" $HERMES_HOME/logs/agent.log

# Send a test short message in Feishu — Agent should execute the rewritten command
```

## File Structure

```
SysTools-text-touch/
├── README.md                              ← This file (EN, with ⚡ prompt)
├── README.zh.md                           ← 中文文档（含 ⚡ 提示）
└── text-touch/
    ├── SKILL.md                           ← Full agent instruction (700 lines, 11 sections)
    └── templates/
        ├── __init__.py                    ← Copyable Plugin template with comments
        └── plugin.yaml                     ← Copyable Plugin manifest template
```

## Critical: Shell Hook vs Python Plugin

Hermes also has Shell Hooks for `pre_gateway_dispatch`, but **`_parse_response()` only recognizes `pre_tool_call`'s `block` action** — not `rewrite` / `skip`. If you need rewriting, **you MUST use Python Plugin**. See SKILL.md section 7.1 for full details.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Plugin not loading | (1) Check `$HERMESS_HOME/plugins/my-router/__init__.py` exists (2) Check `config.yaml` has `plugins.enabled: [my-router]` (3) Restart gateway (4) Check `agent.log` for import errors |
| Plugin loaded but no rewriting | (1) Check regex patterns match your actual messages (2) Ensure patterns are ordered longest-first (3) Check `agent.log` for `[my-router]` debug logs (4) Verify `pre_gateway_dispatch` is exported from `__init__.py` |
| `rewrite` action not working | Shell Hook cannot do `rewrite` — must be Python Plugin. Verify `_process` returns `{"action": "rewrite", "text": "..."}` and the function is registered as `pre_gateway_dispatch` |
| Rules not updating after edits | Restart gateway — Plugin code is loaded at startup, not hot-reloaded |
| Multiple plugins conflict | First-match-wins across plugins. Higher-priority plugins (longer patterns) should be loaded first |

## Upgrade & Maintenance

Text-Touch lives in `$HERMES_HOME/skills/Always/text-touch/` — it's part of your local Hermes distribution. The GitHub version is a snapshot for sharing.

To update:
1. Pull latest from GitHub
2. Replace `$HERMES_HOME/skills/Always/text-touch/` with the new files
3. Re-copy templates if you've customized them
4. Restart gateway

## License

MIT — see parent repo for details.