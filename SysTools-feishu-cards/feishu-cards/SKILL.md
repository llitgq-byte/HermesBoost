---
name: tools-feishu-cards
description: Markdown 自动转飞书卡片（JSON 2.0 interactive）。自动解析表格/标题/代码块，自动清洗全角半角，自动判定拆分，支持多卡片发送。零硬编码路径设计，可移植到任意 Hermes 实例。
version: "2.0.0"
triggers:
  - feishu reply contains table
  - 飞书回复包含表格
  - 需要渲染表格到飞书
  - 飞书卡片发送
  - markdown to feishu card
  - 飞书消息卡片
  - feishu interactive card
  - 复制 skill 到新系统不生效
  - 飞书卡片硬编码路径
related_skills:
  - feishu-cards
---

# Markdown 自动转飞书卡片

将 Markdown 文本自动转换为飞书 `interactive` 卡片（JSON 2.0 schema），支持表格、标题、代码块等完整 Markdown 语法，自动清洗全角半角字符，自动判定是否需要拆分为多张卡片。

---

## 第一部分：触发条件

满足以下**任一条件**时，应使用本 Skill 发送卡片（而非 Hermes 默认的 post 消息）：

1. 回复内容中**包含表格**（`|...|...|` 管道语法）
2. 回复内容中**包含多级标题**（`##` `###` 等）
3. 回复内容中**同时包含**代码块 + 表格 + 标题等复杂格式
4. 用户明确要求以卡片形式发送

**不需要触发的情况：**
- 纯文本、简单加粗、简单列表 → 走 Hermes 默认的 post 消息即可
- 内容很短且没有表格 → 走默认消息

---

## 第二部分：调用前需准备的参数

调用方（agent）在执行代码模板前，必须准备好以下参数：

### 必传参数

| 参数 | 说明 | 获取方式 |
|------|------|---------|
| `text` | 要发送的 Markdown 文本 | agent 自己生成的回复内容 |
| `title` | 卡片标题 | agent 根据回复内容提炼总结 |
| `receive_id` | 目标聊天窗口 ID | 从当前会话上下文中获取 |

### 可选参数（有默认值）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `receive_id_type` | `"chat_id"` | `chat_id` 群聊 / `open_id` 私聊 |
| `app_id` | 自动读取 `FEISHU_APP_ID` 环境变量 | 飞书应用 App ID |
| `app_secret` | 自动读取 `FEISHU_APP_SECRET` 环境变量 | 飞书应用 App Secret |
| `max_card_size` | `30000`（字节） | 单张卡片 JSON 最大字节数 |

### 参数获取说明

**`receive_id` 获取方式：**
- 飞书私聊会话 → `receive_id_type = "chat_id"`，`receive_id = 当前会话的 chat_id`
- 飞书群聊会话 → 同上，但 chat_id 不同
- **必须从会话上下文中动态获取，不能写死**

**`app_id` / `app_secret` 获取方式：**
- 优先从环境变量 `FEISHU_APP_ID` / `FEISHU_APP_SECRET` 自动读取
- 如果环境变量不存在，代码会报错，调用方需要手动传入

**`title` 获取方式：**
- 由 agent 根据回复内容自动总结提炼
- 如果 agent 无法总结，代码会自动 fallback：取第一个 `#` 标题，或取第一行文本前 20 字符

---

## 第三部分：Markdown 输入规范（前置要求）

在转换之前，代码模板会自动进行以下校验和清洗。但调用方也应尽量保证输入规范：

### 3.1 管道字符（必须半角）

```
✅ 半角竖线（U+007C）：|
❌ 全角竖线（U+FF5C）：｜  → 会被自动清洗为半角

✅ 半角连字符（U+002D）：-
❌ 全角破折号（U+FF0D）：－  → 会被自动清洗为半角
```

### 3.2 分隔行

```
✅ 正确：| --- | --- |    或    | - | - |
❌ 错误：| －－－ | －－－ |   （全角，不识别）

每列至少 1 个 - ，可多个。飞书不支持对齐语法（:---: 等），写了不报错但不生效。
```

### 3.3 空格

```
管道符两侧空格可选：
✅ | 列1 | 列2 |
✅ |列1|列2|
```

### 3.4 表格前后空行

```
表格前后必须有空行与其他内容隔开：
✅ 前面文字\n\n| 列1 | 列2 |\n|---|---|\n| a | b |\n\n后面文字
❌ 前面文字\n| 列1 | 列2 |  ← 缺空行，可能不识别
```

### 3.5 特殊字符转义

```
单元格内容包含半角 | 需转义为 \|
其他特殊字符如需原样显示，参考 HTML 转义：
> → &gt;    < → &lt;    ~ → &tilde;    * → &ast;
```

### 3.6 自动清洗（代码自动处理）

代码模板会自动执行以下清洗：
- 全角 `｜` → 半角 `|`
- 全角 `－` → 半角 `-`
- 全角空格 → 半角空格
- 表格前后补空行（如果没有）

---

## 第四部分：转换规则（Markdown → 卡片 JSON）

### 4.1 元素映射表

