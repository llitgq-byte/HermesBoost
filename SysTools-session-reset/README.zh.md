# SysTools-session-reset

**[English](README.md)** · 🇨🇳 中文

---

<p align="center">
  <strong>⚠️ 本 skill 修改 Hermes Agent 核心源代码，安装前请先备份。</strong>
</p>

<p align="center">
  <strong>⚡ 复制以下内容给你的 Agent → Agent 自动配置一切：</strong>
</p>

<p align="center">
  <code>下载 https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-session-reset/session-reset 下的所有文件。先阅读 SKILL.md + references/patches.md + references/README.md + references/session_reset_tool.py。备份 $HERMES_HOME/hermes-agent/ 后，按 references/patches.md 应用 6 处 patch（修改 4 个核心文件 + 新增 1 个 tool 文件）。最后用 'hermes gateway restart --profile &lt;名称&gt;' 重启所有 gateway。这是 Session Reset skill — 让 Agent 在回复投递完成后再清 session，用户的卡片/文字/语音一条都不会丢。</code>
</p>

---

> ⚠️ **警告 — 系统级改动**
>
> 本 skill 修改 Hermes Agent 的 **核心源代码**（`$HERMES_HOME/hermes-agent/` 下 5 个文件）。它**不是**沙盒插件 —— patch 在框架层持久生效，影响本机所有 profile。
>
> **测试版本**：Hermes Agent **v0.15.1**（2026 年 6 月）
> **改动文件**：
> - `$HERMES_HOME/hermes-agent/tools/session_reset_tool.py` *(新建)*
> - `$HERMES_HOME/hermes-agent/toolsets.py`
> - `$HERMES_HOME/hermes-agent/model_tools.py`
> - `$HERMES_HOME/hermes-agent/agent/tool_executor.py`
> - `$HERMES_HOME/hermes-agent/gateway/run.py`
>
> **升级行为**：`hermes upgrade` 可能覆盖 4 个被修改的文件。升级后按 `references/patches.md` 重新打 patch，然后重启所有 gateway。
>
> **安装前先备份**：`hermes-backup` 或 `cp -r $HERMES_HOME/hermes-agent $HERMES_HOME/hermes-agent.bak`

---

## 它解决了什么问题？

Hermes Agent 把每轮对话（工具调用、搜索结果、卡片内容、语音转写）都积累在 session 里。复杂任务（分析 5 只股票、抓 10 篇文章、生成 10 页报告）跑完后，context 可能膨胀到 30k+ tokens，导致：

- API 调用变慢、变贵
- 模型"遗忘"早期对话（context window 截断）
- 下一轮继承上一轮的脏数据

**Session Reset** 让 Agent 把清 session 的操作推迟到回复投递完成之后。下一条用户消息从干净开始，但用户看到的输出（卡片/文字/语音）不会丢一条。

## 核心特性

- **延迟重置** — 回复完全投递后才清，用户可见输出零丢失
- **Skill 粒度控制** — 通过 `## Finishing` 段落按需启用（每个 Skill 独立开关）
- **审计友好** — `reason` 参数会被日志记录（如"完成 5 只股票分析"）
- **平台无关** — `session_reset` 在 `_HERMES_CORE_TOOLS` 里，飞书/CLI/Discord/Telegram 都自动可用
- **完整 patch 文档** — references/patches.md 含 6 个可直接应用的 patch
- **3 种关闭方法** — 删文件 / 从工具列表移除 / 从 `_AGENT_LOOP_TOOLS` 移除

## 工作原理

```
用户消息 → Agent 加载 Skill → ... 工具链 ... → 调用 session_reset(reason=...)
                                                      ↓
                                            生成最终回复
                                                      ↓
                                      飞书投递卡片 + 文字（完整投递）
                                                      ↓
                                  Gateway 检查 _pending_session_reset 标志
                                                      ↓
                              执行 reset_session() + 驱逐缓存的 agent
                                                      ↓
                          下一条用户消息 → 全新 session（干净 context）
```

**两层架构**：
- **系统层**（改代码）— 决定 `session_reset` 工具**是否存在**（影响所有 Agent）
- **Agent 层**（Skill 指令）— 决定**本 Skill 是否调用**重置（每个 Skill 独立控制）

## 安装步骤

### Step 1：备份

```bash
# 用内置备份工具
hermes-backup

# 或手动备份
cp -r $HERMES_HOME/hermes-agent $HERMES_HOME/hermes-agent.bak
```

### Step 2：安装新 tool 文件

```bash
# 拷贝新的 session_reset 工具定义
cp references/session_reset_tool.py $HERMES_HOME/hermes-agent/tools/
```

### Step 3：给 4 个核心文件打 patch

