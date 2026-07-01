# Session Reset — 延迟重置功能

## 这是什么？解决什么问题？

Hermes Agent 在和用户对话时，会把所有聊天记录（包括工具调用结果、搜索结果、飞书卡片内容等）都积累在 session 里。当执行复杂任务时（比如分析 5 只股票、搜索 10 条新闻），session 会迅速膨胀到几万 tokens，导致：
- 模型响应变慢（输入 token 越多越慢、越贵）
- 模型开始"遗忘"早期内容（上下文被截断）
- 下一轮对话还带着上轮的垃圾数据

**Session Reset 就是解决这个问题的。** 它让 Agent 在完成复杂任务后，自动清除 session 上下文。下一次用户发消息时，Agent 从零开始，干干净净。

关键设计：**延迟执行**。Agent 说"我要重置"，但重置发生在回复发送之后。所以用户看到的卡片、文字、语音不会丢失。

---

## 两层架构

```
系统层（改代码）→ 决定工具是否存在 → 所有 Agent 共享
Agent 层（Skill 指令）→ 决定何时调用 → 每个 Agent 独立控制
```

---

## 能力开关

### 系统层：让工具存在或消失

所有改动在 `$HERMES_HOME/hermes-agent/` 目录下，改一次所有 Agent 共享。

#### ✅ 开启（安装）

需要做两件事：

**第一步**：拷贝工具文件

```bash
cp references/session_reset_tool.py $HERMES_HOME/hermes-agent/tools/
```

**第二步**：修改 4 个已有文件，共 6 处改动

打开 `references/patches.md`，里面有每个文件改哪一行、加什么代码，对照着改：

| 文件 | 改动数 | 改什么 |
|------|--------|--------|
| `toolsets.py` | 3 处 | 把 session_reset 加入工具列表 |
| `model_tools.py` | 1 处 | 标记为 agent-loop 工具 |
| `agent/tool_executor.py` | 1 处 | 添加执行分支 |
| `gateway/run.py` | 1 处 | 添加延迟重置逻辑 |

**第三步**：重启 gateway

```bash
hermes gateway restart --profile <agent名称>
```

#### ❌ 关闭（卸载）

三种方法，选一种即可：

| 方法 | 操作 | 影响范围 |
|------|------|----------|
| 最彻底 | 删除工具文件 `rm $HERMES_HOME/hermes-agent/tools/session_reset_tool.py` | 工具完全消失 |
| 保留文件但禁用 | 从 `toolsets.py` 的 `hermes-feishu` 列表里删掉 `"session_reset"` | 飞书 Agent 看不到但文件还在 |
| 最轻量 | 从 `model_tools.py` 的 `_AGENT_LOOP_TOOLS` 里删掉 `"session_reset"` | 工具在列表里但不会被执行 |

改完后重启 gateway 生效。

> 💡 **日常开关不需要改代码！** 见下方 Agent 层说明。

---

### Agent 层：让 Agent 调用或不调用

这才是日常使用中真正的"开关"。**不需要改任何代码，只需要在 Skill 里写不写指令。**

#### ✅ 在某个 Skill 里开启

在 Skill 文件的末尾加一个 `## Finishing` 段落：

```markdown
## Finishing

任务完成后，调用 session_reset tool 清除上下文。
reason 写「股票分析完成：贵州茅台技术面分析」。
```

这样这个 Skill 每次执行完后，Agent 就会自动调 session_reset 清掉上下文。

#### ❌ 在某个 Skill 里关闭

不写 `## Finishing` 指令就行了。Agent 不会主动调 session_reset。

#### 一个 Agent 上可以混用

```
Skill A（重搜索任务）→ 结束后 reset ✅   上下文清空
Skill B（简单问答）  → 不 reset ❌        保留上下文
Skill C（需要记忆）  → 不 reset ❌        保留上下文
```

完全按 Skill 粒度控制，互不干扰。

---

## 怎么写触发指令？

### 最简写法

```markdown
## Finishing

完成后调用 session_reset tool，reason 写「<任务描述>」。
```

### 完整示例（股票分析 Skill）

```markdown
---
name: stock-analysis
description: 分析股票
triggers:
  - 用户要求分析股票
---

# 股票分析

1. 搜索目标股票最新行情
2. 分析技术指标
3. 用飞书卡片输出报告

## Finishing

报告输出完成后，调用 session_reset tool 清除上下文。
reason 写「股票分析完成：<股票名称>」。
```

### 什么时候该用？什么时候不该用？

| 场景 | 用不用？ | 原因 |
|------|----------|------|
| 搜了 5 条新闻、分析 3 只股票 | ✅ 用 | context 膨胀严重 |
| 简单问答（查天气、算数） | ❌ 不用 | context 没多少 |
| 需要记住前面说了什么 | ❌ 不用 | reset 会清掉记忆 |
| 一次工具调用搞定的事 | ❌ 不用 | 没必要 |
| 长对话越聊越多 | ✅ 用 | 及时清理防膨胀 |

---

## 迁移到其他 Hermes 系统

如果你有另一台机器也装了 Hermes，想把 session_reset 带过去：

```bash
# 1. 把整个 skill 目录拷贝过去
scp -r $HERMES_HOME/skills/Always/session-reset/ <目标机器>:$HERMES_HOME/skills/Always/

# 2. 拷贝工具文件
scp references/session_reset_tool.py <目标机器>:$HERMES_HOME/hermes-agent/tools/

# 3. 在目标机器上按 references/patches.md 修改 4 个文件

# 4. 重启目标机器的 gateway
hermes gateway restart --profile <agent名称>
```

---

## 出了问题怎么排查？

**模型说"session_reset 工具不可用"？**

1. 确认工具文件存在：`ls $HERMES_HOME/hermes-agent/tools/session_reset_tool.py`
2. 确认注册：`grep "session_reset" $HERMES_HOME/hermes-agent/toolsets.py`（应有 3 处）
3. 删旧 session 强制重建：`rm <profile>/sessions/sessions.json`
4. 重启 gateway：`hermes gateway restart --profile <名称>`

**调了 session_reset 但 session 没清？**

查日志：`grep "Deferred session reset" <profile>/logs/agent.log`

有日志但没清成功 → 看 ERROR 日志
没日志 → 代码改动可能被覆盖，对照 patches.md 检查
