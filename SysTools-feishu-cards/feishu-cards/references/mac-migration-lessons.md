# Mac 系统迁移复盘记录

## 背景

将 `s-feishu-card-v1` Skill 和 `feishu-table-card` Plugin 从 Windows 系统迁移到 Mac 系统时遇到的问题及修复过程。

## 发现的问题（共 4 个）

### 问题 1：插件未安装未启用

**现象：** 插件文件在 skill 的 scripts/ 目录下，没有复制到 Hermes 的插件目录 `~/.hermes/plugins/`，也没有在 config.yaml 中启用。

**修复：**
- 复制 `__init__.py` + `plugin.yaml` 到 `~/.hermes/plugins/feishu-table-card/`
- 执行 `hermes plugins enable feishu-table-card`
- config.yaml 写入了 `plugins.enabled: [feishu-table-card]`

### 问题 2：Gateway 没有传 chat_id 给 hook

**现象：** Gateway 源码 `conversation_loop.py` 调用 `invoke_hook("transform_llm_output", ...)` 时，只传了 4 个参数：`response_text`、`session_id`、`model`、`platform`，没有传 `chat_id`。

**修复：** 补传两个参数：

```python
# 修改前（4 个参数）
_invoke_hook(
    "transform_llm_output",
    response_text=final_response,
    session_id=agent.session_id or "",
    model=agent.model,
    platform=getattr(agent, "platform", None) or "",
)

# 修改后（6 个参数）
_invoke_hook(
    "transform_llm_output",
    response_text=final_response,
    session_id=agent.session_id or "",
    model=agent.model,
    platform=getattr(agent, "platform", None) or "",
    chat_id=getattr(agent, "_chat_id", None) or "",
    user_id=getattr(agent, "_user_id", None) or "",
)
```

### 问题 3：属性名带下划线，拿错属性

**现象：** AIAgent 的内部属性是 `_chat_id` 和 `_user_id`（带下划线的私有属性），但第一次修复时用了 `chat_id`（无下划线），`getattr(agent, "chat_id", None)` 返回 None。

**修复：** 改为 `getattr(agent, "_chat_id", None)` 和 `getattr(agent, "_user_id", None)`。

### 问题 4：插件硬编码了错误的 fallback chat_id

**现象：** 插件 `_extract_chat_id()` 函数的 fallback 写死了一个旧 chat_id。当 hook 拿不到 chat_id 时就发到了错误的聊天窗口，报错 `code=230002 Bot/User can NOT be out of the chat`。

**修复：** 去掉硬编码 fallback，改为只从环境变量 `FEISHU_DEFAULT_CHAT_ID` 获取，找不到就记录警告并返回空字符串。

## 修改文件清单

| 文件 | 类型 | 修改内容 |
|------|------|----------|
| `~/.hermes/plugins/feishu-table-card/__init__.py` | 新建 | 从 skill scripts 复制 |
| `~/.hermes/plugins/feishu-table-card/plugin.yaml` | 新建 | 从 skill scripts 复制 |
| `~/.hermes/config.yaml` | 修改 | 添加 `plugins.enabled: [feishu-table-card]` |
| `agent/conversation_loop.py` | 修改 | hook 调用增加 `chat_id` + `user_id` 参数 |
| `~/.hermes/plugins/feishu-table-card/__init__.py` | 修改 | 去掉硬编码 fallback chat_id |

## 时间线

| 步骤 | 操作 | 结果 |
|------|------|------|
| 1 | 安装插件 + 启用 + 重启 | ❌ 表格没变卡片 |
| 2 | 检查日志，发现没传 chat_id | 定位根因 |
| 3 | 修复 conversation_loop.py 补传参数（用了 `chat_id`） | ❌ 还是不行 |
| 4 | 发现属性名是 `_chat_id` 不是 `chat_id` | 找到第二个 bug |
| 5 | 修复属性名为 `_chat_id` + `_user_id` | ❌ 还是不行 |
| 6 | 发现插件 fallback 硬编码了错误的 chat_id | 找到第三个 bug |
| 7 | 去掉硬编码 fallback | ❌ 因为步骤 5 的修复还没生效 |
| 8 | 重启 Gateway + `/reset` 新会话 | ✅ 卡片正常显示 |

## 经验教训

1. **不要硬编码 chat_id** — 飞书聊天 ID 是动态的，每个会话不同
2. **注意 Python 私有属性命名** — `_chat_id` ≠ `chat_id`
3. **Gateway hook 参数不完整** — 官方的 `transform_llm_output` hook 只传了 4 个参数，缺少上下文信息，需要自己补
4. **插件修改后必须重启 + 新会话** — 代码修改和插件加载都在启动时完成
5. **Windows 必须清 `__pycache__`** — Python 的 `.pyc` 缓存不会自动刷新
