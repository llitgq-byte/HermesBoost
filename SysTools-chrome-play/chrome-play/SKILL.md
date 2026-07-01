---
name: tools-chrome-play
description: |
  通过本地 Chrome 浏览器（CDP 协议）操作网页的通用指南。
  适用于任何需要打开网页、提取数据、点击交互、SPA 导航的场景。
  核心原则：Chrome 始终保持运行，不要重复启动。
version: "1.0.0"
triggers:
  - 操作浏览器
  - 打开网页
  - 浏览器获取数据
  - Chrome
  - browser_navigate
  - browser_cdp
  - local-chrome
---

# 本地 Chrome 浏览器操作指南

通过本地已运行的 Chrome 浏览器（CDP 协议）打开网页、提取数据、点击页面元素。

---

## 一、浏览器启动与连接

### 1.1 原理概述

Hermes 通过 **Chrome DevTools Protocol (CDP)** 连接本地 Chrome 浏览器。CDP 是 Chrome 内置的调试协议，通常用于 Chrome DevTools 的后台通信。通过在 Chrome 启动时开启 `--remote-debugging-port` 参数，外部程序（如 Hermes）可以通过 HTTP/WebSocket 连接并控制浏览器。

**核心概念：**
- **调试端口（Debug Port）：** Chrome 启动时监听一个 TCP 端口（默认 `9222`），Hermes 通过该端口发送 CDP 指令
- **用户数据目录（User Data Dir）：** 指定独立的 profile 目录，避免与日常使用的 Chrome 冲突
- **CDP URL：** Hermes 配置中的 `browser.cdp_url`，格式为 `http://127.0.0.1:9222`

### 1.2 前提条件

| 项目 | 要求 |
|------|------|
| Chrome 浏览器 | Google Chrome、Chromium、Brave 或 Microsoft Edge 均可 |
| 端口 | 一个未被占用的本地端口（推荐 `9222`） |
| 独立 Profile 目录 | 必须使用独立目录，不能与主浏览器共享 |

### 1.3 启动 Chrome（macOS）

**方法 A：终端命令启动（推荐）**

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/chrome-hermes-profile" &
```

> `&` 放在末尾让 Chrome 在后台运行。如果不想显示终端输出，用 `nohup ... &>/dev/null &`。

**方法 B：macOS 自动登录项（持久化）**

如果希望 Chrome 在系统启动时自动运行：

1. 打开 **系统设置 → 通用 → 登录项**
2. 点击 **+** 添加应用
3. 选择 Chrome，在"选项"中填入参数：
   ```
   --remote-debugging-port=9222 --user-data-dir=$HOME/chrome-hermes-profile
   ```
4. 确保勾选"登录时打开"

> ⚠️ 确保 Chrome 主进程已经完全退出再添加登录项，否则可能创建新的 Chrome 实例。

**方法 C：LaunchAgent（高级）**

创建 `~/Library/LaunchAgents/com.hermes.chrome.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hermes.chrome</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Applications/Google Chrome.app/Contents/MacOS/Google Chrome</string>
        <string>--remote-debugging-port=9222</string>
        <string>--user-data-dir=/Users/YOUR_USERNAME/chrome-hermes-profile</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

然后：`launchctl load ~/Library/LaunchAgents/com.hermes.chrome.plist`

> ⚠️ 将 `YOUR_USERNAME` 替换为实际用户名。`KeepAlive` 确保 Chrome 意外退出后自动重启。

### 1.4 启动 Chrome（Linux）

```bash
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/chrome-hermes-profile" \
  --no-first-run \
  --no-default-browser-check &
```

如果 Chrome 安装路径不同：
- Chromium：`chromium-browser` 或 `chromium`
- Brave：`brave-browser`
- Edge：`microsoft-edge`

**systemd 用户服务（持久化）：**

创建 `~/.config/systemd/user/hermes-chrome.service`：

```ini
[Unit]
Description=Hermes Chrome CDP Browser
After=graphical-session.target

[Service]
ExecStart=/usr/bin/google-chrome --remote-debugging-port=9222 --user-data-dir=%h/chrome-hermes-profile --no-first-run --no-default-browser-check
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now hermes-chrome
```

### 1.5 启动 Chrome（Windows）

```powershell
Start-Process "chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="$env:USERPROFILE\chrome-hermes-profile"
```

或创建快捷方式，在"目标"栏末尾添加参数：
```
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\chrome-hermes-profile"
```

### 1.6 验证 CDP 连接

Chrome 启动后，在终端或浏览器中访问：

