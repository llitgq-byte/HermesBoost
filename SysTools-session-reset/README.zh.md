# SysTools-session-reset

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
> **升级行为**：`hermes upgrade` 可能覆盖 4 个被修改的文件。升级后需要按 `references/patches.md` 重新打 patch，然后重启所有 gateway。
>
> **安装前先备份**：`hermes-backup` 或 `cp -r $HERMES_HOME/hermes-agent $HERMES_HOME/hermes-agent.bak`
>
> ---

## 它是什么

**Session Reset** 让 Hermes Agent **把 session 清空的操作延迟到当前回复投递完成之后**（飞书卡片、文字、语音等都发完才清）。下一条用户消息会从全新的 session 开始。

解决三个常见问题：

| 问题 | 不重置 | 用 session_reset |
|------|--------|------------------|
| 多步分析后 context 膨胀（5 只股票深度研究） | 下一轮继承 30k token 陈旧 context | 下一轮干净启动 |
| 模型"遗忘"早期对话（因 context 截断） | 打到 `max_tokens` 上限，丢弃早期 turns | 到上限前清理 |
| 累积对话污染下轮推理（股票研究数据影响下一个无关问答） | 下轮被前轮数据污染 | 自然隔离 |

## 工作原理

```
用户消息 → Agent 加载 Skill → ...