| Markdown 元素 | 飞书卡片组件 | 说明 |
|--------------|-------------|------|
| `# 一级标题` | `header.title` | 第一个 `#` 提取为卡片标题，不出现正文中 |
| `## ~ ######` | `markdown` 组件 content | 二级及以下标题保留在 markdown 中 |
| `\|...\|...|` 管道表格 | `table` 组件 | 解析为 columns + rows 结构化 JSON |
| 普通段落 | `markdown` 组件 content | 原样保留 |
| `**加粗**` `*斜体*` `~~删除线~~` | `markdown` 组件 content | 原样保留 |
| `[链接](url)` | `markdown` 组件 content | 原样保留 |
| `` `行内代码` `` | `markdown` 组件 content | 原样保留 |
| ```` ```代码块``` ```` | `markdown` 组件 content | 原样保留（飞书支持代码块语法） |
| `- 无序列表` / `1. 有序列表` | `markdown` 组件 content | 原样保留 |
| `> 引用` | `markdown` 组件 content | 原样保留 |
| `![图片](url)` | `markdown` 组件 content | 原样保留 |
| `---` | `hr` 组件 | 独立组件 |

### 4.2 表格转换详情

管道表格转为 `table` 组件的过程：

```
输入：
| 消息类型 | msg_type | 表格支持 |
|----------|----------|---------|
| 纯文本   | text     | ❌      |
| 卡片     | interactive | ✅   |

输出：
{
  "tag": "table",
  "page_size": 10,
  "header_style": {"text_align": "left", "background_style": "grey", "bold": true},
  "columns": [
    {"name": "col_0", "display_name": "消息类型", "data_type": "text"},
    {"name": "col_1", "display_name": "msg_type", "data_type": "text"},
    {"name": "col_2", "display_name": "表格支持", "data_type": "text"}
  ],
  "rows": [
    {"col_0": "纯文本", "col_1": "text", "col_2": "❌"},
    {"col_0": "卡片", "col_1": "interactive", "col_2": "✅"}
  ]
}
```

**data_type 自动推断规则：**
- 纯数字（可含小数点） → `"number"`
- 包含 `[文字](链接)` 格式 → `"lark_md"`
- 其余 → `"text"`

**降级策略：**
- table 组件 > 5 个 → 超出的表格降级为 markdown 管道语法（在 markdown 组件 content 中保留原始 `|...|` 文本）

### 4.3 相邻同类元素合并

相邻的段落、标题、列表、引用、代码块会合并到**同一个** markdown 组件中，减少组件数量：

```
段落1
段落2
## 标题
段落3

→ 合并为一个 markdown 组件，content = "段落1\n\n段落2\n\n## 标题\n\n段落3"
```

表格和分割线（hr）会**打断**合并，作为独立组件。

---

## 第五部分：自动判定和拆分规则

### 5.1 判定优先级

```
第一步：计算预估 JSON 大小
  公式：原始文本 UTF-8 字节数 × 1.3（JSON 结构开销）
  如果预估 > max_card_size（默认 30KB）→ 需要拆分

第二步：计算表格数量
  统计管道表格的个数
  如果 > 5 → 需要拆分

第三步：计算组件数量
  每个 markdown 段落块 = 1 个组件
  每个 table = 1 个组件
  每个 hr = 1 个组件
  如果 > 200 → 需要拆分
```

### 5.2 拆分策略

```
优先级从高到低寻找拆分点：

1. ## 二级标题处（最自然的断点）
2. --- 分割线处
3. 空行处（段落之间）

禁止：
- 禁止在表格中间拆分
- 禁止在代码块中间拆分
```

### 5.3 拆分后的处理

**标题：**
- 第一张卡片：使用原始 title
- 后续卡片：原始 title + "（续 2）"、"（续 3）"...

**颜色轮换：**
```python
COLORS = ["blue", "turquoise", "violet", "green", "indigo", "orange"]
第 N 张卡片使用 COLORS[(N-1) % len(COLORS)]
```

**发送顺序：**
- 依次发送，确保顺序正确
- 如果某张发送失败，停止后续发送并报错

---

## 第六部分：完整调用流程

```
步骤 1：判断是否需要触发（第一部分触发条件）
  ↓ 不触发 → 走 Hermes 默认消息
  ↓ 触发 ↓
步骤 2：准备参数（第二部分参数表）
  - text：agent 的回复内容
  - title：agent 总结的标题
  - receive_id：从当前会话上下文获取
  ↓
步骤 3：读取代码模板
  skill_view("s-feishu-card-v1", file_path="templates/send_card.py")
  ↓
步骤 4：用 execute_code 执行代码
  将 text、title、receive_id 等参数填入代码
  代码自动完成：清洗 → 解析 → 转换 → 判定 → 拆分 → 发送
  ↓
步骤 5：检查返回结果
  成功 → {"success": true, "cards_sent": N, "message_ids": [...]}
  失败 → {"success": false, "error": "原因", "suggestion": "修复建议"}
  ↓
步骤 6：失败处理
  - 根据错误信息调整内容
  - 重试发送
  - 如果仍然失败，降级为 Hermes 默认 post 消息
```

