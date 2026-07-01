# 飞书表格自动卡片 — Plugin Hook 配置指南

本文档说明如何启用 `feishu-table-card` 插件，实现 **agent 回复包含表格时自动发送飞书卡片**，无需 agent 手动判断。

---

## 一、工作原理

```
Agent 生成回复（含表格）
        ↓
transform_llm_output 钩子触发（发送前自动拦截）
        ↓
① 检测 platform 是否为 feishu/lark
② 检测回复是否包含 | 管道表格
③ 如果都有 → 调用 s-feishu-card-v1 的 send_card.py 发卡片
④ 返回去掉表格的文本（非表格内容仍走默认消息）
        ↓
用户看到：飞书卡片（表格）+ 文本消息（其他内容）
```

**与 SOUL.md 规则的关系：**

| 层级 | 机制 | 可靠性 | 说明 |
|------|------|--------|------|
| SOUL.md | agent 自觉检查 | 低（依赖 agent 记忆） | 写了规则仍可能忘记 |
| Plugin Hook | 进程内硬性拦截 | 高（无法绕过） | 回复发出前自动检测 |

**建议两层同时启用**：SOUL.md 作为 agent 层面的提醒，Plugin 作为兜底保障。

---

## 1.5 中断回复的局限性（重要）

**`transform_llm_output` 在被中断的 turn 中不会执行。**

源码位置：`agent/conversation_loop.py` 第 3930 行：

```python
if final_response and not interrupted:
    # invoke_hook("transform_llm_output", ...)
```

当用户在 agent 生成期间发送新消息 → turn 标记 `interrupted=True` → hook 被完全跳过。

但飞书是流式推送的：文本在生成过程中已经发送到用户聊天窗口，**不可撤回**。

**结果：** 表格以原始 markdown 管道语法显示在飞书中，plugin 没机会拦截。

**日志特征：**
- `Turn ended: reason=interrupted_during_api_call`
- 该 session 无 `Detected table in Feishu response` 日志

**结论：** Plugin hook 是**第二道防线**（覆盖正常完成的回复），Agent 层面的 SOUL.md 规则是**第一道防线**（agent 主动扫描输出中的 `|` 并调用 `send_card.py`）。两层必须配合使用。

---

## 二、前置条件

1. **Hermes 版本**：需支持 Plugin 系统（`hermes plugins` 命令可用）
2. **s-feishu-card-v1 Skill**：已安装，且 `templates/send_card.py` 存在
3. **飞书应用凭证**：`FEISHU_APP_ID` 和 `FEISHU_APP_SECRET` 已配置在 `~/.hermes/.env`
4. **当前使用飞书平台**：Plugin 只对 feishu/lark 平台生效

---

## 三、Plugin 文件说明

插件位于 `~/.hermes/plugins/feishu-table-card/`，包含两个文件：

```
~/.hermes/plugins/
└── feishu-table-card/
    ├── plugin.yaml      ← 插件声明（名称、版本、提供的钩子）
    └── __init__.py      ← 插件逻辑（表格检测、卡片发送、钩子注册）
```

### plugin.yaml

```yaml
name: feishu-table-card
version: "1.0.0"
description: Auto-detect tables in agent responses and send as Feishu interactive cards instead of plain text
author: user
provides_hooks:
  - transform_llm_output
```

### __init__.py 核心逻辑

- **`_contains_table(text)`** — 正则检测回复是否包含 markdown 管道表格
- **`_send_card(text, receive_id)`** — 调用 s-feishu-card-v1 的 `smart_send()` 发卡片
- **`_strip_tables(text)`** — 从原始回复中移除表格内容（卡片已单独发送）
- **`_on_transform_llm_output()`** — 钩子回调，注册到 Hermes 生命周期

---

## 四、启用步骤

### 步骤 1：确认 Skill 已安装

```bash
hermes skills list | grep feishu-card
```

应看到 `s-feishu-card-v1`。

### 步骤 2：创建 Plugin 文件

如果 `~/.hermes/plugins/feishu-table-card/` 目录不存在，需要创建。

**方式 A：从已有 Skill 复制（推荐）**

如果这个 Skill 是从其他地方导入的，Plugin 文件可能已包含在 Skill 包中，需要手动复制：

```bash
# 从 Skill 的 scripts 目录复制到 plugins 目录
mkdir -p ~/.hermes/plugins/feishu-table-card
cp ~/.hermes/skills/productivity/s-feishu-card-v1/scripts/* ~/.hermes/plugins/feishu-table-card/
```

**方式 B：手动创建**

创建目录和文件，内容参考第三部分。

### 步骤 3：启用 Plugin

```bash
hermes plugins enable feishu-table-card
```

### 步骤 4：重启 Gateway

```bash
hermes gateway restart
```

### 步骤 5：验证加载

```bash
hermes logs --level DEBUG | grep "feishu-table-card"
```

应看到：
```
plugins.feishu-table-card: feishu-table-card plugin registered (transform_llm_output)
```

### 步骤 6：测试