```
http://127.0.0.1:9222/json/version
```

正常响应示例：
```json
{
  "Browser": "Chrome/126.0.6478.114",
  "Protocol-Version": "1.3",
  "User-Agent": "...",
  "V8-Version": "12.6.228.28",
  "WebKit-Version": "537.36",
  "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/browser/..."
}
```

> 如果无法访问，检查：
> - Chrome 是否已启动并带有 `--remote-debugging-port` 参数
> - 端口是否被其他程序占用（`lsof -i :9222`）
> - 是否有防火墙拦截

### 1.7 配置 Hermes

在 Hermes 的 `config.yaml` 中添加：

```yaml
browser:
  cdp_url: http://127.0.0.1:9222
  inactivity_timeout: 120
```

并确保 `browser` 工具集已启用：

```bash
hermes tools enable browser
```

或在 `config.yaml` 的 `toolsets` 中添加 `browser`。

### 1.8 ⛔ 禁止事项

- **禁止重复启动 Chrome 进程**（会报端口冲突或创建新 profile）
- **禁止使用 Browserbase 或云端浏览器**（没有本地登录态）
- **禁止使用 MCP Chrome DevTools 工具**（找的是默认 Chrome 路径的 DevToolsActivePort，连不上自定义 profile 的 Chrome）
- **禁止用与主 Chrome 相同的 `--user-data-dir`**（会导致锁文件冲突，两个 Chrome 实例无法同时运行）

### 1.9 ⚠️ Profile 隔离（重要限制）

Hermes 的 Chrome 使用**独立 profile 目录**（如 `~/chrome-hermes-profile`），与用户的**主 Chrome profile** 完全隔离：

- ❌ **不会**继承用户主 Chrome 的登录态（cookies、session）
- ❌ **不会**继承用户主 Chrome 的书签、密码、扩展
- ✅ 适合需要"干净"浏览器的自动化场景
- ❌ **不适合**需要用户已登录态的操作（如操作用户的 GitHub、社交媒体等）

**应对策略：**
- 需要用户登录态时 → 让用户提供账号信息，或通过 API/CLI 工具操作
- 需要操作用户已登录的网页 → 让用户手动在主浏览器操作，或指导用户在 Hermes Chrome 中重新登录

### 1.10 ⚠️ 登录态验证流程（用户声称已登录时）

当用户说"我已经登录了"或"你可以接管我的浏览器"时，**不要直接假设未登录**。按以下流程验证：

```
步骤 1：导航到目标网站的首页/仪表盘（不是登录页）
  browser_navigate(url='https://目标网站.com/')

步骤 2：检查快照判断登录态
  → 显示 Dashboard / 用户头像 / 个人内容 → 已登录，直接操作
  → 显示 Sign in / Login 页面 → 未登录，进入步骤 3

步骤 3：向用户确认 Profile 隔离限制（仅此时才解释）
  "Hermes 的 Chrome 使用独立 profile，没有你的登录态。
   方案 A：你在 Hermes Chrome 里登录一次
   方案 B：告诉我你的用户名，通过公开页面操作"
```

**常见误区：**
- ❌ 用户说已登录 → 直接导航到 settings 页面 → 被重定向到登录页 → 误判为未登录
- ✅ 用户说已登录 → 先导航到首页 → 看到 Dashboard → 确认已登录 → 继续操作

---

## 二、工具一览

### 2.1 browser_navigate — 导航到 URL

```
browser_navigate(url='https://example.com')
```

连接本地 Chrome 并打开页面。返回页面快照，包含可交互元素和 ref ID（如 `@e1`、`@e2`）。

> 这是连接浏览器的入口。首次调用即建立 CDP 连接。

### 2.2 browser_snapshot — 获取页面快照

```
browser_snapshot()           # 紧凑视图：交互元素 + ref ID
browser_snapshot(full=true)  # 完整页面内容
```

> ⚠️ `full=true` 有约 **8000 字符限制**，超长页面会被截断。长页面解决方案见 §六。

### 2.3 browser_click — 点击元素

```
browser_click(ref='@e5')     # 点击 ref ID 对应的元素
```

> ⚠️ **SPA 页面禁止使用 `browser_click` 进行导航**，会静默失败（返回 success 但 URL/DOM 不变）。SPA 导航用 JS click（见 §三）。

### 2.4 browser_type — 输入文本

```
browser_type(ref='@e3', text='要输入的文本')
```

### 2.5 browser_scroll — 滚动页面

