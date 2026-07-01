# Auxiliary

**🇨🇳 中文** · [English](README.md)

---

> System-level protection, not capability upgrades — reducing repetition, catching mistakes.

Skills and hooks that add a **protective layer** to Hermes Agent — making it easier to use and less prone to repeat the same mistakes. Not about making it smarter; about making it more reliable in practice.

## What Belongs Here

This category is for modules that solve **system-level friction points** — problems that recur across sessions regardless of what task you're working on.

| Type | Description |
|------|-------------|
| **Skills** | Reusable workflows that encode repeatable procedures so the same task is done consistently every time. |
| **Hooks** | Event-driven interceptors that fire before or after system operations, adding validation, safety checks, or automatic corrections. |

A module lands here when it meets two criteria:

1. **It's cross-cutting** — useful regardless of what you're asking Hermes to do.
2. **It's protective** — it prevents a class of mistakes rather than enabling a new capability.

## Modules

### [memory-file-guard](memory-file-guard/README.md)

A Hermes Agent plugin that intercepts memory and user file writes, requiring explicit user approval before any changes are committed. Prevents the AI from silently overwriting persistent memory — the single most damaging type of mistake in an agent system.

**In short:** Every write to `MEMORY.md` and `USER.md` is blocked until you say yes.

## Who Is This For?

Anyone running Hermes Agent who wants **fewer silent regressions**. If you've ever had an agent corrupt your memory files mid-session, these modules exist for you.

## Contributing Pattern

Every module here was born from a real friction point — not a theoretical need. New modules are added the same way: encounter a problem, build a fix, generalize it.

The bar is simple: if it saves you from the same mistake twice, it belongs here.
