# SysTools-feishu-cards

**🇨🇳 中文** · [English](README.md)

---

<p align="center">
  <strong>⚡ 复制以下内容给你的 Agent → Agent 自动配置一切：</strong>
</p>

<p align="center">
  <code>下载 https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-feishu-cards/feishu-cards 下的全部文件，放入 $HERMES_HOME/skills/Always/feishu-cards/，将 bundled/plugins/feishu-table-card/ 复制到 $HERMES_HOME/plugins/feishu-table-card/，在 config.yaml 的 plugins.enabled 中添加 feishu-table-card，然后重启 gateway。这是 feishu-table-card 插件——自动将回复中的 Markdown 表格转换为飞书交互式卡片。</code>
</p>

---

自动将飞书回复中的 Markdown 表格、标题、代码块等富文本格式转换为飞书 `interactive` 卡片（JSON 2.0 schema）。不再看到原始的 `|...|` 管道文本——每张表格都以飞书表组件正确渲染，支持排序、分页和列宽自适应。

两层保护：Agent 检测到输出含表格时主动调用 `send_card.py` 发送卡片，Plugin 钩子（`transform_llm_output`）自动兜底拦截已完成回复中的表格。

## 为什么需要？

飞书默认消息格式会把 Markdown 表格渲染成纯文本管道符——完全不可读。本模块在两层解决：

1. **Skill** — Agent 读取 SKILL.md 工作流，检测输出中的表格，调用 `send_card.py` 发送格式化的卡片。
2. **Plugin** — `transform_llm_output` 钩子自动拦截已完成回复中的表格，即使 Agent 忘记也会兜底。

## 核心特性

- 完整 Markdown 支持：表格、标题、代码块、列表、引用、分割线、链接、图片
- 零硬编码路径 — 通过 `feishu_card_utils.py` 动态推断，跨平台通用
- 自动拆分 — 超大内容自动拆成多张卡片
- 全角清洗 — `｜` → `|`、`－` → `-`
- Profile 感知 — 多 Agent 环境下正确处理凭证和路由
- 跨平台 — 纯 `pathlib`

## 安装

1. 下载 `feishu-cards/` 下全部文件
2. 放到 `$HERMES_HOME/skills/Always/feishu-cards/`
3. 将 `bundled/plugins/feishu-table-card/` 复制到 `$HERMES_HOME/plugins/feishu-table-card/`
4. 在 `config.yaml` 的 `plugins.enabled` 中添加 `feishu-table-card`
5. 重启 Gateway：`hermes restart gateway`

## 文件结构

```
SysTools-feishu-cards/
├── README.md                              # 英文文档
├── README.zh.md                           # 本文档（中文）
└── feishu-cards/
    ├── SKILL.md                           # Agent 指令
    ├── references/                         # 详细指南（9 份）
    ├── templates/                          # 核心：send_card.py + utils
    ├── scripts/                            # 安装与辅助脚本
    └── bundled/plugins/feishu-table-card/
        ├── __init__.py                    # 插件钩子（transform_llm_output）
        └── plugin.yaml
```

## 常见问题

| 问题 | 解决 |
|------|------|
| 表格显示为原始 `\|...\|` | 插件未加载：`hermes plugins enable feishu-table-card` + 重启 |
| 卡片发到错误窗口 | 检查 hook 上下文中的 `receive_id` |
| `ModuleNotFoundError: lark_oapi` | 用 hermes-agent venv 的 python，不是系统 python |
| `'PluginContext' has no attribute 'register'` | 更新插件为新版 `register(ctx)` API |
| 所有 Agent 卡片串到同一窗口 | 移除插件中硬编码的 ID，只用环境变量 |

## 许可证

MIT