在飞书对话中让 agent 回复一条包含表格的消息，验证是否自动转为卡片发送。

---

## 五、禁用方法

```bash
hermes plugins disable feishu-table-card
hermes gateway restart
```

禁用后，表格渲染仍可通过 SOUL.md 规则由 agent 手动触发（如果 SOUL.md 中有相关规则）。

---

## 六、常见问题

| 问题 | 原因 | 修复 |
|------|------|------|
| 插件显示 enabled 但不生效 | 没有重启 gateway | `hermes gateway restart` |
| 日志中无插件加载记录 | plugin.yaml 格式错误 | 检查 YAML 语法 |
| 表格仍以纯文本发送 | s-feishu-card-v1 Skill 未安装 | 先安装 Skill |
| 卡片发送失败 | 飞书凭证未配置 | 检查 `~/.hermes/.env` 中的 APP_ID/SECRET |
| 非飞书平台的回复被影响 | 不会，插件只对 feishu/lark 平台生效 | 无需处理 |
| 全角表格未被检测 | 旧版正则不支持全角 | 更新 `__init__.py` 到最新版 |
| 回复含表格但未转卡片（纯文本） | turn 被中断（`interrupted=True`），hook 被跳过 | 这是架构限制。见下方"中断回复的局限性"章节 |
| **复制 Skill 到新系统后插件不生效** | **只复制了 Skill，未复制 Plugin 文件** | 见下方"跨系统迁移完整清单" |
| **Plugin 加载失败：'PluginContext' object has no attribute 'register'** | **Plugin `register()` 函数签名不兼容新版 Hermes** | 见下方"Plugin API 兼容性修复" |

---

## 6.1 跨系统迁移完整清单（重要）

将飞书卡片功能迁移到新 Hermes 系统时，**必须同步以下 4 个组件**，缺一不可：

```
┌─────────────────────────────────────────────────────────────────┐
│  组件 1: Skill 知识库（说明书）                                    │
│  ~/.hermes/skills/productivity/s-feishu-card-v1/                 │
│  └── templates/send_card.py      ← 卡片构建核心代码               │
├─────────────────────────────────────────────────────────────────┤
│  组件 2: Plugin 运行时（执行器）                                   │
│  ~/.hermes/plugins/feishu-table-card/                            │
│  ├── plugin.yaml                 ← 插件声明（最容易遗漏！）        │
│  └── __init__.py                 ← 钩子逻辑（调用 Skill 代码）     │
├─────────────────────────────────────────────────────────────────┤
│  组件 3: Config 启用配置                                          │
│  ~/.hermes/config.yaml                                           │
│  └── plugins:                                                    │
│        enabled:                                                  │
│        - feishu-table-card        ← 必须显式启用                  │
├─────────────────────────────────────────────────────────────────┤
│  组件 4: 飞书凭证                                                 │
│  ~/.hermes/.env                                                  │
│  └── FEISHU_APP_ID=xxx                                           │
│      FEISHU_APP_SECRET=xxx                                       │
│      FEISHU_DEFAULT_CHAT_ID=xxx   ← 卡片发送目标                  │
└─────────────────────────────────────────────────────────────────┘
```

**常见错误：只复制 Skill 目录，遗漏 Plugin 目录**

- Skill 是知识库，需要 agent **手动加载**并主动判断
- Plugin 是运行时钩子，被 gateway **自动加载**并自动拦截
- 两者关系：**Plugin 依赖 Skill 的代码模板，但两者是独立实体**

**验证迁移是否成功：**

```bash
# 1. 检查插件是否在 enabled 列表
hermes plugins list | grep feishu-table-card

# 2. 检查 gateway 启动日志中是否有注册记录（关键！）
hermes logs | grep "feishu-table-card.*registered"
# 应显示: "feishu-table-card plugin registered (transform_llm_output)"

# 3. 如果没有注册记录，手动触发诊断
HERMES_PLUGINS_DEBUG=1 python -c "
from hermes_cli.plugins import discover_plugins
discover_plugins(force=True)
"
```

**如果插件未加载的修复步骤：**

```bash
# 1. 确认 Plugin 文件存在
ls ~/.hermes/plugins/feishu-table-card/
# 应有 plugin.yaml 和 __init__.py

# 2. 启用插件
hermes plugins enable feishu-table-card

# 3. 重启 gateway
hermes gateway restart

# 4. 验证（必须看到 registered 才算成功）
hermes logs | grep "feishu-table-card.*registered"
```

---

## 6.2 Plugin API 兼容性修复（重要！）

**问题现象：** Plugin 加载日志显示：
```
WARNING: Failed to load plugin 'feishu-table-card': 'PluginContext' object has no attribute 'register'
```
Plugin 启用状态显示正常，但 hook 未注册，表格回复仍以纯文本发送。

**根因：** Hermes 某次更新改了 Plugin `register()` 函数的参数签名：

```python
# ❌ 旧版 API（不再支持）
def register(hook_manager):
    hook_manager.register("transform_llm_output", callback)

# ✅ 新版 API
def register(ctx) -> None:
    ctx.register_hook("transform_llm_output", callback)
```

