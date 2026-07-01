# Memory & User File Guard

[**🇨🇳 中文**](README.zh.md) · **English**

---

A defensive tool for Hermes Agent — ensures memory and user profile files are never modified without explicit approval. Once enabled, every write to `MEMORY.md` or `USER.md` is intercepted. The Agent must request confirmation, and only after approval does the write proceed. After writing, the file is immediately re-locked and a before/after comparison is displayed.

## Key Features

- **Hard Intercept** — Plugin operates at the `pre_tool_call` hook level. Memory writes without a valid approval marker are blocked.
- **User Confirmation Workflow** — Agent loads a guided skill flow: read current content → request approval → create marker → retry → re-lock → show diff.
- **Time-Limited Marker** — 120-second TTL prevents stale approvals from being reused.
- **Cross-Platform** — Pure Python standard library. macOS (uchg/nouchg, xattr) and Linux (chattr+i, chattr-i).
- **Self-Contained** — Zero external dependencies. One skill folder + one plugin folder; copy and enable.
- **Defense in Depth** — Optional OS-level immutable flags (uchg/chattr+i) for double protection.

---

## 1. Description

This tool is a safety net for Hermes. In normal operation, agents write to MEMORY.md and USER.md to retain context. A misconfigured agent, however, can silently overwrite important data. This guard ensures no write happens without a deliberate human confirmation step.

Protected targets:
- `MEMORY.md` — Persistent system memory (facts, preferences, conventions)
- `USER.md` — User profile entries

Each `add`, `replace`, or `remove` operation to these two files triggers the confirmation flow.

---

## 2. Installation

` ` `bash
# 1. Clone the repository
git clone https://github.com/llitgq-byte/HermesBoost.git
cd HermesBoost/auxiliary/memory-file-guard

# 2. Copy the skill to the target Hermes profile
cp -r tools-memory-user-file-in ~/.hermes/skills/Always/

# 3. Copy the plugin to the target Hermes profile
cp -r tools-memory-user-file-in/bundled/plugins/memory-file-guard ~/.hermes/plugins/

# 4. Enable the plugin — edit ~/.hermes/config.yaml
#    (append to the plugins.enabled list)
# plugins:
#   enabled:
#     - memory-file-guard

# 5. Restart the Hermes gateway
hermes gateway restart
` ` `

---

## 3. How It Works

Agent calls memory tool → Plugin checks for approval marker → No marker → BLOCK + guidance → Agent executes skill workflow (read → clarify → approve → create marker → retry → ALLOW → re-lock → diff).

**File lock commands (macOS):**

` ` `bash
# Lock
chflags uchg ~/.hermes/memories/MEMORY.md
chflags uchg ~/.hermes/memories/USER.md

# Unlock
chflags nouchg ~/.hermes/memories/MEMORY.md
chflags nouchg ~/.hermes/memories/USER.md
` ` `

**Marker file:**
- Path: `/tmp/hermes-memory-guard-approved`
- TTL: 120 seconds (one-shot)
- Contains zero write data (no leakage)

---

## 4. How to Use

No special API or command needed. The guard works transparently:

1. User communicates normally.
2. Plugin intercepts memory writes.
3. Agent presents changes via `clarify()`.
4. User approves or rejects.
5. Write proceeds or aborts.

---

## 5. Configuration

**config.yaml:**
` ` `yaml
plugins:
  enabled:
    - memory-file-guard
` ` `

Skill auto-loads when a block occurs. No manual invocation needed.

**Optional hardening (macOS):**
` ` `bash
chflags uchg ~/.hermes/memories/MEMORY.md
chflags uchg ~/.hermes/memories/USER.md
ls -laO ~/.hermes/memories/
` ` `

---

## File Structure

` ` `
tools-memory-user-file-in/
├── README.md / README.zh.md
├── SKILL.md
└── bundled/plugins/memory-file-guard/
    ├── __init__.py
    └── plugin.yaml
` ` `

Zero external dependencies. No API keys. No cloud services.

---

## License

MIT
