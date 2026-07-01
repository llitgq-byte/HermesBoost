# ⚡ HermesBoost

**🇨🇳 中文** · [**English**](README.md)

---

一套**AI 能力矩阵**——由 skill 和工具组成的持续探索与迭代的集合。

## 系统环境

- **系统：** macOS 26.4.1 (Apple Silicon, arm64)
- **AI 框架：** Hermes Agent v0.15.1

## 架构

基于 Hermes **多 Agent 架构**构建。系统通过隔离的 profile 运行——每个 profile 拥有独立的 skill、memory、cron 和环境变量。任务通过 delegate_task 分发给子 Agent 执行，实现并行且上下文隔离的处理。HermesBoost 是其中一个 profile，专注于能力增强。

## 项目定位

HermesBoost 是一个个人探索空间——一个持续的研究与开发项目，目标是通过实践让 Hermes 真正变得更好，而非停留在理论层面。

### 为什么存在？

Hermes 很强大，但并不完美。在实际使用过程中，会出现重复性错误、缺少防护机制、以及本可以更顺畅的工作流。这个项目的存在就是为了弥补这些不足。

### 目前创建了什么？

- **Skill（技能）**——Hermes 按需加载的可复用流程模块。每个 skill 编码了一套可重复的工作方式（例如如何与某个 API 交互、如何为特定平台格式化输出），从而确保每次执行同一任务时都能保持一致。
- **Hook（钩子）**——事件驱动的拦截器，在系统操作之前或之后触发，添加验证、安全检查或自动修正，而无需修改核心逻辑。

每一件都是原创创建。没有从模板复制，也没有批量生成。每一个模块的出现，都是因为遇到了一个真实的痛点——并解决了它。

## 活跃模块

| 模块 | 功能 |
|------|------|
| **[SysTools-memory-file-guard](SysTools-memory-file-guard/)** | 拦截 memory/user 文件写入，要求用户明确批准后才允许更改。防止 AI 静默覆写你的持久记忆。[English →](SysTools-memory-file-guard/README.md) |
| **[SysTools-feishu-cards](SysTools-feishu-cards/)** | 自动将飞书回复中的 Markdown 表格、标题、代码块转换为飞书 interactive JSON 2.0 卡片。双保险（Agent + Plugin）。[English →](SysTools-feishu-cards/README.md) |
| **[SysTools-feishu-bitable](SysTools-feishu-bitable/)** | 飞书多维表格通用 API 指南，附带纯 Python Helper 脚本。16 个已记录坑点，零依赖。[English →](SysTools-feishu-bitable/README.md) |
| **[SysTools-feishu-calendar](SysTools-feishu-calendar/)** | 通过飞书 API 管理共享日历日程（创建/查询/删除）。CLI 工具，一次性初始化后持久化状态。[English →](SysTools-feishu-calendar/README.md) |
| **[SysTools-chrome-play](SysTools-chrome-play/)** | 通过 CDP 控制本地 Chrome 浏览器。完整启动指南、SPA 模式、CodeMirror 6 编辑、13 个坑点。[English →](SysTools-chrome-play/README.md) |
| **[SysTools-text-touch](SysTools-text-touch/)** | Gateway 入口消息拦截/路由框架。基于正则的 pre-dispatch hook，将模糊短消息改写为确定性 skill 指令。零依赖 Python Plugin。[English →](SysTools-text-touch/README.md) |
| ⚠️ **[SysTools-session-reset](SysTools-session-reset/)** | 延迟 session context 重置（回复投递完成后）。**修改 Hermes 核心代码**（5 个文件）—— 阅读警告。测试版本 v0.15.1。[Warning →](SysTools-session-reset/README.md) |

> 💡 从模块页面复制 prompt → 粘贴给你的 Agent → 自动配置完成。

## 闭环理念

理想状态是**闭环工作流**：一个阶段的输出直接成为下一个阶段的输入，中间无需人工传递。

而现实是：目前大多数流程仍然需要人工介入。成果是可用的，但还谈不上自动化。