---

## 第七部分：已修复的 Bug 记录（重要经验）

**Bug 1：全角清洗破坏表格结构**
- 症状：表格不渲染，每行变成独立段落
- 原因：`clean_fullwidth` 用正则在每行前插空行，包括表格内部行，导致表格被拆散
- 修复：改为逐行处理，只在表格块边界补空行
- 教训：涉及表格的清洗操作必须逐行处理，不能用全局正则替换

**Bug 2：拆分逻辑被 build_card 降级机制绕过**
- 症状：6个表格不拆分，直接发送报错 "table number over limit"
- 原因：`build_card` 把超过5个的 table 降级为 markdown 管道，`check_limits` 看到的 table 永远 ≤5
- 修复：新增 `_count_raw_tables()` 在原始元素层面做拆分决策
- 教训：拆分判断必须在转换之前，不能依赖转换后的结果

**Bug 3：`response.success()` 返回 False 但消息已发送（"假失败"）**
- 症状：用户实际看到了飞书卡片（发送成功），但 agent 报告"发送失败"
- 原因：飞书 SDK 的 `response.success()` 在某些情况下返回 `False`，即使消息实际上已经发送成功。可能是 SDK 版本问题或响应解析问题
- 修复：同时检查 `response.success()` 和 `response.code == 0`
  ```python
  response_code = getattr(response, 'code', None)
  is_success = response.success() or (response_code == 0)
  ```
- 教训：不要完全依赖 SDK 的 `success()` 方法，对于关键操作应做多重验证

**Bug 5：`lark_oapi` 仅在 hermes-agent venv 中可用**
- 症状：`execute_code` 或 `python3 send_card.py` 报 `ModuleNotFoundError: No module named 'lark_oapi'`
- 原因：`lark_oapi` SDK 安装在 hermes-agent 的 venv 中（`~/.hermes/hermes-agent/venv/lib/python3.x/site-packages/`），不在系统 Python 路径中
- 修复：使用 hermes-agent venv 的 Python 执行脚本：
  ```bash
  ~/.hermes/hermes-agent/venv/bin/python3 /path/to/script.py
  ```
- 教训：所有依赖 `lark_oapi` 的卡片发送脚本，必须用 venv Python 执行，不能用系统 `python3` 或 `execute_code`（sandbox 环境无此包）