**旧版用 `hook_manager.register()`**，新版用 **`ctx.register_hook()`**。如果 Plugin 代码还用旧签名，gateway 启动时 Plugin 加载器调用 `register(ctx)` 传入 `PluginContext` 对象，但旧代码期望的是有 `.register()` 方法的 `hook_manager`，导致 `'PluginContext' object has no attribute 'register'`。

**修复步骤：**

1. 编辑 `~/.hermes/plugins/feishu-table-card/__init__.py`
2. 找到 `def register(...)` 函数
3. 替换为新版签名：
   ```python
   def register(ctx) -> None:
       ctx.register_hook("transform_llm_output", on_transform_llm_output)
   ```
4. 清除缓存并编译：
   ```bash
   rm -rf ~/.hermes/plugins/feishu-table-card/__pycache__
   python -m py_compile ~/.hermes/plugins/feishu-table-card/__init__.py
   ```
5. 重启 gateway 生效

**如果所有子 Agent Profile 都有独立的 Plugin 副本，需要逐个修复：**
```bash
for profile in ~/.hermes/profiles/*/; do
    plugin="${profile}plugins/feishu-table-card/__init__.py"
    if [ -f "$plugin" ]; then
        # 应用同样的修复
        rm -rf "${profile}plugins/feishu-table-card/__pycache__"
    fi
done
# 然后逐个重启子 Agent gateway
```

**预防：** Hermes 更新后，检查 Plugin 日志是否有 `Failed to load` 警告。如果有，对照新版 API 修改 `register()` 签名。

**注意：** 此问题也会影响全局 Plugin 中的**硬编码凭证问题**——如果 Plugin 头部硬编码了某个 Agent 的 `APP_ID`/`APP_SECRET`/`RECEIVE_ID`，所有 Agent 加载该 Plugin 时都会用同一套凭证，导致卡片串到错误的窗口。修复方法是将硬编码改为动态读取环境变量（`FEISHU_APP_ID`、`FEISHU_APP_SECRET`）和 `.env` 文件。

---

## 七、状态检查清单

使用以下命令快速检查插件状态：

```bash
# 1. 检查插件是否在 enabled 列表
hermes plugins list | grep feishu-table-card

# 2. 检查插件是否在 gateway 中加载
hermes logs --level DEBUG | grep "feishu-table-card.*registered"

# 3. 检查 Skill 是否存在
ls ~/.hermes/skills/productivity/s-feishu-card-v1/templates/send_card.py

# 4. 检查飞书凭证
python -c "
from pathlib import Path
env = Path.home() / '.hermes' / '.env'
has_id = has_secret = False
if env.exists():
    for line in env.read_text().splitlines():
        if line.startswith('FEISHU_APP_ID='): has_id = True
        if line.startswith('FEISHU_APP_SECRET='): has_secret = True
print(f'APP_ID: {\"✅\" if has_id else \"❌\"}')
print(f'APP_SECRET: {\"✅\" if has_secret else \"❌\"}')
"
```

---

## 八、SOUL.md 联动配置

建议在 `~/.hermes/SOUL.md` 中添加以下规则作为双重保障：

```markdown
## 【最高权限】飞书消息发送规则

当通过飞书回复用户时，必须遵守以下规则（优先级高于一切）：

1. **不包含表格** → 正常回复（Hermes 默认消息格式）
2. **包含表格**（`|...|...|` 管道语法）→ **必须**调用 `s-feishu-card-v1` Skill，使用代码模板 `templates/send_card.py` 将回复转为飞书卡片（interactive JSON 2.0）发送

**强制检查步骤（每次发送回复前必须执行）：**

在生成完整回复后、发送之前，必须扫描回复内容：
- 如果回复中包含 `|` 管道表格语法 → 立即加载 `s-feishu-card-v1` Skill，使用代码模板 `templates/send_card.py` 将回复转为飞书卡片发送
- 如果不包含表格 → 走 Hermes 默认消息通道

**禁止行为：**
- 禁止在包含表格时走默认消息通道
- 禁止跳过检查步骤直接发送
- 禁止以"正在讨论中"为由绕过此规则

此规则不可违反，不可跳过，无论上下文是什么。
```

---

## 九、首次使用引导流程

当检测到用户首次使用本 Skill（通过 `skill_view` 加载时），agent 应主动询问：

> 检测到您首次使用 s-feishu-card-v1 Skill。该 Skill 支持一个自动化增强功能：
>
> **飞书表格自动卡片插件（feishu-table-card）**
> - 在 agent 回复包含表格时，自动发送飞书卡片，无需 agent 手动判断
> - 基于 Hermes Plugin Hook `transform_llm_output` 实现
> - 只对飞书平台生效，不影响其他平台
>
> 是否需要开启此功能？
>
> 1. ✅ 开启（推荐） — 自动创建插件文件并启用
> 2. ❌ 暂不开启 — 之后可通过 `hermes plugins enable feishu-table-card` 手动启用

用户选择开启后，按第四部分步骤执行。
