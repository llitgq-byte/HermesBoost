# SysTools-feishu-calendar

[🇨🇳 中文](README.zh.md) · **English**

---

<p align="center">
  <strong>⚡ Copy this to your Agent → Agent will auto-configure everything:</strong>
</p>

<p align="center">
  <code>Download all files from https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-feishu-calendar/feishu-calendar, place them under $HERMES_HOME/skills/Always/tools-feishu-calendar/, ensure the <code>requests</code> package is installed (<code>pip install requests</code>), then restart the gateway. This is the Feishu Calendar skill — manage shared calendar events (create/list/delete) via Feishu API, with one-time initialization and persistent state.</code>
</p>

---

A **Feishu Calendar management skill** for Hermes Agent. Provides a CLI tool to create, list, and delete events on a shared calendar managed by your Feishu app. One-time setup, then all agents share the same calendar.

## Why Does This Exist?

Hermes agents need a reliable way to manage calendar events — reminders, meetings, scheduled tasks — through Feishu's calendar API. The initialization flow handles the tricky parts (calendar creation, ACL authorization, chat member discovery) so the agent only needs to call simple CLI commands.

## Core Features

- **One-time initialization** — creates an app-owned calendar, auto-discovers user via chat_id, sets ACL permissions
- **CLI-based operations** — `status`, `init`, `list`, `create`, `delete`, `reset` subcommands
- **Persistent state** — calendar ID and user info saved to `calendar_state.json` (auto-managed)
- **Flexible time input** — specify duration by minutes or explicit end time
- **Multi-source chat_id discovery** — checks env vars, `.env` file, and session context

## How It Works

1. On first use, Agent asks user for calendar name and chat_id
2. `init` command creates the calendar, finds the user via chat members API, and grants ACL access
3. Subsequent operations (list/create/delete) use the persisted `calendar_state.json`
4. All commands return JSON for easy Agent parsing

## Installation

1. Download all files from the [`feishu-calendar/`](https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-feishu-calendar/feishu-calendar) directory
2. Place them under `$HERMES_HOME/skills/Always/tools-feishu-calendar/`
3. Install the `requests` dependency: `pip install requests`
4. Ensure `FEISHU_APP_ID` and `FEISHU_APP_SECRET` are set in your profile's `.env`
5. Restart the gateway

## File Structure

```
SysTools-feishu-calendar/
├── README.md                         ← This file
├── README.zh.md                      ← 中文文档
└── feishu-calendar/
    ├── SKILL.md                      ← Agent instructions
    └── scripts/
        └── calendar_tool.py           ← CLI tool (depends on requests)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `execute_code` path resolution fails | Use absolute paths instead of `~` |
| Init fails with "获取聊天成员失败" | Enable `im:chat:readonly` + `im:chat` scopes (app identity) in Feishu Developer Console |
| Permission error | Enable `calendar:calendar` and `calendar:calendar:create` scopes (app identity) |

## License

MIT
