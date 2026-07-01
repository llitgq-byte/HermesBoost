# SysTools-feishu-calendar

**🇨🇳 中文** · [English](README.md)

---

<p align="center">
  <strong>⚡ 把下面这段复制给你的 Agent → Agent 会自动完成安装：</strong>
</p>

<p align="center">
  <code>Download all files from https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-feishu-calendar/feishu-calendar, place them under $HERMES_HOME/skills/Always/tools-feishu-calendar/, ensure the <code>requests</code> package is installed (<code>pip install requests</code>), then restart the gateway. This is the Feishu Calendar skill — 通过飞书 API 管理共享日历日程（创建/查询/删除），一次性初始化后持久化状态。</code>
</p>

---

适用于 Hermes Agent 的**飞书日历管理 Skill**。提供 CLI 工具在应用拥有的共享日历上创建、列出和删除日程。一次性设置后，所有 Agent 共享同一个日历。

## 为什么有这个 Skill？

Hermes Agent 需要可靠的方式管理日历日程——提醒、会议、计划任务——通过飞书日历 API。初始化流程处理了棘手部分（创建日历、ACL 授权、聊天成员发现），Agent 只需调用简单的 CLI 命令。

## 核心功能

- **一次性初始化** — 创建应用拥有的日历，通过 chat_id 自动发现用户，设置 ACL 权限
- **CLI 操作** — `status`、`init`、`list`、`create`、`delete`、`reset` 子命令
- **持久化状态** — calendar ID 和用户信息保存到 `calendar_state.json`（自动管理）
- **灵活的时间输入** — 通过分钟数或显式结束时间指定持续时间
- **多来源 chat_id 发现** — 检查环境变量、`.env` 文件和会话上下文

## 工作原理

1. 首次使用时，Agent 询问用户日历名称和 chat_id
2. `init` 命令创建日历，通过聊天成员 API 发现用户，并授权 ACL 访问
3. 后续操作（list/create/delete）使用持久化的 `calendar_state.json`
4. 所有命令返回 JSON，便于 Agent 解析

## 安装

1. 从 [`feishu-calendar/`](https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-feishu-calendar/feishu-calendar) 目录下载所有文件
2. 放到 `$HERMES_HOME/skills/Always/tools-feishu-calendar/` 下
3. 安装 `requests` 依赖：`pip install requests`
4. 确保你的 profile `.env` 中设置了 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET`
5. 重启 gateway

## 文件结构

```
SysTools-feishu-calendar/
├── README.md                         ← 英文文档
├── README.zh.md                      ← 本文件
└── feishu-calendar/
    ├── SKILL.md                      ← Agent 指令文件
    └── scripts/
        └── calendar_tool.py           ← CLI 工具（依赖 requests）
```

## 常见问题

| 问题 | 解决方案 |
|------|---------|
| `execute_code` 路径解析失败 | 用绝对路径代替 `~` |
| 初始化报"获取聊天成员失败" | 飞书开发者后台补开 `im:chat:readonly` + `im:chat` 权限（应用身份） |
| 权限错误 | 开通 `calendar:calendar` 和 `calendar:calendar:create` 权限（应用身份） |

## License

MIT
