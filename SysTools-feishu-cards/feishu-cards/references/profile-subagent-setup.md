# Profile/子 Agent 飞书权限配置指南

## 问题背景

子 Agent（Profile）无法访问飞书文档/表格，即使主 Agent 可以正常访问。

## 根因分析

| 检查项 | 主 Agent | 子 Agent (Profile) | 结果 |
|--------|---------|-------------------|------|
| `FEISHU_APP_ID` | `cli_xxxxxx` | `cli_yyyyyy` | **不同应用** |
| `toolsets` | `hermes-cli` + 平台工具 | `hermes-cli` | **缺少 feishu 工具** |
| 应用权限 | 已开通 | 未开通 | **权限不共享** |

## 解决方案

### 方案1：共享主应用凭证（推荐）

让子 Agent 使用与主 Agent 相同的飞书应用：

```bash
# 编辑 ~/.hermes/profiles/<profile_name>/.env
FEISHU_APP_ID=cli_xxxxxx          # 与主 Agent 相同
FEISHU_APP_SECRET=****  # 与主 Agent 相同
```

**优点：**
- 权限共享，主应用能访问的子 Agent 都能访问
- 无需重复配置权限
- 文档/表格只需授权一次

**缺点：**
- 两个 Agent 共用同一个飞书机器人身份
- 无法区分消息来源

### 方案2：添加 feishu toolsets + 独立应用（推荐用于 Stock 等独立场景）

1. **修改 config.yaml 添加 toolsets：**

```yaml
# ~/.hermes/profiles/<profile_name>/config.yaml
toolsets:
- hermes-cli
- feishu_doc      # ← 读取飞书文档
- feishu_drive    # ← 文档评论操作
```

**注意：** 必须同时添加 `feishu_doc` 和 `feishu_drive`，不能只写 `feishu`（不存在这个 toolset）。

**常见错误：** 只添加 `feishu` 会导致 toolset 找不到，Agent 仍然无法使用飞书工具。

2. **给子 Agent 应用单独开通权限：**
   - 飞书开放平台 → 找到子 Agent 的 `FEISHU_APP_ID`
   - 权限管理 → 添加 `bitable:app`、`docx:document`、`drive:drive`
   - 版本管理与发布 → 创建新版本 → 申请发布

3. **给文档/表格授权：**
   - 打开目标文档/表格
   - 右上角「···」→「添加文档应用」
   - 搜索子 Agent 应用名称 →「可编辑」→「添加」

**优点：**
- 两个 Agent 完全独立
- 可以区分消息来源

**缺点：**
- 需要维护两套权限
- 每个文档/表格需要授权两次

## 快速诊断命令

```bash
# 检查子 Agent 的飞书配置
cat ~/.hermes/profiles/<profile_name>/.env | grep FEISHU

# 检查子 Agent 的 toolsets
cat ~/.hermes/profiles/<profile_name>/config.yaml | grep -A 5 "toolsets:"

# 对比主 Agent 和子 Agent 的 APP_ID
echo "主 Agent:" && cat ~/.hermes/.env | grep FEISHU_APP_ID
echo "子 Agent:" && cat ~/.hermes/profiles/<profile_name>/.env | grep FEISHU_APP_ID
```

## 验证步骤

1. 确认子 Agent 的 `.env` 中有正确的 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET`
2. 确认子 Agent 的 `config.yaml` 中 `toolsets` 包含 `feishu_doc` 和 `feishu_drive`
3. 确认应用已开通所需权限（bitable/docx/drive）
4. 确认文档/表格已给应用授权
5. 重启子 Agent 的 gateway：`hermes restart gateway --profile <profile_name>`
6. 测试读取/写入操作

## 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| "Cannot find feishu toolset" | config.yaml 缺少 `feishu_doc`/`feishu_drive` | 添加 `- feishu_doc` 和 `- feishu_drive` 到 toolsets |
| "Token invalid" | APP_ID/APP_SECRET 错误 | 检查 .env 中的凭证 |
| "Missing permission" | 应用未开通权限 | 去飞书开放平台添加权限 |
| "App not authorized" | 文档/表格未给应用授权 | 添加文档应用并授予权限 |
| "Module 'utils' has no attribute..." | Plugin 模块名冲突 | 见 `cross-platform-portability.md` 第 11.4 节 |

## MCP 配置注意事项

当为子 Agent 配置飞书 MCP 时，**必须直接写死凭证值**，不能使用 `${FEISHU_APP_ID}` 变量引用：

```yaml
# ✅ 正确：直接写死值
mcp_servers:
  lark:
    command: npx
    args:
    - "@larksuite/lark-mcp"
    env:
      LARK_APP_ID: cli_yyyyyy
      LARK_APP_SECRET: ****

# ❌ 错误：YAML 不支持这种变量引用
    env:
      LARK_APP_ID: ${FEISHU_APP_ID}
      LARK_APP_SECRET: ${FEISHU_APP_SECRET}
```

Hermes 的 MCP 配置不会自动解析 `.env` 文件中的变量，使用 `${}` 语法会导致 MCP 工具无法认证。
