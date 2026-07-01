⚡ HermesBoost

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

Every piece is originally crafted. Nothing is copied from a template or generated in bulk. Each module exists because a real friction point was encountered — and solved.

## Categories

| Category | Description |
|----------|-------------|
| **Auxiliary** | Skills and hooks that add a protective layer to Hermes — making it easier to use and less prone to repeat the same mistakes. Not about making it "smarter"; about making it more reliable in practice. |
| **Finance** | Stock research and analysis workflows — from pre-market briefing and intraday tracking to post-trade review — tailored to personal holdings and investment strategies. |
| **Life** | Everyday intelligence solutions. Currently pending development — to be expanded over time. |

## The Closed-Loop Philosophy

The ideal is a **closed-loop workflow**: the output of one stage feeds directly into the input of the next, with no manual handoffs in between.

Reality today: most processes still require manual steps. The results are functional, but not yet autonomous.

What we're really exploring is this boundary — where manual ends and automatic begins — and how far we can push it, one module at a time.

## Roadmap

| Phase | Status | Focus |
|-------|--------|-------|
| Auxiliary Foundation | 🔄 In Progress | System-level skills and hooks |
| Finance Pipeline | 📋 Planned | Stock research workflows |
| Life Tools | ⏸️ On Hold | Everyday intelligence |
| Further Exploration | 🔮 Open | Wherever the gaps appear |

The journey itself is the product. Every component is originally crafted.[🇬🇧 English](#english) · [🇨🇳 中文](#chinese)

---

<a name="english"></a>

> HermesBoost is not a collection of isolated tools. It is an **ecosystem of AI capabilities** designed to amplify, connect, and orchestrate how AI augments real work and life.

## What Is HermesBoost?

Every module here is built with one principle: **nothing stands alone**. Skills are designed to pass signals, share context, and trigger one another — moving toward a state where the whole system operates as a self-reinforcing loop.

## Categories

| Category | Description |
|----------|-------------|
| **Orchestration** | System-level capabilities that make the AI engine itself more reliable, efficient, and less error-prone. |
| **Finance** | End-to-end stock research and collaboration — from pre-market intelligence through post-trade review. |
| **Life** | Intelligent solutions for everyday scenarios, proving that AI's value extends well beyond the desk. |

## The Closed-Loop Philosophy

The north star is **closure**: intelligence flows from one module to the next without manual handoffs, and the output of one stage becomes the informed input of the next.

We are not there yet. But we are building toward it — methodically, iteratively, and in the open.

## Roadmap

| Phase | Status | Focus |
|-------|--------|-------|
| Foundation | 🔄 In Progress | System-level orchestration skills |
| Finance | 📋 Planned | Stock research pipeline |
| Life | 📋 Planned | Everyday intelligence |
| Integration | 🔮 Vision | Full closed-loop connectivity |

<br>

---

<a name="chinese"></a>

> HermesBoost 不是孤立工具的合集，而是一个**能力生态**——旨在增强、连通并编排 AI 如何赋能真实的工作与生活。

## 项目定位

这里的每一个模块都遵循一个原则：**没有什么是孤岛**。Skills 之间可以传递信号、共享上下文、彼此触发——推动整个系统朝着自我增强的闭环演进。

## 三大类别

| 类别 | 描述 |
|------|------|
| **Orchestration（编排层）** | 系统级辅助能力，让 AI 引擎本身更稳定、更聪明、更少犯错。 |
| **Finance（金融层）** | 股票研究与协同的全链路智能化——从盘前、盘中到复盘。 |
| **Life（生活层）** | 日常场景的智能化方案，证明 AI 的价值远不止于工作。 |

## 闭环理念

北极星是**闭环**：智能在模块之间自动流转，无需人工传递，一个阶段的输出成为下一个阶段的明智输入。

我们还未抵达。但我们正在朝着它，逐步地、迭代地、公开地构建。

## 路线图

| 阶段 | 状态 | 聚焦 |
|------|------|------|
| 基础建设 | 🔄 进行中 | 系统级编排能力 |
| 金融层 | 📋 计划中 | 股票研究管线 |
| 生活层 | 📋 计划中 | 日常智能 |
| 全链路整合 | 🔮 远景 | 完整闭环连通 |

<br>

*Every component is original-crafted. This log documents a journey — not a finished product.*

*所有内容均为原创创建。这里记录的是一段旅程，不是一件成品。*An **AI capability matrix** — a living system of interconnected skills, continuously evolving toward a fully orchestrated closed-loop.</｜DSML｜parameter>An **AI capability matrix** — a living system of interconnected skills, continuously evolving toward a fully orchestrated closed-loop.

## What Is HermesBoost?

HermesBoost is not a collection of isolated tools. It is an **ecosystem of AI capabilities** designed to amplify, connect, and orchestrate how AI augments real work and life.

Every module here is built with one principle: **nothing stands alone**. Skills are designed to pass signals, share context, and trigger one another — moving toward a state where the whole system operates as a self-reinforcing loop.

## Categories

- **Orchestration** — System-level capabilities that make the AI engine itself more reliable, efficient, and less error-prone.
- **Finance** — End-to-end stock research and collaboration, from pre-market intelligence through post-trade review.
- **Life** — Intelligent solutions for everyday scenarios, proving that AI's value extends well beyond the desk.

## The Closed-Loop Philosophy

The north star is **closure**: intelligence flows from one module to the next without manual handoffs, and the output of one stage becomes the informed input of the next.

We are not there yet. But we are building toward it — methodically, iteratively, and in the open.

## Roadmap

| Phase | Status | Focus |
|-------|--------|-------|
| Foundation | 🔄 In Progress | System-level orchestration skills |
| Finance | 📋 Planned | Stock research pipeline |
| Life | 📋 Planned | Everyday intelligence |
| Integration | 🔮 Vision | Full closed-loop connectivity |


<div id="zh">

---

## 🧩 项目定位

HermesBoost 不是孤立工具的合集，而是一个**能力生态**——旨在增强、连通并编排 AI 如何赋能真实的工作与生活。

这里的每一个模块都遵循一个原则：**没有什么是孤岛**。Skills 之间可以传递信号、共享上下文、彼此触发——推动整个系统朝着自我增强的闭环演进。

## 三大类别

- **Orchestration（编排层）** — 系统级辅助能力，让 AI 引擎本身更稳定、更聪明、更少犯错
- **Finance（金融层）** — 股票研究与协同的全链路智能化，从盘前、盘中到复盘
- **Life（生活层）** — 日常场景的智能化方案，证明 AI 的价值远不止于工作

## 闭环理念

北极星是**闭环**：智能在模块之间自动流转，无需人工传递，一个阶段的输出成为下一个阶段的明智输入。

我们还未抵达。但我们正在朝着它，逐步地、迭代地、公开地构建。

## 路线图

| 阶段 | 状态 | 聚焦 |
|------|------|------|
| 基础建设 | 🔄 进行中 | 系统级编排能力 |
| 金融层 | 📋 计划中 | 股票研究管线 |
| 生活层 | 📋 计划中 | 日常智能 |
| 全链路整合 | 🔮 远景 | 完整闭环连通 |

</div>


*Every component is original-crafted. This log documents a journey — not a finished product.*

*所有内容均为原创创建。这里记录的是一段旅程，不是一件成品。*
