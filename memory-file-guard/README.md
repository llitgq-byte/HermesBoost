# memory-file-guard

[🇨🇳 中文](README.zh.md) · **English**

---

<p align="center">
  <strong>⚡ Copy this to your Agent → Agent will auto-configure everything:</strong>
</p>

<p align="center">
  <code>Download all files from https://github.com/llitgq-byte/HermesBoost/tree/main/memory-file-guard/memory-file-guard, place them under $HERMES_HOME/skills/Always/memory-file-guard/, copy bundled/plugins/memory-file-guard/ to $HERMES_HOME/plugins/memory-file-guard/, add memory-file-guard to plugins.enabled in config.yaml, then restart the gateway. This is the memory-file-guard plugin — intercepts memory/user file writes and requires explicit user confirmation before allowing changes.</code>
</p>

---

Protects Hermes persistent memory files (`MEMORY.md`, `USER.md`) from silent AI overwrites. When the agent attempts to write to memory or user files, a plugin hook (`pre_tool_call`) blocks the write and forces a user confirmation flow — no changes happen without explicit approval.

## Why Does This Exist?

Hermes agents use the `memory` tool to save persistent notes across sessions. Without protection, an agent can silently overwrite, corrupt, or hallucinate incorrect information into your memory files — and you'd never know. This module adds a mandatory human-in-the-loop checkpoint before any memory write is allowed.

## Core Features

- **Hard intercept** — Plugin hook `pre_tool_call` blocks memory/user writes at the gateway level, impossible for the agent to bypass
- **Confirmation flow** — Agent reads current content → asks user via `clarify()` → user approves → write proceeds
- **File locking** (optional) — Secondary `uchg`/`chattr +i` lock for double protection
- **Content diff** — After write, automatically shows before/after comparison
- **Self-contained** — Plugin bundled inside the skill directory, copy to any Hermes instance and it works
- **Cross-platform** — Pure Python standard library, macOS/Linux compatible

## How It Works

```
Agent calls memory tool → Plugin intercepts (no approval marker)
  → BLOCK → returns confirmation instructions
  → Agent reads current file → asks user
  → User confirms → Agent creates marker file → retries memory tool
  → Plugin detects marker → ALLOW → deletes marker → write succeeds
  → Agent re-locks file → outputs content + diff
```

## Installation

1. **Download** — Get all files from `memory-file-guard/memory-file-guard/`
2. **Copy skill** — Place under `$HERMES_HOME/skills/Always/memory-file-guard/`
3. **Copy plugin** — Copy `bundled/plugins/memory-file-guard/` to `$HERMES_HOME/plugins/memory-file-guard/`
4. **Enable** — Add `memory-file-guard` to `plugins.enabled` in `config.yaml`
5. **Restart** — `hermes restart gateway`

## File Structure

```
memory-file-guard/
├── README.md                              # This file (English)
├── README.zh.md                           # 中文文档
└── memory-file-guard/                     # Skill content (same name)
    ├── SKILL.md                           # Agent instruction
    ├── references/
    │   └── github-release-checklist.md    # Release checklist
    └── bundled/plugins/memory-file-guard/
        ├── __init__.py                    # Plugin source (pre_tool_call hook)
        └── plugin.yaml                    # Plugin metadata
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Memory writes not blocked | Plugin not loaded: `hermes plugins enable memory-file-guard` + restart |
| Agent stuck in confirmation loop | Marker file not created — check `__hermes_memory_approved` exists in temp dir |
| Permission denied on lock | File already has `uchg` flag: `chflags nouchg <file>` |

## License

MIT
