# Memory File Guard

[🇨🇳 中文](README.zh.md) · **English**

---

<p align="center">
  <strong>⚡ Copy this to your Agent → Agent will auto-configure everything:</strong>
</p>

<p align="center">
  <code>Download plugin.yaml and __init__.py from https://github.com/llitgq-byte/HermesBoost/tree/main/auxiliary/memory-file-guard/bundled/plugins/memory-file-guard, place them under $HERMES_HOME/plugins/memory-file-guard/, add memory-file-guard to plugins.enabled in config.yaml, then restart the gateway. This is the Memory File Guard plugin — it intercepts Hermes Agent memory and user file writes, requiring explicit user approval before changes take effect, preventing the AI from silently overwriting persistent memory.</code>
</p>

---

A Hermes Agent plugin that **intercepts memory and user file writes**, requiring explicit user approval before any changes are committed. Designed as a safety net to prevent the AI from silently overwriting your persistent memory.

## Why Does This Exist?

Hermes Agent uses two files — `MEMORY.md` and `USER.md` — to store persistent knowledge across sessions. These files are critical: they shape how the agent behaves, what it remembers about you, and how it responds in future conversations.

The problem? The agent can write to these files at any time, without asking. A single hallucination or poorly reasoned update can corrupt your entire memory store.

**Memory File Guard** solves this by adding a mandatory human-in-the-loop checkpoint. Every write attempt is blocked until you explicitly approve it.

## Core Features

- **Hard intercept** — Plugin-level hook blocks `memory` tool calls before they execute. The agent cannot bypass this.
- **Zero-dependency** — Pure Python standard library. No pip installs, no external packages.
- **Cross-platform** — Works on both macOS (`uchg`/`xattr`) and Linux (`chattr +i`) file locks.
- **Marker-based approval** — A 120-second TTL marker file mechanism ensures approvals are fresh and one-time.
- **Self-contained** — Everything needed is bundled in this directory. Copy to any Hermes instance and it works.

## How It Works

```
Agent wants to write memory
        ↓
   Calls memory tool
        ↓
   Plugin intercepts (pre_tool_call hook)
        ↓
   No approval marker? → BLOCK → Returns instruction to agent
        ↓
   Agent reads current file content
   Agent asks user via clarify() → Shows what will change
        ↓
   User approves → Agent creates marker file + unlocks file
        ↓
   Agent retries memory tool
        ↓
   Plugin detects marker → ALLOWS → Consumes (deletes) marker
        ↓
   Write succeeds → Agent re-locks file
   Agent shows full content + before/after comparison
```

Two layers of protection:

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| **Plugin intercept** | `pre_tool_call` hook | Hard block — memory writes are impossible without approval |
| **OS file lock** (optional) | `uchg` / `chattr +i` | Secondary safety — even if the plugin fails, the OS prevents writes |

## Installation

### Prerequisites

- Hermes Agent v0.15.0+ with plugin support
- Python 3.9+ (standard library only)

### Step 1: Copy the Plugin

```bash
# Determine HERMES_HOME
# Default profile: ~/.hermes
# Sub-agent profile: ~/.hermes/profiles/<name>

PLUGIN_SRC=<this-directory>/bundled/plugins/memory-file-guard
PLUGIN_DST=$HERMES_HOME/plugins/memory-file-guard

cp -r "$PLUGIN_SRC" "$PLUGIN_DST"
```

### Step 2: Enable in config.yaml

Add to your Hermes `config.yaml`:

```yaml
plugins:
  enabled:
    - memory-file-guard
```

### Step 3: Restart Gateway

```bash
hermes gateway restart
# For sub-agents:
# hermes gateway restart --profile <name>
```

### Step 4: Verify

Check your agent log for:

```
plugins.memory-file-guard: memory-file-guard plugin registered (pre_tool_call)
```

## Usage

No special commands needed. The plugin works transparently:

1. **You don't need to do anything differently** — just use Hermes normally.
2. When the agent tries to write `MEMORY.md` or `USER.md`, the plugin blocks it.
3. The agent is instructed to show you the **exact changes** and ask for your approval.
4. You say yes or no. Only your approval allows the write.

### What the Agent Does After Being Blocked

The agent receives a structured instruction set when blocked:

1. Read the current file content
2. Call `clarify()` to show you: action type (add/replace/remove), target file, old content, new content
3. Wait for your confirmation
4. On approval: unlock file → create marker → retry memory call → re-lock file
5. Show you the full updated content with a before/after comparison

### What Happens if You Reject

The agent simply stops. No changes are made. The memory files remain untouched.

## Configuration

### Required

| Setting | Where | Value |
|---------|-------|-------|
| Plugin path | `$HERMES_HOME/plugins/memory-file-guard/` | Must exist |
| config.yaml entry | `plugins.enabled` | Must include `memory-file-guard` |

### Optional: OS-Level File Locks

For defense-in-depth, you can lock the memory files at the OS level. Even if the plugin somehow fails, the OS prevents modification.

**macOS:**

```bash
# Lock
chflags uchg ~/.hermes/memories/MEMORY.md
chflags uchg ~/.hermes/memories/USER.md

# Unlock (agent does this automatically during approved writes)
chflags nouchg ~/.hermes/memories/MEMORY.md
```

**Linux:**

```bash
# Lock
chattr +i ~/.hermes/memories/MEMORY.md
chattr +i ~/.hermes/memories/USER.md

# Unlock
chattr -i ~/.hermes/memories/MEMORY.md
```

### Marker File

| Property | Value |
|----------|-------|
| Path | `/tmp/hermes-memory-guard-approved` |
| Lifetime | 120 seconds |
| Behavior | Consumed (deleted) after first use |

## File Structure

```
memory-file-guard/
├── README.md                          # This file (English)
├── README.zh.md                       # 中文文档
└── bundled/
    └── plugins/
        └── memory-file-guard/
            ├── __init__.py            # Plugin source code
            └── plugin.yaml            # Plugin declaration
```

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| Plugin not loaded | Wrong directory or not enabled in config | Check plugin path and `config.yaml` |
| Write blocked even with marker created | Marker expired (>120s) | Re-create marker with `touch /tmp/hermes-memory-guard-approved` |
| Unlock fails | Insufficient file permissions | Check file ownership |
| Re-lock fails after write | File held by another process | Check for other processes accessing the file |

## License

MIT