我们真正在探索的是这个边界——人工在哪里结束、自动从哪里开始——以及我们能一次一个模块地把它推多远。

## 目录结构

```
hermesboost/
├── README.md                              # 英文文档
├── README.zh.md                           # 中文文档
├── SysTools-memory-file-guard/             # Memory & User 文件写入保护
│   ├── README.md                          # 公开文档（英文）
│   ├── README.zh.md                       # 公开文档（中文）
│   └── memory-file-guard/                  # Skill 内容
│       ├── SKILL.md                        # Agent 指令
│       ├── references/
│       └── bundled/plugins/memory-file-guard/
│           ├── __init__.py                  # 插件源码
│           └── plugin.yaml                  # 插件声明
├── SysTools-feishu-cards/                  # Markdown → 飞书交互式卡片
│   ├── README.md                          # 公开文档（英文）
│   ├── README.zh.md                       # 公开文档（中文）
│   └── feishu-cards/                      # Skill 内容
│       ├── SKILL.md                        # Agent 指令
│       ├── references/
│       ├── templates/
│       ├── scripts/
│       └── bundled/plugins/feishu-table-card/
│           ├── __init__.py                  # 插件钩子
│           └── plugin.yaml
├── SysTools-feishu-bitable/                 # 飞书多维表格 API 指南 + 辅助脚本
│   ├── README.md                          # 公开文档（英文）
│   ├── README.zh.md                       # 公开文档（中文）
│   └── feishu-bitable/                    # Skill 内容
│       ├── SKILL.md                        # Agent 指令
│       └── scripts/
│           └── feishu_bitable.py            # Python 辅助脚本（urllib，零依赖）
├── SysTools-feishu-calendar/                 # 飞书日历管理
│   ├── README.md                          # 公开文档（英文）
│   ├── README.zh.md                       # 公开文档（中文）
│   └── feishu-calendar/                   # Skill 内容
│       ├── SKILL.md                        # Agent 指令
│       └── scripts/
│           └── calendar_tool.py             # CLI 工具（依赖 requests）
├── SysTools-chrome-play/                      # 通过 CDP 控制本地 Chrome 浏览器
│   ├── README.md                          # 公开文档（英文）
│   ├── README.zh.md                       # 公开文档（中文）
│   └── chrome-play/                       # Skill 内容
│       ├── SKILL.md                        # Agent 指令
│       ├── references/                     # 技术参考文档（5 篇）
│       └── templates/                      # GitHub Profile README 模板
├── SysTools-text-touch/                       # Gateway 入口消息拦截/路由框架
│   ├── README.md                          # 公开文档（英文）
│   ├── README.zh.md                       # 公开文档（中文）
│   └── text-touch/                        # Skill 内容
│       ├── SKILL.md                        # Agent 指令（700 行）
│       └── templates/                      # 可复制的 Plugin 模板
│           ├── __init__.py                  # 含正则规则的 Plugin 入口
│           └── plugin.yaml                  # Plugin 清单
├── SysTools-session-reset/                    # ⚠️ 延迟 session 重置（修改 Hermes 核心代码）
│   ├── README.md                          # 公开文档（英文，含警告框）
│   ├── README.zh.md                       # 公开文档（中文，含警告框）
│   └── session-reset/                     # Skill 内容（修改 Hermes 核心）
│       ├── SKILL.md                        # Agent 指令（309 行，无精确行号）
│       └── references/                    # 3 个文档 — 修改指南 + 工具源码
│           ├── README.md                    # 系统级介绍 + 启用/关闭方法
│           ├── patches.md                   # 5 个核心文件的完整 patch diff
│           └── session_reset_tool.py        # 新工具源码（90 行）
```

## 路线图

| 阶段 | 状态 | 聚焦 |
|------|------|------|
| 防护与守卫 | ✅ 已发布 | 记忆文件保护 |
| 平台集成 | ✅ 已发布 | 飞书卡片渲染、多维表格 API |
| 后续探索 | 🔮 开放 | 哪里不足就补哪里 |

<br>

*探索本身就是成果。所有内容均为原创创建。*