**Bug 4：Windows 路径兼容性（`\profiles\/` vs `/profiles/`）**
- 症状：子 Agent（Profile）模式下，`.env` 路径读取失败，fallback 到主 agent 的 `.env`
- 原因：`send_card.py` 中检测 profile 模式时只检查 `/profiles/`（Unix 正斜杠），Windows 路径用 `\profiles\`（反斜杠），条件永远为 False
  ```python
  # 原来（错误）
  if hermes_home and "/profiles/" in hermes_home:  # Windows 上永远不匹配
  ```
- 修复：同时检查两种路径分隔符
  ```python
  # 修复后
  if hermes_home and ("/profiles/" in hermes_home or "\\profiles\\" in hermes_home):
  ```
- 教训：Windows 路径处理必须同时支持 `\` 和 `/`，不能假设 Unix 格式

---

## 第八部分：常见错误和修复

| 错误现象 | 原因 | 修复 |
|---------|------|------|
| 表格显示为纯文本 `|a\|b\|` | 全角竖线 `｜` | 代码自动清洗，或手动改为半角 |
| 卡片发送失败 code=230099 | JSON 格式错误 | 检查特殊字符转义 |
| 内容被截断 | 超过 30KB | 自动拆分为多张卡片 |
| 飞书认证失败 | App ID/Secret 错误 | 检查环境变量 `FEISHU_APP_ID` / `FEISHU_APP_SECRET` |
| 发送到错误窗口 | receive_id 不对 | 从会话上下文重新获取 |
| code=200861 unsupported tag note | JSON 2.0 不支持 note | 不使用 note 组件 |
| markdown 表格只显示5行 | 管道表格每页5行限制 | 改用 table 组件（支持10行） |
| 代码块渲染异常 | 代码块内含 ``` 嵌套 | 使用更多反引号包裹 |
| 标题显示为原始 `#` 文本 | 用了 text/post 消息 | 必须用 interactive 卡片 |
| 认证失败 code=10014 app secret invalid | 环境变量未加载（terminal grep 屏蔽了 secret 值） | 代码模板已内置 .env 文件直接读取作为 fallback |
| 表格不渲染（卡片正常但表格为纯文本竖线） | `clean_fullwidth` 用正则在表格行之间插空行，把表格拆散成单独 paragraph | **禁止用 `re.sub` 批量匹配 `\n|` 插空行**。必须逐行处理，只在表格块的进入/离开边界补空行，表格内部不能动。见 `templates/send_card.py` 中 `_looks_like_table_line()` + 逐行状态机实现 |
| 切换模型后表格不走卡片（纯文本） | Plugin 未加载到 gateway 运行时进程（`plugins.enabled` 被连续 `hermes config set` 覆盖丢失） | 检查日志 `hermes logs \| grep "feishu-table-card.*registered"`，如果没有 → `hermes plugins enable feishu-table-card` + `/restart` |
| 非 default Profile 下卡片发送认证失败（**根因：插件加载了主 agent 的 Skill 路径**） | `feishu-table-card` 插件的 `_get_card_module()` 硬编码加载 `~/.hermes/skills/...`（主 agent Skill 路径）。子 agent 的 `send_card.py` 虽然已修复 `.env` 路径，但插件本身加载的是主 agent 的副本，导致 `.env` 读取仍然指向主 agent | **已修复**：插件 `_get_card_module()` 和 `_get_feishu_credentials()` 现在通过 `sys.path` 推断或 `active_profile` 文件检测当前 profile，优先加载 profile 本地的 Skill 和 `.env`。详见 SKILL.md 第八部分 |
| 非 default Profile 下卡片发送认证失败（旧） | `send_card.py` 硬编码了 `~/.hermes/.env`（第 496 行），子 agent 读取了主 agent 的凭证和 `FEISHU_DEFAULT_CHAT_ID`，导致卡片发到主 agent 窗口 | **已修复**：`send_card.py` 现在支持动态检测当前 profile 路径（通过 `HERMES_HOME` 环境变量）。详见 SKILL.md 第八部分 |
| 非 default Profile 下卡片发送认证失败（旧） | `send_card.py` 硬编码了 `~/.hermes/.env`（第 303 行 `os.path.expanduser("~/.hermes/.env")`），非 default profile 读不到自己的凭证 | 改为 `os.path.expanduser("~/.hermes/profiles/<profile_name>/.env")`（stock profile 即 `~/.hermes/profiles/stock/.env`），或在调用时显式传入 `app_id`/`app_secret` |
| **卡片发送"假失败"** | `response.success()` 返回 False 但消息实际已发送成功 | 同时检查 `response.success()` 和 `response.code == 0`，见第七部分 Bug 3 |
| **cron 环境下 `os.path.expanduser("~")` 展开到 profile home 目录** | Hermes cron job 的 `HOME` 环境变量指向 profile home（如 `/Users/<youruser>/.hermes/profiles/<profile>/home`），`os.path.expanduser("~")` 和 `os.environ["HOME"]` 都返回该目录，导致基于 `~` 的路径拼接多出一层 `/home`。`lark_oapi` 等依赖也不在 cron 默认 Python 路径中 | **不要用 `expanduser` 或 `HOME`**。直接用已知绝对路径（如 `_HOME = "/Users/<realuser>"`），或通过 `hermes-agent/venv/bin/python3` 启动脚本（`os.execv` 重跑）。这是 cron 专属问题，交互式 session 不受影响 |
| **Plugin 加载失败 `'PluginContext' object has no attribute 'register'`** | Hermes 版本更新后 Plugin 注册 API 变更：旧版 `def register(hook_manager): hook_manager.register(...)` → 新版 `def register(ctx) -> None: ctx.register_hook(...)`。Plugin 静默失败，不阻止 gateway 启动，但表格卡片不渲染 | 更新 `__init__.py` 的 `register` 函数签名为新版 API：`def register(ctx) -> None: ctx.register_hook("transform_llm_output", callback)`。清除 `__pycache__` + 重启 gateway。验证方式：日志不再出现 `Failed to load plugin 'feishu-table-card'`，且发带表格消息能看到卡片 |
| **Windows 路径问题** | `send_card.py` 只检查 `/profiles/` 不检查 `\profiles\`，导致子 Agent 读取主 Agent 的 `.env` | 同时检查两种分隔符：`"/profiles/" in path or "\\profiles\\" in path`，见第七部分 Bug 4 |
| **Mac 系统 Plugin 未生效** | 只复制了 Skill 没复制 Plugin，或 Plugin 路径硬编码指向旧系统 | 同步复制 Plugin + 启用 + 重启。详见 `references/cross-platform-portability.md` |
| **Mac 系统卡片发到错误窗口** | Plugin `__init__.py` 硬编码了旧 chat_id 作为 fallback | 升级到 v2.0+，移除所有硬编码 fallback。详见 `references/cross-platform-portability.md` |
| **子 Agent 无法读取飞书文档/表格** | ① 子 Agent 使用不同的 `FEISHU_APP_ID` ② `config.yaml` 缺少 `feishu` toolset | ① 改为与主 Agent 相同的 APP_ID 或单独开通权限 ② 在 `toolsets` 中添加 `- feishu`。详见 `references/profile-subagent-setup.md` |
| **Gateway 重启后 Plugin 加载失败：`'PluginContext' object has no attribute 'register'`** | Hermes 新版 Plugin API 变更：`register(hook_manager)` 签名已废弃，新签名是 `register(ctx) -> None`；`hook_manager.register("hook_name", cb)` 改为 `ctx.register_hook("hook_name", cb)` | 修改 `__init__.py` 的 `register` 函数：`def register(ctx) -> None: ctx.register_hook("transform_llm_output", on_transform_llm_output)`。**所有 Hermes 升级后必须检查此兼容性** |
| **全局 Plugin 硬编码凭证导致跨 Agent 卡片串窗** | `~/.hermes/plugins/` 是全局共享目录，所有 Agent 的 gateway 启动时都会加载同一个 Plugin。如果 Plugin 的 `__init__.py` 顶部硬编码了某个 Agent 的 `APP_ID`/`APP_SECRET`/`RECEIVE_ID`，则**所有 Agent** 触发卡片时都会发到那一个 Agent 的窗口 | **绝对不能在 Plugin 中硬编码凭证**。Plugin 的 `__init__.py` 必须：① 从环境变量 `FEISHU_APP_ID`/`FEISHU_APP_SECRET` 动态读取（每个 Agent gateway 启动时自动注入自己的值）；② `receive_id` 从 hook kwargs 的 `chat_id` 获取，fallback 到 `FEISHU_DEFAULT_CHAT_ID` 环境变量 → 当前 profile 的 `.env` 文件。这样每个 Agent 加载同一个 Plugin 文件，但运行时使用各自的凭证和聊天窗口 |

---

## 第九部分：调用示例

### 最小调用示例

```python
from hermes_tools import execute_code