打开 [`references/patches.md`](references/patches.md)，按文件中标注对 4 个文件应用 6 处 patch：

| 文件 | Patch 数 | 风险等级 |
|------|---------|---------|
| `toolsets.py` | 3 处（`_HERMES_CORE_TOOLS`、`session_reset_tool` 定义、`hermes-feishu` 列表） | 高 |
| `model_tools.py` | 1 处（`_AGENT_LOOP_TOOLS` 集合） | 中 |
| `agent/tool_executor.py` | 1 处（新增 `session_reset` 的 elif 分支） | 中 |
| `gateway/run.py` | 1 处（compression exhaustion 块后加 deferred-reset 检查） | 高 |

### Step 4：重启所有 gateway

```bash
hermes gateway restart --profile <your-profile>
hermes gateway restart --profile <other-profile>
# ... 给每个需要 session_reset 的 profile 都重启
```

### Step 5：验证

```bash
# 确认 tool 文件存在
ls $HERMES_HOME/hermes-agent/tools/session_reset_tool.py

# 确认 toolset 注册（应有 3 处匹配）
grep "session_reset" $HERMES_HOME/hermes-agent/toolsets.py

# 确认 agent-loop 注册
grep "session_reset" $HERMES_HOME/hermes-agent/model_tools.py

# 在飞书聊天里发个复杂任务，Agent 完成后日志里应看到 session_reset 调用
grep "Deferred session reset" $HERMES_HOME/logs/agent.log
```

## 文件结构

```
SysTools-session-reset/
├── README.md                              ← 本文件（英文，含 WARNING + ⚡ 提示）
├── README.zh.md                           ← 中文文档（含警告框 + ⚡ 提示）
└── session-reset/
    ├── SKILL.md                           ← Agent 指令（309 行，完整指南）
    └── references/
        ├── README.md                      ← 系统层介绍 + 启用/关闭（184 行）
        ├── patches.md                     ← 6 处 patch 的完整 diff（153 行）
        └── session_reset_tool.py          ← 新工具源码（90 行）
```

## 在 Skill 中使用

在需要清理 context 的 Skill 末尾加 `## Finishing` 段落：

```markdown
## Finishing

[任务输出] 投递完成后，调用 session_reset tool 清除上下文。
reason 写「[任务描述] — context 重，延迟重置」。
```

### 何时用 / 何时不用

| 场景 | 是否重置 | 原因 |
|------|---------|------|
| 多步分析（5 只股票、10 篇文章） | ✅ 用 | context 膨胀严重 |
| 简单问答（查天气、算数） | ❌ 不用 | context 没多少 |
| 一次性工具调用（查日历、发消息） | ❌ 不用 | 没意义 |
| 长对话 context 越攒越多 | ✅ 用 | 防止晚期截断 |
| Skill 需要跨轮记忆 | ❌ 不用 | reset 会破坏 Skill |

## 故障排查

| 问题 | 解决 |
|------|------|
| Agent 说"session_reset 工具不可用" | (1) 确认 tool 文件存在 (2) 检查 toolsets.py 的 3 处 grep (3) 删 `sessions.json` 强制重建 agent (4) 重启 gateway |
| `session_reset` 调用了但 session 没清 | 查 `grep "Deferred session reset" agent.log` — 有日志但 reset 没成功 → 看 ERROR 堆栈；没日志 → patch 可能被覆盖 |
| `hermes upgrade` 后 patch 丢失 | 按 `references/patches.md` 重新打。升级前先提交改过的 core 文件或 `hermes-backup` |
| `_pending_session_reset` 没被设置 | 检查 `_AGENT_LOOP_TOOLS` 是否包含 `"session_reset"`。少了它会走标准 MCP dispatch 而不是 elif 分支 |
| Agent 重建后看不到新工具 | 删 `sessions.json` 再重启 gateway。旧 agent 对象被缓存，是在打 patch 之前构建的 |

## 升级与维护

这些 patch 修改 Hermes **核心源码**，`hermes upgrade` 可能覆盖。

**每次升级后**：
1. `diff -r $HERMES_HOME/hermes-agent /path/to/backup` 找改动
2. 按 `references/patches.md` 重打丢失的 patch
3. 在聊天里测试 session_reset 是否仍可用
4. 如果你的 core 文件在 git 里，commit 改动的版本

**升级前先备份**：
```bash
cp -r $HERMES_HOME/hermes-agent $HERMES_HOME/hermes-agent.v0.15.1.bak
```

## 许可证

MIT —— 详见父仓库。Skill 文件（SKILL.md、references/）MIT 许可。Patch 修改的是 Hermes Agent 核心代码，保留其原始许可证。