```
browser_scroll(direction='down')   # 向下滚动
browser_scroll(direction='up')     # 向上滚动
```

### 2.6 browser_press — 按键

```
browser_press(key='Enter')    # 提交表单
browser_press(key='Escape')   # 关闭弹窗
```

### 2.7 browser_console — 执行 JS / 查看控制台

```
# 执行 JS 表达式并获取返回值
browser_console(expression='document.title')

# 获取控制台日志（log/warn/error）
browser_console()
```

### 2.8 browser_vision — 视觉截图

```
browser_vision(question='页面上显示了什么内容？')
```

当快照不够直观时，用截图确认页面实际外观。

### 2.9 browser_cdp — 底层 CDP 协议

当内置工具不够用时，直接通过 CDP 协议操作：

```
# 获取所有标签页
browser_cdp(method='Target.getTargets', params={})

# 在指定标签执行 JS
browser_cdp(method='Runtime.evaluate', params={'expression': '...'}, target_id='<tab_id>')

# 在指定标签导航
browser_cdp(method='Page.navigate', params={'url': '...'}, target_id='<tab_id>')
```

### 2.10 browser_back — 后退

```
browser_back()
```

---

## 三、SPA 单页应用导航（⚠️ 重要）

SPA（Single Page Application）点击导航后页面不会完全刷新，DOM 异步渲染，需要特殊处理。

### 3.1 导航优先级

| 优先级 | 方式 | 适用场景 |
|--------|------|----------|
| 1️⃣ | `browser_navigate(url)` | 打开页面、回首页、任何需要完整刷新的场景 |
| 2️⃣ | JS click（见下方） | SPA 内部导航：Tab 切换、侧边栏导航 |
| 3️⃣ | `browser_click(ref)` | 仅限非 SPA 页面的普通链接/按钮 |

> ⚠️ **SPA 内部导航禁止使用 `browser_click`。** 会「静默失败」——返回 success 但 URL 不变、DOM 不更新。

### 3.2 JS click 标准模板

所有 SPA 导航统一使用 IIFE 包裹，避免 let/const 重复声明：

```javascript
(() => {
  const items = document.querySelectorAll('选择器');
  items.forEach(item => {
    if (item.textContent.trim() === '目标文字') item.click();
  });
  return 'clicked';
})()
```

### 3.3 SPA 等待规则

JS click 后必须等待异步渲染完成才能提取数据。等待时长视网站而定（通常 500ms–2s）：

```javascript
// 推荐模式：click + 等待 + 提取 三合一
(() => {
  const tabs = document.querySelectorAll('.tab-item');
  tabs.forEach(t => { if(t.textContent.trim() === '目标tab') t.click(); });
  return new Promise(r => setTimeout(() => r('done'), 800));
})()
// 下一轮 browser_console 提取数据
```

### 3.4 跨一级板块导航

某些 SPA 框架（如 Vue/React）从一级板块直接跳到另一个一级板块，目标板块可能不会正确渲染。

**正确做法：切换一级板块前，先 `browser_navigate` 回首页，再 JS click 进入目标板块。**

```
❌ 板块A → JS click "板块B"（可能渲染异常）
✅ browser_navigate(首页) → JS click "板块B"（正常渲染）
```

同板块内的子导航切换不需要回首页。

### 3.5 Vue/React 输入框特殊处理

框架响应式表单可能不响应 `browser_type`，需要用 JS 原生 setter 绕过：

```javascript
(() => {
  const input = document.querySelector('输入框选择器');
  const nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
  nativeSetter.call(input, '要输入的值');
  input.dispatchEvent(new Event('input', { bubbles: true }));
  return 'set';
})()
```

### 3.6 点击视口外的按钮（下方折叠区域）

当目标按钮在页面底部、`browser_snapshot` 中不可见时（如 GitHub 设置页的 "Update profile"），用 JS 全局搜索并点击：

```javascript
(() => {
  const buttons = document.querySelectorAll('button');
  for (const btn of buttons) {
    if (btn.textContent.trim() === '目标按钮文字') {
      btn.click();
      return 'clicked';
    }
  }
  return 'not found';
})()
```

> ⚠️ 不要对 SPA 导航按钮使用此模式（见 §3.1）。仅适用于传统表单提交按钮。

### 3.7 设置 `<select>` 下拉框值

`browser_type` 无法操作 `<select>` 元素。用 JS 原生 setter + change 事件：

```javascript
(() => {
  const select = document.querySelector('select#目标选择器');
  if (select) {
    select.value = '目标值';
    select.dispatchEvent(new Event('change', { bubbles: true }));
    return 'set';
  }
  return 'not found';
})()
```

