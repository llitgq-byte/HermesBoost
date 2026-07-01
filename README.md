# ⚡ HermesBoost

[**🇨🇳 中文**](README.zh.md) · **English**

---

An **AI capability matrix** — a living collection of skills and tools, continuously explored and iterated upon.

## Environment

- **System:** macOS 26.4.1 (Apple Silicon, arm64)
- **AI Framework:** Hermes Agent v0.15.1

## Architecture

Built on Hermes' **multi-agent architecture**, the system operates through isolated profiles — each with its own skills, memory, cron jobs, and environment. Tasks are dispatched to subagents via delegate_task, enabling parallel and context-isolated execution. HermesBoost is one such profile, dedicated to capability amplification.

## Project Positioning

HermesBoost is a personal exploration space — an ongoing research and development effort aimed at making Hermes genuinely better through practice, not theory.

### Why Does It Exist?

Hermes is powerful, but it's not perfect. In real-world use, there are repetitive mistakes, missing guardrails, and workflows that should be smoother. This project exists to close those gaps.

### What Has Been Built?

- **Skills** — Reusable procedural modules that Hermes loads on demand. Each skill encodes a repeatable workflow (e.g., how to interact with an API, how to format output for a specific platform) so that the same task is done consistently every time.
- **Hooks** — Event-driven interceptors that fire before or after system operations, adding validation, safety checks, or automatic corrections without modifying core logic.

Every piece is originally crafted. Nothing is copied from a template or generated in bulk. Each module exists because a real friction point was encountered and solved.

## Categories

| Category | Description |
|----------|-------------|
| **[Auxiliary](auxiliary/)** | Skills and hooks that add a protective layer to Hermes — making it easier to use and less prone to repeat the same mistakes. [中文 →](auxiliary/README.zh.md) |
| **[Finance](finance/)** | Stock research and analysis workflows — from pre-market briefing and intraday tracking to post-trade review — tailored to personal holdings and investment strategies. [中文 →](finance/README.zh.md) |
| **[Life](life/)** | Everyday intelligence solutions. Currently pending development — to be expanded over time. [中文 →](life/README.zh.md) |

### Active Modules

| Module | Category | What It Does |
|--------|----------|-------------|
| **[Memory File Guard](auxiliary/memory-file-guard/)** | Auxiliary | Intercepts memory/user file writes, requires explicit user approval before allowing changes. Prevents silent memory corruption. [中文 →](auxiliary/memory-file-guard/README.zh.md) |

## The Closed-Loop Philosophy

The ideal is a **closed-loop workflow**: the output of one stage feeds directly into the input of the next, with no manual handoffs in between.

Reality today: most processes still require manual steps. The results are functional, but not yet autonomous.

What we are really exploring is this boundary — where manual ends and automatic begins — and how far we can push it, one module at a time.

## Directory Structure

hermesboost/
├── README.md                              # English documentation
├── README.zh.md                           # 中文文档
├── auxiliary/
│   ├── README.md                          # Auxiliary overview (EN)
│   ├── README.zh.md                       # Auxiliary 概述（中文）
│   └── memory-file-guard/                 # Memory & User file write protection
│       ├── README.md                      # Module docs (EN)
│       ├── README.zh.md                   # 模块文档（中文）
│       └── bundled/plugins/memory-file-guard/
│           ├── __init__.py                 # Plugin source
│           └── plugin.yaml                 # Plugin declaration
├── finance/
│   ├── README.md                          # Finance overview (EN)
│   └── README.zh.md                       # 金融概述（中文）
└── life/
    ├── README.md                          # Life overview (EN)
    └── README.zh.md                       # 生活概述（中文）

## Roadmap

| Phase | Status | Focus |
|-------|--------|-------|
| Auxiliary Foundation | In Progress | System-level skills and hooks |
| Finance Pipeline | Planned | Stock research workflows |
| Life Tools | On Hold | Everyday intelligence |
| Further Exploration | Open | Wherever the gaps appear |

The journey itself is the product. Every component is originally crafted.
