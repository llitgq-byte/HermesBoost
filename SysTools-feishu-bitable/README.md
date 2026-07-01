# SysTools-feishu-bitable

[🇨🇳 中文](README.zh.md) · **English**

---

<p align="center">
  <strong>⚡ Copy this to your Agent → Agent will auto-configure everything:</strong>
</p>

<p align="center">
  <code>Download all files from https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-feishu-bitable/feishu-bitable, place them under $HERMES_HOME/skills/Always/tools-feishu-bitable/, then restart the gateway. This is the Feishu Bitable skill — a universal API guide for Feishu Bitable (multidimensional tables) with a pure-Python helper script (urllib, no deps).</code>
</p>

---

A universal **Feishu Bitable (多维表格) API guide** for Hermes Agent. Covers authentication, CRUD operations, field types, pagination, relation fields, and 16 documented pitfalls — plus a ready-to-use Python helper script.

## Why Does This Exist?

Feishu's Bitable API has many undocumented quirks: Number fields return strings but require numeric input, server-side filters silently fail, PATCH returns 404 on records, and credential handling is tricky under Hermes's keyword filtering. This skill encapsulates battle-tested patterns so every Agent avoids these traps.

## Core Features

- **Complete API reference** — all 7 endpoints (list tables/fields/records, get/create/update/delete records) with request/response formats
- **Field type cheat sheet** — 10 field types with correct read/write formats (especially the asymmetric Number type)
- **Pagination helper** — auto-pagination `list_all_records()` function
- **Relation fields** — proper handling of Type 7 objects vs plain IDs
- **16 documented pitfalls** — from permission errors to Unicode encoding issues
- **Python helper script** — zero-dependency `feishu_bitable.py` with all CRUD operations + `find_records()` local filter

## How It Works

1. Agent reads `SKILL.md` to understand Feishu Bitable API patterns
2. For Python-based operations, Agent uses `scripts/feishu_bitable.py` as a library
3. Credentials are injected via the two-step method (terminal → `/tmp/feishu_creds.json` → script reads JSON) to bypass Hermes keyword filtering
4. All operations use `urllib.request` — no `requests` or other external dependencies needed

## Installation

1. Download all files from the [`feishu-bitable/`](https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-feishu-bitable/feishu-bitable) directory
2. Place them under `$HERMES_HOME/skills/Always/tools-feishu-bitable/`
3. Ensure `FEISHU_APP_ID` and `FEISHU_APP_SECRET` are set in your profile's `.env`
4. Restart the gateway

## File Structure

```
SysTools-feishu-bitable/
├── README.md                         ← This file
├── README.zh.md                      ← 中文文档
└── feishu-bitable/
    ├── SKILL.md                      ← Agent instructions (API guide + pitfalls)
    └── scripts/
        └── feishu_bitable.py          ← Python helper (urllib, no deps)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Permission error `99991672` | Enable `bitable:app` scope in Feishu Developer Console (for app identity) |
| Server-side filter returns empty | Don't use server-side filter; use `list_all_records()` + local filtering |
| `NumberFieldConvFail` (1254061) | Number fields: write `int`/`float`, never `str` from API response |
| `PATCH` returns 404 | Use `PUT` for record updates |
| Hermes filters `SECRET` keyword | Use two-step credential extraction (terminal → JSON → script) |
| `InvalidSort` with Chinese params | Skip server-side sort; use Python `.sort()` locally |

## License

MIT