### 3.8 向 CodeMirror 6 编辑器写入内容（⚠️ GitHub 等网站）

GitHub 的文件编辑器使用 **CodeMirror 6**（不是 Monaco）。直接设置 `textContent` 或使用 Monaco API 均无效。

#### ✅ 推荐方法：execCommand insertText（单步、可靠）

> ⚠️ **关键限制：`browser_type` 在 GitHub CodeMirror 6 编辑器上是 APPEND 行为！**
> 多次调用 `browser_type` 不会覆盖已有内容，而是**追加**到末尾。这会导致文件内容被重复叠加（如 3 次调用 = 3 倍重复内容）。
> ⚠️ 永远不要用 `browser_type` 直接向 GitHub 文件编辑器写入大量内容。
> ✅ **正确方案**：用下方 `execCommand` 的 JS 写法（全选后一次性替换）。

```javascript
(() => {
  const cmContent = document.querySelector('.cm-content');
  if (!cmContent) return 'no CodeMirror editor found';
  cmContent.focus();
  document.execCommand('selectAll', false, null);
  document.execCommand('insertText', false, '要写入的完整内容（用 \\u{1F44B} 语法保留 emoji）');
  return 'done, length: ' + cmContent.textContent.length;
})()
```

**优势：** 单步完成，不需要 `browser_press`，无需多轮工具调用。实测对 CodeMirror 6 可靠。

**⚠️ Emoji 语法要求：** `browser_console` 中 `\\u{XXXX}`（ES6 大括号语法）**不会被 JS 引擎正确解析**，会作为字面文本写入。**必须使用 JSON 代理对（surrogate pairs）：**

| Emoji | ❌ 不工作（字面文本） | ✅ 正确（代理对） |
|-------|----------------------|------------------|
| 👋 | `\\u{1F44B}` | `\\ud83d\\udc4b` |
| 🤖 | `\\u{1F916}` | `\\ud83e\\udd16` |
| 🚀 | `\\u{1F680}` | `\\ud83d\\ude80` |
| ❤️ | `\\u{2764}\\u{FE0F}` | `\\u2764\\ufe0f` |

