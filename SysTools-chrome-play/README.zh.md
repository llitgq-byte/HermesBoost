# SysTools-chrome-play

**🇨🇳 中文** · [English](README.md)

---

<p align="center">
  <strong>⚡ 把下面这段复制给你的 Agent → Agent 会自动完成安装：</strong>
</p>

<p align="center">
  <code>Download all files from https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-chrome-play/chrome-play, place them under $HERMES_HOME/skills/Always/tools-chrome-play/, add <code>browser</code> to the enabled toolsets list, set <code>browser.cdp_url: http://127.0.0.1:9222</code> in config.yaml, then restart the gateway. This is the Chrome Play skill — 通过 CDP 协议控制本地 Chrome 浏览器，实现网页自动化、数据提取和页面交互。</code>
</p>

---

适用于 Hermes Agent 的**本地 Chrome 浏览器自动化 Skill**。通过 Chrome DevTools Protocol (CDP) 连接本地运行的 Chrome 实例，实现导航、点击、输入、数据提取及任意网页交互——包括 GitHub 等 SPA 网站的复杂操作。

## 为什么有这个 Skill？

浏览器自动化是 AI Agent 最强大的能力之一，但暗坑无数：SPA 导航静默失败、CodeMirror 编辑器追加而非替换、文件上传被 CDP HTTP 端点阻止、GitHub sudo mode 切换页面后表单状态丢失……本 Skill 记录了 13+ 个坑点及经过验证的解决方案，让 Agent 不再浪费时间重新发现这些问题。

## 核心功能

- **Chrome 启动指南** — macOS、Linux、Windows 完整启动说明（终端、登录项、systemd、LaunchAgent）
- **Hermes 配置** — CDP URL 设置、browser 工具集启用
- **10 个浏览器工具文档** — navigate、snapshot、click、type、scroll、press、console、vision、CDP、back
- **SPA 导航模式** — JS click 模板、等待策略、跨板块导航、Vue/React 输入处理
- **CodeMirror 6 深度指南** — execCommand insertText、代理对 emoji 编码、剪贴板粘贴备选、删除重建恢复
- **文件上传变通方案** — DataTransfer 对象、混合内容限制、决策树
- **GitHub Web UI 参考** — 个人资料编辑、目录删除、sudo mode、CSP 约束
- **13 个已记录坑点**及解决方案

## 工作原理

1. 启动 Chrome 时添加 `--remote-debugging-port=9222 --user-data-dir=~/chrome-hermes-profile`
2. 配置 Hermes：`browser.cdp_url: http://127.0.0.1:9222`
3. Agent 通过 `browser_navigate()` 连接，然后通过 snapshot/click/type/console 交互
4. SPA 页面使用 JavaScript click（IIFE 包裹）代替 `browser_click`
5. 复杂编辑器（CodeMirror 6）使用 `execCommand('insertText')` + 代理对编码

## 安装

### 第一步：启动 Chrome 并开启 CDP

```bash
# macOS
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/chrome-hermes-profile" &

# 验证
curl http://127.0.0.1:9222/json/version
```

### 第二步：配置 Hermes

```yaml
# config.yaml
browser:
  cdp_url: http://127.0.0.1:9222
```

启用 browser 工具集：`hermes tools enable browser`

### 第三步：安装 Skill

1. 从 [`chrome-play/`](https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-chrome-play/chrome-play) 目录下载所有文件
2. 放到 `$HERMES_HOME/skills/Always/tools-chrome-play/` 下
3. 重启 gateway

## 文件结构

```
SysTools-chrome-play/
├── README.md                         ← 英文文档
├── README.zh.md                      ← 本文件
└── chrome-play/
    ├── SKILL.md                      ← Agent 指令文件（完整指南 + 13 个坑点）
    ├── references/
    │   ├── file-upload-workarounds.md       ← 文件上传技术与限制
    │   ├── github-browser-edit-pitfalls.md   ← CodeMirror / 编辑器坑点
    │   ├── github-bilingual-readme.md        ← 双语 README 策略
    │   ├── github-csp-constraints.md         ← GitHub CSP + Web UI 决策树
    │   └── github-profile-editing.md         ← GitHub 个人资料优化
    └── templates/
        └── github-profile-readme.md          ← Profile README 模板（Tokyo Night 配色）
```

## 常见问题

| 问题 | 解决方案 |
|------|---------|
| `browser_navigate` 连接失败 | 检查 Chrome 是否以 `--remote-debugging-port=9222` 启动 |
| 端口被占用 | `lsof -i :9222` — 关闭现有 Chrome 或使用其他端口 |
| Profile 锁冲突 | 确保 `--user-data-dir` 与主 Chrome profile 不同 |
| SPA 点击静默失败 | 用 IIFE 包裹的 JS click（见 SKILL.md §3.2） |
| 文件上传不工作 | CDP HTTP 端点限制 — 用 DataTransfer 或手动上传 |

## License

MIT