code = '''
# 代码模板内容（从 templates/send_card.py 读取后填入参数）
result = smart_send(
    text="""要发送的 Markdown 内容，支持表格：
| 列1 | 列2 |
|-----|-----|
| a   | b   |
""",
    title="卡片标题",
    receive_id="<chat_id>",
)
print(result)
'''
```

### 完整调用示例（带所有参数）

```python
result = smart_send(
    text="Markdown 内容...",
    title="自定义标题",
    receive_id="oc_xxx",
    receive_id_type="chat_id",
    app_id="cli_xxx",           # 可选，默认从环境变量读取
    app_secret="xxx",            # 可选，默认从环境变量读取
    max_card_size=30000,         # 可选，默认 30KB
)
```

---

## 第十部分：自动化增强 — Plugin Hook

本 Skill 支持通过 Hermes Plugin Hook 实现**全自动表格卡片发送**，无需 agent 手动判断。

**详细配置指南请参考：** `references/plugin-hook-setup.md`

### 核心概念

| 项目 | 说明 |
|------|------|
| 插件名称 | `feishu-table-card` |
| 钩子类型 | `transform_llm_output`（回复发送前自动触发） |
| 触发条件 | 平台为 feishu/lark **且** 回复包含 `\|` 管道表格 |
| 依赖 | 本 Skill（s-feishu-card-v1）的 `templates/send_card.py` |

### 首次使用引导

**当检测到用户首次加载本 Skill 时，agent 应主动询问：**

> 检测到您首次使用 s-feishu-card-v1 Skill。该 Skill 支持一个自动化增强功能：
>
> **飞书表格自动卡片插件（feishu-table-card）**
> - agent 回复包含表格时，自动发送飞书卡片，无需手动判断
> - 基于 Hermes Plugin Hook 实现，无法被 agent 忽略
> - 只对飞书平台生效，不影响其他平台
>
> 是否需要开启此功能？

用户确认后，按照 `references/plugin-hook-setup.md` 第四部分执行启用步骤。

### 插件版本同步检查

**当子 agent 卡片路由异常时**，先用诊断脚本扫描所有 profile 的插件版本：

```bash
python ~/.hermes/skills/productivity/s-feishu-card-v1/scripts/scan_plugin_versions.py
```

输出示例：
```
Profile              Lines    Status
------------------------------------------
[main agent]         331      REFERENCE
------------------------------------------
lifehelper           331      OK
stock                239      STALE
```

STALE 的 profile 需要从主 Agent 复制最新插件 + 清缓存 + 重启 gateway。

### Plugin register() API 版本兼容性（重要）

Hermes Plugin 注册 API 在某次更新后发生变更：

```python
# ❌ 旧版（已废弃，会导致 'PluginContext' object has no attribute 'register'）
def register(hook_manager):
    hook_manager.register("transform_llm_output", on_transform_llm_output)

# ✅ 新版（当前正确签名）
def register(ctx) -> None:
    ctx.register_hook("transform_llm_output", on_transform_llm_output)
```

**注意：** Plugin 加载失败是静默的——gateway 正常启动，不报崩溃，只是表格不渲染卡片。必须检查启动日志确认 `feishu-table-card` 无 `Failed to load` 警告。

### 插件无法拦截被中断的回复（架构限制）

**现象：** agent 回复包含表格，但以纯文本管道语法发送到飞书，卡片未触发。

**根因：** `conversation_loop.py` 第 3930 行的 `transform_llm_output` 调用有条件守卫：

```python
if final_response and not interrupted:
    # Plugin hook: transform_llm_output  ← 被跳过