**查找代理对的方法：** `codePoint.toString(16)` → 查 [Unicode surrogate pair table](https://www.compart.com/en/unicode/)，或用 Python：`[hex(c) for c in 'emojitext'.encode('utf-16-be')]`

**备选方案：** 如果不想手动编码 emoji，用剪贴板粘贴法（`navigator.clipboard.writeText('含emoji内容')` + `Meta+a` + `Meta+v`），见下方备选方法。

> 📋 **实操 pitfalls 汇总（browser_type 追加、SPA 残留、变量重复声明等）见 `references/github-browser-edit-pitfalls.md`**

#### ✅ 备选方法：剪贴板粘贴（推荐用于含 emoji 的长文本）

当内容含大量 emoji 且不想手动编码代理对时：

```javascript
// 步骤 1：将内容写入剪贴板（字面 emoji 在 writeText 中正常工作）
navigator.clipboard.writeText('你的完整内容含 emoji 👋🚀...').then(() => 'clipboard set');

// 步骤 2：通过 browser_press 工具全选 + 粘贴
// browser_press(key='Meta+a')   → 全选
// browser_press(key='Meta+v')   → 粘贴
```

**⚠️ 此方法有时会静默失败** — `Meta+v` 执行了但编辑器内容未变（焦点不在正确位置）。如果粘贴后编辑器内容没变且 Commit 按钮仍 disabled，改用 execCommand 方法。

**推荐策略：** 短文本 / 少量 emoji → execCommand + 代理对；长文本 / 大量 emoji → 剪贴板粘贴。

#### ⚠️ 编辑失败时的终极回退：删除重建

当 CodeMirror 6 编辑器内容已损坏（重复叠加、截断、描述丢失等），继续 `execCommand` 修复往往会让问题更严重——全选替换后内容可能仍旧，或内容与预期不符。

**正确流程：**

```
① 确认内容已损坏（browser_console 检查 lines 数量远大于预期）
② 回到文件视图 → "More file actions" (…) → Delete file → Commit
③ "Create new file" → 相同文件名 → 输入干净内容 → Commit
```

> ✅ **为什么有效：** 绕过 CodeMirror 编辑器，从零开始创建文件，不存在旧状态残留或追加风险。

> ⏱️ **删除重建 vs 编辑修复 决策树：**
> - 文件内容干净，只需小改 → `execCommand` 全选替换
> - 文件内容已损坏（重复/截断/乱码）→ **删除重建**（不要继续编辑）
> - `execCommand` 替换后通过 browser_console 验证仍不对 → **删除重建**

#### ❌ 失败过的方案（不要重试）

- 直接设 `cmContent.textContent` — DOM 变了但 CodeMirror 内部状态不同步，提交时内容为空
- Monaco API / `window.monaco` — GitHub 用的是 CodeMirror 6，没有 Monaco
- `DataTransfer` + `drop` 事件 — 不生效
- GitHub API `fetch('api.github.com/repos/...')` — 浏览器内 fetch/XHR 均被 CORS/CSRF 拦截
- InputEvent + `data: 'insertText'` — 不触发 CodeMirror handler
- CodeMirror 6 View dispatch — 无法从控制台获取 View 实例
- 反复 `browser_type`/`browser_press(Ctrl+a)` + `browser_type` 尝试覆盖 — **每次调用都追加，3次调用=3倍重复**

#### ⚠️ browser_console 变量作用域陷阱

`browser_console` 的 JS 上下文在**同一页面**的多次调用间保持持久化。`let`/`const` 声明的变量**不能重复声明**：

```
// 第一次调用
browser_console(expression='let cmContent = document.querySelector(...)')

// 第二次调用 — ❌ SyntaxError: Identifier 'cmContent' has already been declared
browser_console(expression='let cmContent = document.querySelector(...)')
```

**解决方法（任选一种）：**
- ✅ **IIFE 包裹**（推荐）：`(() => { let x = ...; return x; })()`
- ✅ 换变量名：`let cmEd2 = ...`
- ✅ 用 `var`（允许重复声明）

#### 验证写入成功

```javascript
(() => {
  const cmContent = document.querySelector('.cm-content');
  const commitBtn = [...document.querySelectorAll('button')].find(b => b.textContent.includes('Commit'));
  return JSON.stringify({
    text: cmContent.textContent.substring(0, 60),
    lines: cmContent.querySelectorAll('.cm-line').length,
    commitDisabled: commitBtn ? commitBtn.disabled : 'not found'
  });
})()
```

### 3.9 GitHub API 浏览器内调用限制

在 GitHub 页面的浏览器控制台中，`fetch()` 和 `XMLHttpRequest` 到 `api.github.com` **均不可用**：

```javascript
// ❌ fetch — Failed to fetch（CORS/CSRF 拦截）
fetch('https://api.github.com/repos/user/repo/contents/README.md', {
  method: 'PUT', credentials: 'include', ...
})

// ❌ XHR — 同样失败
const xhr = new XMLHttpRequest();
xhr.open('PUT', 'https://api.github.com/...', true);
xhr.withCredentials = true; // 仍然 Failed to load
```

**替代方案：** 使用 `execCommand` 直接操作编辑器提交（见 §3.8），或通过 `gh` CLI / terminal 操作。

### 3.10 验证表单提交成功

提交后检查 DOM 中的 flash 消息确认结果：

```javascript
(() => {
  const msgs = document.querySelectorAll('[class*="flash"], [class*="notice"], [class*="success"]');
  const result = [];
  for (const m of msgs) {
    if (m.textContent.trim()) result.push(m.textContent.trim().substring(0, 100));
  }
  return JSON.stringify({url: window.location.href, messages: result});
})()
```

---

## 四、典型操作流程

### 4.1 打开网页并提取内容

```
① browser_navigate(url='https://目标网站.com')    # 打开页面，返回快照
② browser_snapshot(full=true)                       # 获取完整内容
③ 根据需要点击、滚动、提取数据
```

### 4.2 点击页面中的链接/标题

```
① browser_navigate(url='https://目标网站.com')     # 打开页面
② 从返回的快照中找到目标元素的 ref ID（如 @e12）
③ browser_click(ref='@e12')                          # 点击
④ browser_snapshot(full=true)                        # 获取新页面内容
```

### 4.3 在输入框中搜索

```
① browser_navigate(url='https://目标网站.com')     # 打开页面
② 从快照中找到输入框的 ref ID（如 @e3）
③ browser_type(ref='@e3', text='搜索关键词')         # 输入
④ browser_press(key='Enter')                         # 提交
⑤ browser_snapshot(full=true)                        # 获取搜索结果
```

### 4.4 多标签页操作

```
① browser_cdp(method='Target.getTargets', params={})  # 列出所有标签
② 记录目标标签的 targetId
③ browser_cdp(method='Page.navigate', params={'url': '...'}, target_id='<tab_id>')
④ browser_cdp(method='Runtime.evaluate', params={'expression': '...'}, target_id='<tab_id>')
```

---

## 五、页面数据提取技巧

通过 `browser_console` 执行 JS 直接提取 DOM 数据，比 snapshot 更灵活、无长度限制。

### 5.1 提取文本

```javascript
document.querySelector('main').innerText.substring(0, 8000)
```

### 5.2 提取表格数据

```javascript
Array.from(document.querySelectorAll('table')).map(t => t.innerText).join('\n---\n')
```

### 5.3 提取链接

```javascript
Array.from(document.querySelectorAll('a')).map(a => a.textContent.trim() + ' → ' + a.href).join('\n')
```

### 5.4 点击特定文本的元素

```javascript
document.querySelectorAll('nav a').forEach(a => {
  if (a.textContent.trim() === '目标文字') a.click();
});
```

### 5.5 提取 h2 模块（标题 + 内容）

```javascript
let sections = [];
document.querySelectorAll('h2').forEach(h2 => {
  let text = '【' + h2.textContent.trim() + '】';
  let el = h2.nextElementSibling;
  let n = 0;
  while(el && !el.matches('h2') && n < 20) {
    let t = el.innerText ? el.innerText.trim() : '';
    if(t && t.length > 5 && t.length < 2000) text += '\n' + t;
    el = el.nextElementSibling; n++;
  }
  sections.push(text);
});
sections.join('\n\n')
```

---

## 六、长页面截断问题与解决方案

### 6.1 问题

`browser_snapshot(full=true)` 有约 8000 字符限制。超过后显示 `[... N more lines truncated]`，丢失下半部分内容。

### 6.2 解决方案：JS 直接提取 DOM

不要用 `browser_snapshot`，改用 `browser_console` 执行 JS 提取文本（见 §五的各种提取模式）。

### 6.3 提取策略

- 优先用 CSS 选择器精准定位目标区域（`querySelector` / `querySelectorAll`）
- 用 `.innerText` 获取渲染后文本
- 用 `.substring(0, N)` 控制长度
- 复杂页面按标题层级分段提取（如 h2 → h3）

---

## 七、文件上传（⚠️ 已知限制）

### 7.1 CDP `DOM.setFileInputFiles` 不可用

当前 CDP 端点为 `http://127.0.0.1:9222`（HTTP），不是 WebSocket URL。`browser_cdp` 的 `DOM.setFileInputFiles` 方法会报错：

```
CDP endpoint is not a WebSocket URL: 'http://127.0.0.1:9222'. Expected ws://... or wss://...
```

**这意味着无法通过 CDP 协议直接设置文件输入框的值。**

### 7.2 替代方案 A：DataTransfer + 文件输入框

当页面已有 `<input type="file">` 元素时，用 JS 创建 File 对象并触发 change 事件：

```javascript
// 从 data URL 创建 File 对象（推荐，不受跨域限制）
(async () => {
  const input = document.querySelector('input[type="file"]');
  if (!input) return 'file input not found';
  
  // 方式 1：从 data URL（base64）创建
  const dataUrl = 'data:image/png;base64,iVBORw0KGgo...';
  const arr = dataUrl.split(',');
  const mime = arr[0].match(/:(.*?);/)[1];
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) u8arr[n] = bstr.charCodeAt(n);
  const file = new File([u8arr], 'filename.png', { type: mime });
  
  const dt = new DataTransfer();
  dt.items.add(file);
  input.files = dt.files;
  input.dispatchEvent(new Event('change', { bubbles: true }));
  return 'file set, size: ' + file.size;
})()
```

### 7.3 替代方案 B：本地 HTTP 服务器（⚠️ 混合内容限制）

**注意：此方案通常不可行。** 当目标页面是 HTTPS 时，浏览器会阻止 `fetch()` 到 `http://localhost`（混合内容策略）。即使本地服务器设置了 CORS 头也无济于事。

```javascript
// ❌ 会失败：HTTPS 页面无法 fetch HTTP localhost
(async () => {
  const resp = await fetch('http://localhost:18888/image.png');
  // → Failed to fetch (mixed content)
})()
```

### 7.4 替代方案 C：手动上传（最终手段）

当自动化方案都不可行时，告知用户手动上传：

> "头像上传需要手动操作：请进入设置页面，点击头像区域上传图片。"

### 7.5 文件上传决策树

```
需要上传文件？
├── 页面有 <input type="file">？
│   ├── 是 → 用 DataTransfer + File 对象（方案 A）
│   │   ├── 有 data URL / base64？→ 直接创建 File
│   │   └── 只有本地文件路径？→ 需要用户手动上传（方案 C）
│   └── 否 → 需要用户手动上传（方案 C）
└── CDP DOM.setFileInputFiles？
    └── 当前不可用（HTTP 端点）→ 回退到方案 A 或 C
```

> 详细代码和替代方案见 `references/file-upload-workarounds.md`

---

## 八、GitHub 个人资料编辑

通过浏览器自动化编辑 GitHub 个人资料的完整流程。

### 8.1 编辑入口

```
browser_navigate(url='https://github.com/settings/profile')
```

先确认登录态：导航到 `github.com` 看到 Dashboard 后，再进入 settings。

### 8.2 表单填写

| 字段 | 操作 |
|------|------|
| Name | `browser_type` |
| Bio | `browser_type`（建议风趣幽默，突出技术背景） |
| Public email | JS setter + change event |
| URL | `browser_type` |
| Social accounts | `browser_type` × 4 |
| Company | `browser_type` |
| Location | `browser_type` |

### 8.3 保存

"Update profile" 按钮在页面底部，用 JS 全局搜索点击：

```javascript
(() => {
  for (const btn of document.querySelectorAll('button')) {
    if (btn.textContent.trim() === 'Update profile') {
      btn.click();
      return 'clicked';
    }
  }
  return 'not found';
})()
```

### 8.4 验证

检查 flash 消息：`"Profile updated successfully — view your profile."`

### 8.5 头像上传

⚠️ 当前不可自动化（CDP HTTP 端点 + HTTPS 混合内容限制）。直接告知用户手动上传。

### 8.6 Profile README

创建与用户名同名的仓库（`username/username`），其中的 `README.md` 自动显示在主页顶部。

> 可复用模板见 `templates/github-profile-readme.md`

### 8.7 Pin 仓库

主页可固定 6 个仓库。进入 `github.com/<username>` → "Customize your pins"。

> 详细代码和完整优化清单见 `references/github-profile-editing.md`

---

## 九、GitHub Web UI 操作参考

当 `gh` CLI 不可用时，可通过浏览器自动化完成大部分 GitHub 操作。

**平台限制与应对：**

| 限制 | 说明 | 应对 |
|------|------|------|
| `<style>` 标签被 CSP 过滤 | README.md 渲染时 `<style>` 块被静默移除 | 使用锚点链接替代 CSS toggle |
| `fetch('api.github.com')` 跨域拦截 | 浏览器内 XHR/fetch 到 GitHub API 被 CORS/CSRF 拦截 | 用 DOM 操作 + CodeMirror execCommand，或 `gh` CLI |
| `gh` CLI 未安装 | 部分机器无 GitHub CLI | 用 `https://github.com/new` Web UI 创建仓库 |

### 9.1 GitHub Web UI 删除整个目录（逐文件删除）

GitHub 网页界面**不支持直接删除目录**。只能逐个删除文件，当目录内所有文件被删除后，空目录自动消失。

**标准流程（N 个文件 = N 次删除 + N 次 commit）：**

```
① browser_navigate(url='https://github.com/user/repo/tree/main/path/to/dir')
② browser_snapshot()  → 找到目录下所有文件
③ 对每个文件循环执行：
   a) browser_click(ref='@e文件链接')    → 进入文件视图
   b) browser_snapshot()               → 获取新 ref
   c) browser_click(ref='@eMore file actions')  → 展开操作菜单
   d) browser_snapshot()               → ref 变了，必须重新获取
   e) browser_click(ref='@eDelete file') → 确认删除视图
   f) browser_snapshot()
   g) browser_click(ref='@eCommit changes...')  → 打开 commit 对话框
   h) browser_snapshot()
   i) browser_click(ref='@eCommit changes')     → 直接 commit（默认 commit message 即可）
   j) browser_snapshot() → 确认 "File successfully deleted."
④ browser_navigate(url='https://github.com/user/repo/tree/main/path/to/dir') → 验证 404
```

**⚠️ Pitfalls：**
- **每次点击后必须重新 snapshot**：展开菜单和 commit 对话框都会改变 DOM 和 ref ID，用旧 ref 点击会命中错误元素
- **commit 对话框中 radio 默认选中 "Commit directly to the main branch"**：无需切换，直接点 "Commit changes"
- **删除最后一个文件后**，页面自动跳转到父目录，空目录不再出现在文件树中
- **大量文件时考虑效率**：如果目录下文件很多（>5个），考虑用 `gh` CLI 或 GitHub API 批量删除

> 详细参考：`references/github-csp-constraints.md`、`references/github-bilingual-readme.md`

### 9.2 GitHub Sudo Mode 验证流程（⚠️ 关键陷阱）

GitHub 对敏感操作（添加 SSH key、修改邮箱、创建 PAT 等）会触发 **sudo mode**，要求通过邮件验证码确认身份。

**⚠️ 核心陷阱：验证码是单次使用 + 15 分钟有效，且离开页面会丢失表单状态！**

#### ❌ 常见失败模式

```
① 填写表单（Title + Key）
② 提交 → 触发 sudo mode → 需要验证码
③ browser_navigate 去 Gmail 取验证码   ← 💀 表单状态丢失！
④ 回到 GitHub → 页面重新加载 → 所有输入清空
⑤ 需要重新填写 + 重新获取新验证码 → 重复循环
```

#### ✅ 正确策略

**策略 A：用户手动添加 SSH key（推荐）**

> "请你在浏览器中打开 https://github.com/settings/ssh/new ，粘贴以下公钥添加。"

用户在自己的浏览器中操作，不存在页面切换丢失状态的问题。

**策略 B：用 GitHub API + PAT（如果有 token）**

```bash
curl -X POST https://api.github.com/user/keys \
  -H "Authorization: token $GITHUB_TOKEN" \
  -d '{"title":"key-name","key":"ssh-ed25519 AAAA..."}'
```

**策略 C：两步分离 — 先提交表单，不离开页面，通过非浏览器渠道获取验证码**

1. 提交表单 → 出现验证码输入框
2. **不要 navigate 离开** GitHub 页面
3. 用 `terminal` 检查邮件，或让用户手动查看邮箱告诉你验证码
4. 在当前页面输入验证码并提交

**决策树：**

```
需要执行 GitHub 敏感操作？
├── 用户可手动操作？→ 让用户自己做（策略 A），最快最可靠
├── 有 GitHub PAT？→ 用 API 绕过 sudo mode（策略 B）
└── 都没有？→ 尝试策略 C，但大概率失败 → 退回策略 A
```

---

## 十、注意事项

| 问题 | 说明 |
|------|------|
| SPA 渲染延迟 | 点击后等待后再提取，否则数据可能为空 |
| 登录态 | 已登录的网站保持登录态（cookies 保存在 profile 中） |
| 页面过长 | 使用 `browser_scroll(direction='down')` 分段查看，或用 JS 提取 |
| 截图辅助 | 当快照不够直观时，用 `browser_vision` 看实际页面 |
| 不要关浏览器 | 操作完成后不要关闭标签页或浏览器，保持运行 |
| 失败处理 | 提取失败就重试一次，仍失败标记「暂无数据」，不反复折腾 |
| 文件上传 | CDP 端点限制，优先让用户手动上传 |
| GitHub 编辑 | 见 `references/github-profile-editing.md` |

## Pitfalls 速查

| # | 问题 | 解决方案 |
|---|------|---------|
| 1 | SPA 导航用 browser_click 静默失败 | 用 JS click（IIFE 包裹） |
| 2 | browser_type 在 CodeMirror 6 上是追加行为 | 用 execCommand selectAll + insertText |
| 3 | browser_console let/const 重复声明报错 | 用 IIFE 包裹或 var |
| 4 | emoji 在 browser_console 中写入失败 | 用 surrogate pairs 代理对编码 |
| 5 | CDP DOM.setFileInputFiles 不可用（HTTP 端点） | DataTransfer + File 对象，或手动上传 |
| 6 | GitHub sudo mode 表单状态丢失 | 让用户手动操作，或用 API |
| 7 | GitHub fetch/XHR 跨域拦截 | DOM 操作 + CodeMirror，或 gh CLI |
| 8 | 跨一级板块导航渲染异常 | 先 navigate 回首页，再 JS click |
| 9 | CodeMirror 编辑器内容损坏 | 删除重建文件，不要继续编辑 |
| 10 | Chrome 端口冲突 / profile 锁冲突 | 确保独立 user-data-dir，不重复启动 |
| 11 | Vue/React 输入框不响应 browser_type | JS 原生 setter + dispatch input event |
| 12 | 长页面 snapshot 截断 | 用 browser_console JS 提取 DOM |
| 13 | 剪贴板粘贴法静默失败 | 改用 execCommand + 代理对 |
