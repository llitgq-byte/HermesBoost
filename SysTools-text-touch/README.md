# SysTools-text-touch

> Gateway message interception & routing framework — turn fuzzy short messages into deterministic skill commands.

## What It Does

**Text-Touch** is a Python Plugin framework that hooks into Hermes' `pre_gateway_dispatch` event — the moment a user's message enters the gateway, before it reaches the Agent. By matching short fuzzy messages (`#12 done`, `601138 S`, `茅台 vs 五粮液`) against a list of regex patterns, it rewrites them into unambiguous skill commands. The Agent never has to "guess" intent.

## Why It Exists

When users send short commands (codes, ticker symbols, IDs, status words) the LLM often routes them to the wrong skill, or asks for clarification. Text-Touch makes routing **100% deterministic** — it matches first, rewrites second, Agent executes third.

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
  "Load stock-chromeJJ skill, run diagnosis + 巨潮测评 + F10 panorama on 601138"
Agent: "Clear command, executing."
       → 100% accurate, zero ambiguity
```

## Key Features

- **Zero-dependency Python Plugin** — pure stdlib (`re`, `logging`), no pip installs
- **First-match-wins priority** — longer patterns placed first to avoid truncation
- **3 actions supported**: `rewrite` (transform), `skip` (drop), `allow` (pass through)
- **Per-Agent isolation** — plugins live in `~/.hermes/plugins/` (default) or `~/.hermes/profiles/<name>/plugins/`
- **Hot reload via Gateway restart** — change rules, `hermes gateway restart`, done
- **Built-in walkthrough & maintenance guide** — covers both human and Agent-driven rule edits

## Repository Layout

```
SysTools-text-touch/
├── README.md                          # This file (EN)
├── README.zh.md                       # 中文文档
└── text-touch/
    ├── SKILL.md                       # Full agent instruction (700 lines)
    └── templates/
        ├── __init__.py                # Copyable Plugin template with comments
        └── plugin.yaml                # Copyable Plugin manifest template
```

## Quick Start

The skill ships with copyable templates. From the Agent:

```bash
# 1. Locate your plugins directory
#    - default profile → ~/.hermes/plugins/
#    - sub-Agent profile → ~/.hermes/profiles/<name>/plugins/

# 2. Create plugin dir
mkdir -p ~/.hermes/plugins/my-router

# 3. Copy the templates
cp ~/.hermes/skills/Always/text-touch/templates/* ~/.hermes/plugins/my-router/

# 4. Edit plugin.yaml → set name
# 5. Edit __init__.py → fill in _RULES

# 6. Enable in config.yaml:
#    plugins:
#      enabled:
#        - my-router

# 7. Restart Gateway
hermes gateway restart
```

See `text-touch/SKILL.md` section "第四部分：从零开始的完整 Walkthrough" for a complete worked example (task router: `#12 done` → mark task done, `5` → view task #5).

## Hook Protocol

`pre_gateway_dispatch` is the entry-point hook in Hermes' message pipeline:

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

## Critical: Shell Hook vs Python Plugin

Hermes also has Shell Hooks for `pre_gateway_dispatch`, but **`_parse_response()` only recognizes `pre_tool_call`'s `block` action** — not `rewrite` / `skip`. If you need rewriting, **you MUST use Python Plugin**. See SKILL.md section 7.1 for full details.

## Source

This module is extracted from `~/.hermes/skills/Always/text-touch/` in the live Hermes distribution — the canonical, always-loaded version. The version published here is the same code, the same docs, the same walkthroughs.

## Agent-Ready Prompt

Copy-paste this into a fresh Agent to bootstrap a Text-Touch router:

```
Download all files from https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-text-touch/text-touch/

Inspect SKILL.md in full. Help me build a regex-based message router plugin for my Hermes Agent. Ask me:
  1. Which profile I'm working in (default or sub-Agent)?
  2. Which short messages users currently send that get misrouted?
  3. Which skill should each pattern rewrite to?

Then copy the templates from `templates/` to the right `plugins/` directory, fill in the regex rules following the priority-first ordering (longer patterns before shorter), enable the plugin in config.yaml, and restart the gateway. Verify via `agent.log` that the plugin loaded correctly.
```

## License

Same as parent repo.