```

当用户在 agent 生成回复期间发送新消息时，turn 被标记为 `interrupted=True`，hook **完全不执行**。但飞书是流式推送的——文本在生成过程中已经逐段发送到用户聊天窗口，不可撤回。

**结果：** 表格以原始 markdown 管道语法显示，没有卡片，也无法补救。

**日志特征：**
- `Turn ended: reason=interrupted_during_api_call`
- 本次 session 中**没有** `Detected table in Feishu response` 日志

**影响范围：** 仅发生在用户打断 agent 生成的场景。正常完成的回复不受影响（日志显示多次 `Card sent OK`）。

**应对策略：** 这不是 bug 而是设计权衡——中断时不做转换避免对不完整的回复做卡片。因此 **agent 层面的表格扫描规则（SOUL.md）必须作为第一道防线**，plugin hook 是第二道（兜底）。两层配合：
1. **Agent 层（SOUL.md 规则）**：输出前扫描 `|`，发现表格 → 调用 `s-feishu-card-v1` 的 `send_card.py` 主动发卡片。这是**可靠的**，因为 agent 控制自己的输出。
2. **Plugin 层（transform_llm_output）**：拦截漏网的表格。覆盖正常完成的回复。

**验证方法：** 发生问题时检查 `agent.log`：
```bash
# 确认是中断导致的
grep "interrupted" ~/.hermes/logs/agent.log | tail -5
# 确认 hook 没触发
grep "Detected table" ~/.hermes/logs/agent.log | tail -5
```

### 插件加载持久性问题

**问题：** gateway 重启后 Plugin `feishu-table-card` 可能不加载，即使 config.yaml 里 `plugins.enabled` 列表包含它。

**根因：** `hermes config set` 的实现是"读 config.yaml → 改值 → 整个写回"。连续快速执行多条时存在竞态：前一次写入还未完成，后一次读到不完整的文件（空 `{}`），写回后 `plugins.enabled` 列表就丢失了。用户插件（如 feishu-table-card）是 opt-in 的，依赖 `plugins.enabled` 列表，没有自动加载机制。

**验证插件是否加载：**
```bash
# 查看 gateway 启动日志
hermes logs | grep "Plugin discovery complete"
# 应显示 "26 found, 22 enabled"（22 包含 feishu-table-card）

# 查看插件注册
hermes logs | grep "feishu-table-card.*registered"
# 应显示 "feishu-table-card plugin registered (transform_llm_output)"

# 或用 hermes plugins list（但这只读 config 文件，不代表运行时状态）
hermes plugins list | grep feishu-table-card
```

**如果插件未加载：**
```bash
hermes plugins enable feishu-table-card
/restart
```

**关键区别：**
- `hermes plugins list` 显示 enabled → 只是 config 文件写对了
- 日志里有 `feishu-table-card plugin registered` → 运行时真正加载了
- **两者都满足才说明插件正常工作**

### ⚠️ Pitfall：cron 任务中无法发送飞书卡片

**现象**：cron job 尝试用 `execute_code` 执行 `send_card.py` 发送飞书卡片，失败。

**根因**：cron job 创建时设置了 `enabled_toolsets`（如 `["file", "skills"]`），**排除了 `execute_code`**。cron 默认拥有全部工具（包括 `execute_code`），卡片可以正常发送——问题出在人为限制了工具集。

**正确做法**：
- 创建需要发卡片的 cron 任务时，**不要设置 `enabled_toolsets`**（或传空数组 `[]`），让 agent 拥有全部默认工具
- 已有成功案例：`day-morning` 早报 cron 不设 `enabled_toolsets`，卡片发送正常
- 如果确实需要限制工具集（如节省 token），则在 prompt 中指导 agent 用纯文本格式推送，不走卡片

**常见误解**："cron 天然不支持发卡片"——这是错的。只有被 `enabled_toolsets` 限制后才不支持。

### ⚠️ Pitfall：管道表格单元格内容含 `|` 导致数据截断

**现象**：表格某列内容包含 `|` 时，数据被截断或列错位。

**根因**：`send_card.py` 的 `parse_pipe_table` 用 `dl.split("|")` 切分，内容中的 `|` 被误当分隔符。

**修复**：单元格内容禁止使用半角 `|`，用 `·`、`｜`（全角）、`—` 等替代。详见 `references/pipe-table-pitfalls.md`。

**示例**：
```
# ❌ 错误 — 穿衣建议列被截断
| 建议 | 薄外套|长裤，带伞 |

# ✅ 正确 — 用 · 替代 |
| 建议 | 薄外套·长裤，带伞 |
```

---

## 第十一部分：零硬编码路径设计 — Skill + Plugin 可移植性指南（v2.0）

### 11.1 设计目标

将 `s-feishu-card-v1` 和 `feishu-table-card` 设计为**零硬编码、零配置、跨平台**的可移植组件：

- **零硬编码路径**：所有路径运行时动态推断，不写死任何绝对路径
- **零配置部署**：复制到任意 Hermes 实例后无需修改代码即可运行
- **跨平台兼容**：Windows / macOS / Linux 统一通过 `pathlib` 处理
- **Skill + Plugin 共用工具**：提取 `utils.py` 避免重复代码

### 11.2 架构图（v2.0）

```
s-feishu-card-v1/
├── SKILL.md              # Skill 知识库（本文档）
├── README.md             # 部署文档（面向用户）
├── templates/
│   ├── send_card.py      # 卡片构建与发送核心逻辑
│   ├── utils.py          # ★ NEW: 共用工具（路径推断、凭证读取、环境检测）
│   └── feishu_card_template.json
└── scripts/
    └── install_plugin.py # ★ NEW: 一键安装脚本

