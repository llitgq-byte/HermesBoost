# 飞书 API 常见错误码参考

## 消息发送相关

| 错误码 | 含义 | 修复方式 |
|--------|------|---------|
| 0 | 成功 | - |
| 230001 | receive_id 参数错误 | 检查 receive_id 是否正确 |
| 230002 | Bot/User can NOT be out of the chat | `open_id` 不能用于 DM 发送（飞书 DM 的 chat_id ≠ 用户的 open_id）。**对于 DM，始终使用 `receive_id_type="chat_id"` 并传入 DM 会话的 `chat_id`**（格式：`oc_xxx`），不要传用户的 `open_id`。获取 DM chat_id：从 `channel_directory` 或会话上下文，格式为 `oc_xxx`。另见第八部分错误表"open_id 跨应用发送"条目 |
| 230009 | 卡片 JSON 格式错误 | 检查 JSON 结构是否合法，特殊字符是否转义 |
| 230099 | 卡片内容超限 | 缩减内容或拆分为多张卡片 |
| 232001 | tenant_access_token 过期 | 重新认证（SDK 自动处理） |
| 99991400 | request_body 格式错误 | 检查请求体 JSON 结构 |
| 99991401 | 缺少必填参数 | 检查 receive_id、msg_type、content |
| 99991663 | 无权发送到该会话 | 检查机器人是否在群内 |
| 99992361 | open_id cross app not allowed | 飞书 Open Platform 限制：`open_id` 不能跨应用使用。如果机器人要给另一个 app 的用户发消息，必须用该用户在本 bot 下的 `chat_id`（DM 会话），而不是用户的 `open_id`。**解决：换用 DM 的 `chat_id` + `receive_id_type="chat_id"`** |
| 99991664 | 消息内容超限 | 检查 content 大小 |

## 卡片 JSON 2.0 相关

| 错误码 | 含义 | 修复方式 |
|--------|------|---------|
| 200861 | unsupported tag note | JSON 2.0 不支持 note 标签，改用 markdown |
| 200862 | 组件数量超限 | 减少组件数（上限 200） |
| 200863 | table 数量超限 | 减少表格数（上限 5） |
| 200864 | table 列数超限 | 减少列数（上限 50） |

## 认证相关

| 错误码 | 含义 | 修复方式 |
|--------|------|---------|
| 10001 | app_id 或 app_secret 无效 | 检查 FEISHU_APP_ID / FEISHU_APP_SECRET 环境变量 |
| 10002 | app_id 不存在 | 确认 App ID 是否正确 |
| 10003 | app_secret 错误 | 确认 App Secret 是否正确 |

## 通用排查步骤

1. 先确认环境变量 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET` 是否正确
2. 确认 `receive_id` 对应的聊天窗口存在且机器人在范围内
3. 将卡片 JSON 单独 print 出来检查格式
4. 用飞书卡片搭建工具（https://open.feishu.cn/cardkit）验证 JSON 是否合法
