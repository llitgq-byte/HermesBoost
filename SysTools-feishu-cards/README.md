# SysTools-feishu-cards

[🇨🇳 中文](README.zh.md) · **English**

---

<p align="center">
  <strong>⚡ Copy this to your Agent → Agent will auto-configure everything:</strong>
</p>

<p align="center">
  <code>Download all files from https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-feishu-cards/feishu-cards, place them under $HERMES_HOME/skills/Always/feishu-cards/, copy bundled/plugins/feishu-table-card/ to $HERMES_HOME/plugins/feishu-table-card/, add feishu-table-card to plugins.enabled in config.yaml, then restart the gateway. This is the feishu-table-card plugin — auto-converts Markdown tables in Feishu replies to rich interactive cards.</code>
</p>

---

Auto-converts Markdown tables, headings, code blocks, and other rich formatting in Feishu replies into interactive JSON 2.0 cards. No more raw `|...|` pipe text — every table renders as a proper Feishu table component with sorting, pagination, and column auto-sizing.

Two layers of protection: the agent manually calls `send_card.py` when it detects tables in its output, and a plugin hook (`transform_llm_output`) auto-intercepts any completed reply containing tables as a safety net.

## Why Does This Exist?

Feishu's default message format renders Markdown tables as plain pipe text — unreadable. This module solves it at two levels:

1. **Skill** — the agent reads the SKILL.md workflow, detects tables in its output, and calls `send_card.py` to send a properly formatted card.
2. **Plugin** — a `transform_llm_output` hook auto-catches tables in completed replies, even if the agent forgets.

## Core Features

- Full Markdown: tables, headings, code blocks, lists, blockquotes, dividers, links, images
- Zero hardcoded paths — dynamic inference via `feishu_card_utils.py`, works everywhere
- Auto-split — large content splits into sequenced cards
- Fullwidth cleanup — `｜` → `|`, `－` → `-`
- Profile-aware — correct credentials and routing in multi-agent setups
- Cross-platform — pure `pathlib`

## Installation

1. Download all files from `feishu-cards/`
2. Place under `$HERMES_HOME/skills/Always/feishu-cards/`
3. Copy `bundled/plugins/feishu-table-card/` to `$HERMES_HOME/plugins/feishu-table-card/`
4. Add `feishu-table-card` to `plugins.enabled` in `config.yaml`
5. Restart gateway: `hermes restart gateway`

## File Structure

```
SysTools-feishu-cards/
├── README.md                              # This file
├── README.zh.md                           # 中文文档
└── feishu-cards/
    ├── SKILL.md                           # Agent instruction
    ├── references/                         # Detailed guides (9 files)
    ├── templates/                          # Core: send_card.py + utils
    ├── scripts/                            # Install & utilities
    └── bundled/plugins/feishu-table-card/
        ├── __init__.py                    # Plugin hook (transform_llm_output)
        └── plugin.yaml
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Tables show as raw `\|...\|` | Plugin not loaded: `hermes plugins enable feishu-table-card` + restart |
| Cards sent to wrong chat | Check `receive_id` in hook context |
| `ModuleNotFoundError: lark_oapi` | Use `hermes-agent` venv python, not system python |
| `'PluginContext' has no attribute 'register'` | Update plugin to new `register(ctx)` API |
| All agents send to same window | Remove hardcoded IDs from plugin, use env vars only |

## License

MIT