~/.hermes/plugins/feishu-table-card/
├── __init__.py           # Plugin 入口（导入 utils.py，零硬编码）
├── plugin.yaml           # 插件声明（v2.0.0）
└── utils.py              # ★ 可选: 复制自 Skill（避免跨目录导入）
```

### 11.3 已移除的硬编码点（v2.0 完整清单）

| # | 位置 | 旧硬编码（v1.x） | 新实现（v2.0） | 影响 |
|---|------|----------------|---------------|------|
| 1 | `send_card.py:17` | `C:\Users\macmini\...` Windows 绝对路径 | 动态 `sys.path` 推断 + `Path.home()` | 跨系统复制后无需修改 |
| 2 | `send_card.py:496` | `"/profiles/"` Unix 分隔符 | `pathlib.Path` 跨平台拼接 | Windows/Mac 统一支持 |
| 3 | `__init__.py:122` | `~/.hermes/skills/productivity/s-feishu-card-v1` | `utils.find_skill_template()` 递归搜索 | 不依赖分类名称 |
| 4 | `__init__.py:87` | `~/.hermes/.env` 重复凭证逻辑 | `utils.get_feishu_credentials()` 统一读取 | Skill + Plugin 共用 |
| 5 | `__init__.py:235` | 硬编码 fallback chat_id `oc_d6f9ed86...` | 完全移除，仅依赖参数/环境变量 | 避免发到错误窗口 |
| 6 | `__init__.py:147` | 重复实现 `.env` 解析 | 统一调用 `feishu_card_utils.read_env_file()` | 减少维护成本 |
| 7 | `send_card.py` | 独立实现路径推断 | 导入 `feishu_card_utils.get_hermes_home()` 等函数 | 代码复用 |
| 8 | `__init__.py:91` | `import utils` 与 Hermes 内置模块冲突 | 重命名为 `feishu_card_utils.py` | 避免 `module 'utils' has no attribute 'find_skill_template'` |

### 11.4 共用工具模块命名规范（关键）

**模块名称必须使用唯一前缀，不能命名为通用名称如 `utils.py`**。

#### 错误做法（会导致冲突）

```python
# ❌ 错误：通用名称会与 Hermes 内置模块冲突
import utils  # 可能加载到错误的内置 utils 模块
```

#### 正确做法（使用项目前缀）

```python
# ✅ 正确：使用唯一前缀名称
import feishu_card_utils as utils_mod
```

#### 冲突根因

Hermes Gateway 进程在启动时会加载大量内置模块。如果 Plugin 使用 `import utils`，Python 的模块缓存（`sys.modules`）中可能已存在一个名为 `utils` 的内置模块，导致 Plugin 加载到错误的模块。

**错误日志特征：**
```
Hook 'transform_llm_output' callback _on_transform_llm_output raised: 
module 'utils' has no attribute 'find_skill_template'
```

**排查方法：**
```python
import utils
print(utils.__file__)  # 检查加载的是哪个文件
# 如果输出不是 ~/.hermes/plugins/feishu-table-card/utils.py，说明冲突了
```

#### 命名规范

| 组件 | 推荐文件名 | 说明 |
|------|-----------|------|
| 共用工具模块 | `feishu_card_utils.py` | 项目前缀 + 功能描述 |
| Plugin 入口 | `__init__.py` | 固定名称 |
| 卡片模板 | `feishu_card_template.json` | 项目前缀 |

### 11.5 feishu_card_utils.py API

```python
# 路径推断
get_hermes_home() -> Path          # 当前 Hermes 实例根目录
get_hermes_repo_path() -> str      # Hermes 源码/安装目录
find_skill_template(name) -> Path  # 查找 Skill 模板目录（递归搜索）
get_env_path() -> Path             # 当前实例的 .env 文件路径

# 凭证读取
read_env_file(path) -> dict        # 读取 .env 为字典
get_feishu_credentials() -> tuple  # 获取 (app_id, app_secret)
get_feishu_chat_id() -> str        # 获取 chat_id（零硬编码 fallback）

# 环境检测
is_profile_mode() -> bool          # 是否在 profile 模式下
get_current_profile_name() -> str  # 当前 profile 名称

# 跨平台兼容
ensure_lark_oapi()                 # 确保 lark_oapi 可导入

