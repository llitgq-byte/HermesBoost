---
name: tools-feishu-calendar
description: "飞书日历操作。通过飞书 API 管理共享日历的日程增删改查。首次使用需初始化，之后所有 Agent 共享同一个日历。"
version: "1.0.0"
triggers:
  - 用户提到日历、日程、会议、安排、提醒
  - 用户要求创建/查询/修改/删除日程
---

# 飞书日历

通过飞书 API 管理一个由应用拥有的共享日历。所有 Agent profile 共享同一份日历和状态。

## 前提

- `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET` 已在 `.env` 中配置
- 飞书应用已开启日历相关 API 权限

## 脚本路径

```
TOOL=$HERMES_HOME/skills/Always/tools-feishu-calendar/scripts/calendar_tool.py
```

> **⚠️ 重要**：`execute_code` 沙箱中 `~` 会展开到 profile home 路径（如 `~/.hermes/profiles/<profile>/home/`），导致路径解析错误。`terminal()` 中 `~` 展开正确，不受影响。
>
> 因此：**`terminal()` 中用 `~` 路径即可，`execute_code` 中必须用绝对路径。**
>
> ```bash
> # ✅ terminal() 中 — ~ 展开正确
> python3 $HERMES_HOME/skills/Always/tools-feishu-calendar/scripts/calendar_tool.py
> ```
>
> ```python
> # ✅ execute_code 中 — 必须用绝对路径
> subprocess.run(["python3", "/absolute/path/to/skills/Always/tools-feishu-calendar/scripts/calendar_tool.py"])
> ```

## 操作流程

### 第一步：检查是否已初始化

收到任何日历相关请求时，**先执行**：

```bash
python3 $HERMES_HOME/skills/Always/tools-feishu-calendar/scripts/calendar_tool.py
```

- 返回 `"initialized": true` → 直接跳到「日常操作」
- 返回 `"initialized": false` → 执行「首次初始化」

### 首次初始化

**步骤 1：询问用户**

> 向用户确认日历名称，例如 "Hermes 助手日历"。

**步骤 2：获取 chat_id**

从以下来源依次查找飞书 DM 的 chat_id（`oc_` 开头）：
1. 当前会话上下文中的 chat_id
2. Profile `.env` 中的 `FEISHU_DM_CHAT_ID`
3. 直接询问用户

**步骤 3：执行初始化**

```bash
python3 $HERMES_HOME/skills/Always/tools-feishu-calendar/scripts/calendar_tool.py init \
  --name "用户指定的日历名称" \
  --chat-id "oc_xxxxxxxxxxxx"
```

**步骤 4：告知用户**

> 告诉用户日历创建成功。飞书"日历助手"机器人会自动推送一条授权通知，用户直接点击通知中的链接即可查看和订阅日历。

### 日常操作

#### 查询日程

默认查询未来 7 天：

```bash
python3 $HERMES_HOME/skills/Always/tools-feishu-calendar/scripts/calendar_tool.py list
```

指定天数：

```bash
python3 $HERMES_HOME/skills/Always/tools-feishu-calendar/scripts/calendar_tool.py list --days 14
```

#### 创建日程

指定持续时长（分钟）：

```bash
python3 $HERMES_HOME/skills/Always/tools-feishu-calendar/scripts/calendar_tool.py create \
  --title "日程标题" \
  --when "2026-06-04 10:00" \
  --minutes 60 \
  --desc "描述内容" \
  --location "地点"
```

指定结束时间（与 --minutes 二选一）：

```bash
python3 $HERMES_HOME/skills/Always/tools-feishu-calendar/scripts/calendar_tool.py create \
  --title "日程标题" \
  --when "2026-06-04 10:00" \
  --end "2026-06-04 11:30"
```

`--desc` 和 `--location` 均为可选。都不指定持续时间则默认 1 小时。

#### 删除日程

```bash
python3 $HERMES_HOME/skills/Always/tools-feishu-calendar/scripts/calendar_tool.py delete \
  --event-id "事件ID"
```

#### 重置（重新初始化）

删除日历并清空状态，下次使用时会重新走初始化流程：

```bash
python3 $HERMES_HOME/skills/Always/tools-feishu-calendar/scripts/calendar_tool.py reset --confirm
```

## 输出格式

所有命令返回 JSON，统一包含 `"ok": true/false`。list 返回 `"events"` 数组，每个事件含 `event_id`、`title`、`description`、`location`、`start`、`end`、`status`、`link`。

## 注意事项

- `--when` 格式：`YYYY-MM-DD HH:MM`（24 小时制）
- ACL 授权和 calendar_id 永不过期，初始化只需一次
- 状态持久化在脚本同目录的 `calendar_state.json` 中
- 如果初始化失败，可根据返回的 error 信息排查
- **`calendar_state.json` 包含运行时数据，不应发布到公开仓库**

### 初始化所需权限（应用身份）

首次初始化 `init` 命令时，除了日历权限外，还需要 IM 权限（因为要获取聊天成员信息）。确保飞书开发者后台已开通以下 **应用身份** 权限：

| 权限 | 用途 |
|------|------|
| `calendar:calendar` | 日历读写 |
| `calendar:calendar:create` | 创建日历 |
| `im:chat:readonly` | 读取群信息 |
| `im:chat` | 群管理读写 |

如果只开通了日历权限就执行 init，会报"获取聊天成员失败"，需要补开 IM 权限。

## Python 脚本模式

脚本依赖 `requests` 库（非 `urllib`），使用前确保已安装。

### Pitfalls

| # | 问题 | 解决方案 |
|---|------|---------|
| 1 | `execute_code` 中 `~` 路径双重展开 | 用绝对路径 |
| 2 | 初始化缺 IM 权限报错 | 补开 `im:chat:readonly` + `im:chat`（应用身份） |
| 3 | `calendar_state.json` 泄露真实 ID | 不发布此文件 |
| 4 | 脚本依赖 `requests` | 非 urllib，需确保安装 |
