# GitHub 个人资料编辑（浏览器自动化）

通过 `github.com/settings/profile` 页面编辑 GitHub 个人资料的完整流程。

## 前置条件

- 用户已在 Hermes Chrome 中登录 GitHub
- 先导航到 `github.com` 确认登录态（看到 Dashboard），再进入 settings

## 表单字段与操作

### 1. 基本信息

| 字段 | 元素类型 | 操作方式 |
|------|---------|---------|
| Name | textbox | `browser_type(ref, text)` |
| Public email | `<select>` | JS setter + change event |
| Bio | textbox (multiline) | `browser_type(ref, text)` |
| Pronouns | `<select>` | JS setter + change event |
| URL | textbox | `browser_type(ref, text)` |
| Social accounts | textbox × 4 | `browser_type(ref, text)` |
| Company | textbox | `browser_type(ref, text)` |
| Location | textbox | `browser_type(ref, text)` |

### 2. 保存

"Update profile" 按钮在页面底部，`browser_snapshot` 中可能不可见。用 JS 全局搜索：

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

### 3. 验证成功

```javascript
(() => {
  const msgs = document.querySelectorAll('[class*="flash"], [class*="success"]');
  return Array.from(msgs).map(m => m.textContent.trim().substring(0, 100));
})()
```

成功标志：`"Profile updated successfully — view your profile."`

## 头像上传

⚠️ **当前不可自动化**。原因：
1. `browser_cdp(DOM.setFileInputFiles)` — CDP 端点为 HTTP，非 WebSocket
2. 本地 HTTP 服务器 + fetch — HTTPS 页面阻止混合内容
3. DataTransfer + File — 需要 data URL，但大图片 base64 传递困难

**处理方式：** 直接告知用户手动上传，不要反复尝试自动化。

## Profile README

创建与用户名同名的仓库（如 `llitgq-byte/llitgq-byte`），其中的 `README.md` 会自动显示在 GitHub 主页顶部。GitHub 会标注："is a special repository: its README.md will appear on your profile!"

### 创建步骤

1. 导航到 `github.com/new`
2. 仓库名 = 用户名（如 `llitgq-byte`），填入描述
3. **不要勾选** "Add a README file"（checkbox 点击后 `browser_click` 提交按钮经常返回 "You can't perform that action at this time"）
4. Public 可见性
5. 用 JS 点击 "Create repository"：
   ```javascript
   const btn = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Create repository');
   if (btn) { btn.click(); 'clicked'; } else { 'not found'; }
   ```
6. 创建后进入 `github.com/<username>/<username>/new/main`
7. 设文件名 + 用 CodeMirror 注入写入 README.md 内容（见 SKILL.md §3.8）
8. 点击 "Commit changes..."，确认提交

### ⚠️ GitHub API 浏览器内调用不可用

不要尝试在浏览器控制台通过 `fetch()`/XHR 调用 `api.github.com`（CORS/CSRF 拦截）。只能用网页表单操作或 `gh` CLI。

### README 内容建议

```
👋 欢迎语 + 关于我
🛠️ 技术栈徽章（shields.io）
📊 GitHub 统计卡片（github-readme-stats.vercel.app）
🔥 精选项目展示
📫 联系方式
⚡ 有趣的冷知识/名言
```

> **Emoji 处理：** `execCommand('insertText')` 可以写入 emoji，但必须用 JSON 代理对（`\ud83d\udc4b`），不能用 `\u{XXXX}` 语法（会被写入为字面文本）。详见 SKILL.md §3.8 的代理对照表。如果内容含大量 emoji，推荐用剪贴板粘贴法。

## Pin 仓库

GitHub 主页可固定展示 6 个仓库。

### 设置方式

1. 进入 `github.com/<username>`
2. 点击 "Customize your pins"
3. 勾选最多 6 个仓库
4. Save pins

### 前提

需要先有仓库才能 Pin。

## 完整优化清单

- [ ] 上传头像（手动）
- [ ] 填写 Name
- [ ] 填写 Bio（建议风趣幽默，突出技术背景和当前兴趣）
- [ ] 设置 Public email
- [ ] 填写 Location（FDE 求职可考虑不填，避免地域限制）
- [ ] 添加 Social accounts（最多 4 个）
- [ ] 创建 Profile README 仓库
- [ ] 创建工具仓库并 Pin

## 实际案例（2026-06-30）

**用户：** llitgq-byte（Shan Ding）
**完成：**
- 名称设为 "Shan Ding"
- Bio（英文版，FDE 求职导向，幽默风格）
- 3 个社交链接（Bilibili / 小红书 / 抖音）
- 头像（用户手动上传）
- Profile README 仓库创建 + README.md 写入（CodeMirror 注入方式）

**踩坑记录：**
- `browser_click` 在 `/new` 页面提交时返回 "You can't perform that action at this time"，改用 JS `.click()` 成功
- GitHub 编辑器是 CodeMirror 6（不是 Monaco），`execCommand('selectAll')` + `execCommand('insertText')` 是唯一可靠的写入方式
- emoji 需用 JSON 代理对（`\ud83d\udc4b`），`\u{XXXX}` 会变成字面文本；或用剪贴板粘贴法绕过
- 浏览器内 fetch/XHR 到 `api.github.com` 被 CORS 拦截
