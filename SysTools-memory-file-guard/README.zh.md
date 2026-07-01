# memory-file-guard

**🇨🇳 中文** · [English](README.md)

---

<p align="center">
  <strong>⚡ 复制以下内容给你的 Agent → Agent 自动配置一切：</strong>
</p>

<p align="center">
  <code>下载 https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-memory-file-guard/memory-file-guard 下的全部文件，放入 $HERMES_HOME/skills/Always/memory-file-guard/，将 bundled/plugins/memory-file-guard/ 复制到 $HERMES_HOME/plugins/memory-file-guard/，在 config.yaml 的 plugins.enabled 中添加 memory-file-guard，然后重启 gateway。这是 memory-file-guard 插件——拦截 memory/user 文件写入，要求用户明确确认后才允许更改。</code>
</p>

---

保护 Hermes 持久记忆文件（`MEMORY.md`、`USER.md`）不被 AI 静默覆写。当 Agent 尝试通过 `memory` 工具写入这些文件时，插件钩子（`pre_tool_call`）会自动拦截，强制走用户确认流程——没有你的明确批准，任何写入都不会发生。

## 为什么需要？

Hermes Agent 使用 `memory` 工具保存跨会话的持久笔记。没有保护的话，Agent 可能静默地覆写、篡改或幻觉式地往你的记忆文件写入错误信息——而你完全不知道。本模块在每次 memory 写入前加入必须的人工确认环节。

## 核心特性

- **硬拦截** — 插件钩子 `pre_tool_call` 在 gateway 层面阻止 memory/user 写入，Agent 无法绕过
- **确认流程** — Agent 读取当前内容 → 通过 `clarify()` 询问用户 → 用户批准 → 写入执行
- **文件锁**（可选）— 额外的 `uchg`/`chattr +i` 锁，双重保险
- **内容对比** — 写入后自动展示新旧内容 diff
- **自包含** — Plugin 打包在 skill 目录内，复制到任何 Hermes 实例即可使用
- **跨平台** — 纯 Python 标准库，macOS/Linux 通用

## 工作原理

```
Agent 调用 memory 工具 → Plugin 拦截（无确认标记）
  → 阻止 → 返回确认指引
  → Agent 读取当前文件 → 询问用户
  → 用户确认 → Agent 创建标记文件 → 重试 memory 工具
  → Plugin 检测标记 → 放行 → 删除标记 → 写入成功
  → Agent 重新上锁 → 输出内容 + diff
```

## 安装

1. **下载** — 获取 `memory-file-guard/memory-file-guard/` 下全部文件
2. **复制 Skill** — 放到 `$HERMES_HOME/skills/Always/memory-file-guard/`
3. **复制 Plugin** — 将 `bundled/plugins/memory-file-guard/` 复制到 `$HERMES_HOME/plugins/memory-file-guard/`
4. **启用** — 在 `config.yaml` 的 `plugins.enabled` 中添加 `memory-file-guard`
5. **重启** — `hermes restart gateway`

## 文件结构

```
memory-file-guard/
├── README.md                              # 英文文档
├── README.zh.md                           # 本文档（中文）
└── memory-file-guard/                     # Skill 内容（同名）
    ├── SKILL.md                           # Agent 指令
    ├── references/
    │   └── github-release-checklist.md    # 发布检查清单
    └── bundled/plugins/memory-file-guard/
        ├── __init__.py                    # 插件源码（pre_tool_call 钩子）
        └── plugin.yaml                    # 插件元数据
```

## 常见问题

| 问题 | 解决 |
|------|------|
| Memory 写入未被拦截 | 插件未加载：`hermes plugins enable memory-file-guard` + 重启 |
| Agent 卡在确认循环 | 标记文件未创建——检查临时目录下 `__hermes_memory_approved` 是否存在 |
| 文件锁定权限被拒 | 文件已有 `uchg` 标记：`chflags nouchg <file>` |

## 许可证

MIT