# 调试
dump_env_info() -> str             # 输出环境诊断信息
```

### 11.6 路径推断优先级（运行时）

```
1. HERMES_HOME 环境变量（如果已设置）
2. 当前文件位置回溯（utils.py → templates/ → skill/ → skills/ → .hermes/）
3. hermes_cli 模块文件位置 → 向上推断 hermes-agent 根目录
4. sys.path 中包含 hermes-agent 的条目
5. Path.home() / ".hermes"（最终 fallback，跨平台）
```

### 11.7 跨平台兼容性

| 平台 | 路径处理 | 额外注意事项 |
|------|---------|-------------|
| Windows | `pathlib.Path` 自动处理 `\` 和 `/` | 修改源码后必须清除 `__pycache__` 并重新编译 |
| macOS | `pathlib.Path` 自动处理 `/` | 无特殊要求 |
| Linux | `pathlib.Path` 自动处理 `/` | 无特殊要求 |
| WSL | 混合路径 | 统一用 `Path()` 包装 |

### 11.8 迁移检查清单（v2.0 简化版）

复制 Skill 到新系统后，只需执行：

```bash
# 1. 一键安装（自动复制 Plugin + 启用 + 重启）
python ~/.hermes/skills/productivity/s-feishu-card-v1/scripts/install_plugin.py

# 2. 验证
hermes logs | grep "feishu-table-card.*registered"
```

或手动执行：

```bash
# 1. 复制 Plugin（如果 install_plugin.py 不可用）
cp -r ~/.hermes/skills/productivity/s-feishu-card-v1/scripts/feishu-table-card \
      ~/.hermes/plugins/

# 2. 启用
hermes plugins enable feishu-table-card

# 3. 重启
hermes restart gateway

# 4. 清除缓存（Windows 必须）
find ~/.hermes/plugins -name "__pycache__" -exec rm -rf {} +
python -m py_compile ~/.hermes/plugins/feishu-table-card/__init__.py

# 5. 发送测试消息验证
```

- `references/plugin-hook-setup.md` — Plugin 安装与配置详细指南
- `references/cross-platform-portability.md` — 零硬编码可移植性完整指南（含 Mac 复盘教训）
- `references/hardcoded-paths-migration.md` — 旧版本硬编码点迁移对照表（v1.x → v2.0）
- `references/profile-subagent-setup.md` — Profile/子 Agent 飞书权限配置指南（解决子 Agent 无法访问文档/表格问题）

### 11.9 调试命令

```bash
# 环境诊断
python ~/.hermes/skills/productivity/s-feishu-card-v1/templates/utils.py

# 插件版本扫描（多 profile）
python ~/.hermes/skills/productivity/s-feishu-card-v1/scripts/scan_plugin_versions.py
```

### 11.10 Mac 迁移复盘

从 Mac 系统迁移时遇到的实际问题及修复过程，详见 `references/mac-migration-lessons.md`。

核心教训：
1. 不要硬编码 chat_id
2. 注意 Python 私有属性 `_chat_id` ≠ `chat_id`
3. Gateway hook 需要补传 `chat_id` 和 `user_id`
4. 插件修改后必须重启 + 新会话
5. Windows 必须清 `__pycache__`
---

---

## 第十二部分：Skill vs Plugin 关系澄清

**最常见误区：认为 Skill 包含了 Plugin 功能**

| 维度 | Skill (s-feishu-card-v1) | Plugin (feishu-table-card) |
|------|--------------------------|---------------------------|
| **本质** | 知识库 + 代码模板 | 运行时钩子 |
| **加载方式** | agent 手动 `skill_view()` 加载 | gateway 启动时自动扫描加载 |
| **触发方式** | agent 主动判断后调用 | 回复发出前自动拦截 |
| **存放位置** | `~/.hermes/skills/...` | `~/.hermes/plugins/...` |
| **依赖关系** | 被 Plugin 调用 | 依赖 Skill 的 `send_card.py` |
| **能否独立工作** | ✅ 可以（agent 手动调用） | ❌ 不行（必须依赖 Skill 代码） |

**关键结论：**
- 只复制 Skill → agent 可以手动发卡片，但**没有自动拦截**
- 只复制 Plugin → 插件加载失败（找不到 `send_card.py`）
- **两者都必须复制**，并且都要在 config 中启用、重启 gateway

**跨系统迁移时必须同步的 5 个组件：**
1. `~/.hermes/skills/productivity/s-feishu-card-v1/` — Skill 知识库
2. `~/.hermes/plugins/feishu-table-card/` — Plugin 运行时
3. `~/.hermes/config.yaml` 中 `plugins.enabled` 包含 `feishu-table-card`
4. `~/.hermes/.env` 中的飞书凭证（`FEISHU_APP_ID` / `FEISHU_APP_SECRET`）
5. `~/.hermes/.env` 中的 `FEISHU_DEFAULT_CHAT_ID`（可选，用于 fallback）

**子 Agent (Profile) 额外注意事项：**
- 子 Agent 的 `.env` 中 `FEISHU_APP_ID` 默认与主 Agent 不同，需要手动改为相同值或单独开通权限
- 子 Agent 的 `config.yaml` 中 `toolsets` 需要包含 `feishu` 才能使用飞书工具（这是最常见的问题！）
- 子 Agent 的 `toolsets` 默认只有 `hermes-cli`，必须显式添加 `feishu_doc` 和 `feishu_drive`
- 详见 `references/profile-subagent-setup.md`

详见 `references/plugin-hook-setup.md` 第六部分"跨系统迁移完整清单"，以及 `references/cross-platform-portability.md` 零硬编码可移植性指南。
