# GitHub 浏览器编辑实操 Pitfalls

基于 HermesBoost 项目创建过程中的真实踩坑记录（2026-07-01）。

---

## Pitfall #1：`browser_type` 不会覆盖，只会追加

**场景：** 在 GitHub 文件编辑器中用 `browser_type` 输入内容。

**现象：** 第一次 `browser_type` 输入成功；第二次继续在同一编辑器用 `browser_type` 输入「修正版」内容后，文件内容变成原始 + 修正版叠加 = 3 倍重复。

**根因：** GitHub 的 CodeMirror 6 编辑器没有传统的 `<textarea>`，`browser_type` 的 CDP `Input.insertText` 直接在光标位置**追加**文本，而不是替换。

**解决方案：** 永远不要用 `browser_type` 向 GitHub 编辑器写入。改用 `browser_console` 的 `execCommand('selectAll') + execCommand('insertText', ...)` 一次性全选替换。

---

## Pitfall #2：切换新文件时旧的编辑器 Session 残留

**场景：** 用 `browser_navigate` 进入 `/new/main` 页面创建文件 A，输入内容后没有点 Commit；接着用另一个 `browser_navigate` 进入 `/new/main` 页面创建文件 B。

**现象：** 文件 B 的编辑器里显示的是文件 A 的内容。

**根因：** GitHub 是 SPA，`browser_navigate` 到相同 URL (`/new/main`) 时不会销毁旧 DOM，只有文件名字段会重置。

**解决方案：** 每次 `browser_navigate` 到 `/new/main` 后，先用 JS 检查 `.cm-content` 是否已有内容 → 若有，用 `execCommand('selectAll') + execCommand('delete')` 清空后再开始输入。

---

## Pitfall #3：Copilot 自动生成 Commit 消息可能不准确

**场景：** 点「Commit changes」后 Commit Dialog 弹出，GitHub Copilot 自动生成了 Commit 消息。

**现象：** Copilot 生成的消息可能是上次操作的描述（如「Correct entry point and update plugin.yaml format」），与当前操作的实际内容不符。

**解决方案：** 每次 Commit 前**检查并修改** Commit 消息，使其准确反映本次变更。

---

## Pitfall #4：CodeMirror 6 无法从控制台拿到 View 实例

**场景：** 想通过 JavaScript 直接操作 CodeMirror 的 View/State 来精确替换内容。

**现象：** `window.monaco` 不存在；`.cm-view` 属性为 undefined；无法拿到 EditorView 实例。

**解决方案：** 不要用 CodeMirror API，直接用 `document.execCommand` 模拟 keyboard command。

---

## Pitfall #5：browser_console IIFE 中的变量重复声明

**场景：** 在同一浏览器会话中多次用 `browser_console` 访问同一页，都声明了 `const cmContent = ...`。

**现象：** 第二次及之后报 `SyntaxError: Identifier 'cmContent' has already been declared`。

**解决方案：**
- 始终用 IIFE 包裹：`(() => { const x = ...; return x; })()`
- 或用 `var`（允许重复声明）

---

## 验证写入成功

每次写入后立即验证内容长度和行数：

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

**判断标准：**
- `lines` 与预期的行数一致 → ✅ 写入成功
- `lines` 是 3 倍预期（或 2 倍） → ❌ 遭遇 Pitfall #1（browser_type 追加）
- `commitDisabled: true` → ❌ 编辑器检测到空内容或焦点异常

---

## Pitfall #6：编辑失败后继续编辑只会让内容更乱 → 删除重建（2026-07-01）

**场景：** CodeMirror 6 编辑器内容已损坏（重复叠加、描述字段丢失、Unicode 编码失败后继续 `browser_type`/`execCommand` 修复）。

**现象：** `browser_press(Ctrl+a)` + `browser_type` 每次调用都是追加；`execCommand` 全选替换后实际内容要么依旧损坏、要么仍不符合预期。修复尝试越多，文件越乱。

**根因：** CodeMirror 6 在页面未完全刷新的情况下保留编辑状态。SPA 从 `/blob/main/...` 跳转到 `/edit/main/...` 时，浏览器端 CodeMirror 实例可能残留。此外，`browser_type` 的 CDP `Input.insertText` 始终在当前光标位置追加——即使 `browser_press(Ctrl+a)` "选中"了内容，插入时选区也被新文本覆盖，而不是先删除再写入。

**正确解决方案：用「删除 + 新建」绕过问题**

```
Step 1: 验证内容已损坏
  → browser_console: cmContent.querySelectorAll('.cm-line').length >> 预期行数 = 已损坏

Step 2: 回到文件视图
  → browser_navigate 到 /tree/main/.../目录/ 页面
  → 或直接在 .github.com 页面用 JS: 点 "More file actions" 下拉中的 "Delete file"

Step 3: 确认删除
  → 出现 Delete Dialog → 点 "Commit changes" 确认

Step 4: 新建文件
  → 系统自动跳转到 "Create new file" 页面（因为 Delete + Create 路径一致）
  → 或手动 /new/main/.../ → 输入文件名 → 输入干净内容 → Commit
```

**决策流程：**

```
编辑器内容损坏？
├── 是 → 停止编辑 → 删除文件 → 新建同路径文件 → 输入干净内容 → Commit
└── 否（首次编辑、编辑器空白） → execCommand 全选 + 单次 insertText
```

**实测时间线（2026-07-01）：**

| 步骤 | 动作 | 结果 |
|------|------|------|
| 1 | `browser_type` | 3 倍重复内容 |
| 2 | `browser_press(Ctrl+a)` + `browser_type` | 6 倍追加 |
| 3 | `execCommand('selectAll')` + `execCommand('insertText', ...)` | 内容更乱 |
| 4 | Delete file → Create new file | ✅ 干净内容写入 |

**教训：** 当编辑器内容已损坏时，停止所有编辑尝试。CodeMirror 6 无法从控制台获得内部 View 实例来强制清理状态。删除+新建是唯一可靠的回退方案。

---

## Pitfall #7：浏览器创建文件时变成 Git Tree/Submodule 而非 Blob（2026-07-01）

**场景：** 通过 GitHub Web UI（`/new/main`）在已存在的目录下创建新文件（如 `auxiliary/memory-file-guard/README.md`）。

**现象：**
- 提交后文件看似存在，但 `raw.githubusercontent.com` 返回 **404**
- GitHub Tree API 显示文件类型为 `tree`（应为 `blob`），`size: 0`
- 路径显示为异常的嵌套形式，如 `auxiliary/memory-file-guard/README.md</auxiliary/memory-file-guard/README.md`
- 同一目录下其他文件（如 `SKILL.md`）不受影响，只有部分文件中招

**根因推测：** GitHub Web UI 在 SPA 路由下偶尔会把 create-file 请求误解为 submodule/tree-reference 创建（可能与浏览器残留的 FormData 拼接方式或 SPA 内部状态有关）。具体触发条件未完全明确，但曾在「已经在同一浏览器会话中创建过同名文件再删除」后复现。

**验证方法（快速检查三件套）：**

```bash
# 1. raw URL 返回 404？= 文件不存在或损坏
curl -s "https://raw.githubusercontent.com/OWNER/REPO/main/路径/文件.md" | head -3

# 2. Tree API 检查类型
curl -s "https://api.github.com/repos/OWNER/REPO/git/trees/main?recursive=1" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for item in data.get('tree', []):
    if '目标路径' in item['path']:
        print(f'{item[\"type\"]:6s} {item.get(\"size\", \"dir\"):>6}  {item[\"path\"]}')
"

# 3. diff 本地文件 vs 远程（如果有本地副本）
curl -s "https://raw.githubusercontent.com/OWNER/REPO/main/路径/文件.md" > /tmp/remote.md
diff 本地文件 /tmp/remote.md  # 无输出 = 一致
```

预期：所有文件应为 `blob` 类型、`size > 0`、`path` 不含 `<` 字符。如果出现 `type: tree`、`path` 含 `<`、或 raw URL 返回 404，即已损坏。

**解决方案：**

```
Step 1: 确认损坏
  → curl raw URL → 404 = 损坏
  → curl Tree API → type: tree = 损坏
  → Tree API 中 path 含 < 字符 = 确认损坏

Step 2: 删除损坏的 tree entry（⚠️ 关键细节）
  → browser_navigate 到父目录页面（如 auxiliary/memory-file-guard）
  → 损坏条目在页面中显示为「Directory」，名称含 <（如 README.md</auxiliary/memory-file-guard）
  → ⚠️ 不能从父目录直接删除！没有删除目录的按钮
  → ✅ 必须点击进入损坏目录 → 找到内部的文件（如 README.md）
  → 点文件名 → 进入文件视图 → "More file actions" (…) → "Delete file" → Commit
  → 文件删除后，空的损坏目录自动消失（GitHub 不会保留空目录）

  注意：左侧文件树（File Tree Navigation）可能缓存旧的条目，刷新页面即可更新

  如有多个损坏条目（如 README.md< 和 README.zh.md<），重复以上流程逐个删除

Step 3: 重建文件
  → 方案 A：通过 "Add file" → "Create new file" 创建同名文件 → execCommand 写入 → Commit
  → 方案 B：通过 terminal 用 curl PUT GitHub API 直接创建（需要 token）
  → 方案 C：本地 git clone → 修复 → push（如果 push 可用）

Step 4: 再次验证 Tree API，确认 type: blob, size > 0 且 raw URL 返回内容
```

**特别提醒：**
- 不要把 `404` 误判为「文件还没创建成功」！如果 404 + Tree API 能看到 entry → 那是 tree 类型损坏，不是「未提交」
- 损坏的 tree entry 不会自动修复，永远停留在 `type: tree`，必须手动删除
- `SKILL.md`、`__init__.py` 等程序源代码文件不容易中招；`README.md`/`README.zh.md` 等描述性文件似乎是更容易触发（可能与文件内容格式或首次创建时的 Form 编码有关，但样本不够多，无法确定）
- **损坏条目显示为 Directory 而非 File** — GitHub Web UI 无法从父目录直接删除子目录，必须点击进入目录内部删除文件
- **删除后空目录自动消失** — 不需要额外的清理步骤

---

## 已验证可用的 GitHub 浏览器编辑方案（2026-07-01 更新）

| 操作 | 方案 | 状态 |
|------|------|------|
| 写入小文件 (< 50 行) | `execCommand('selectAll') + execCommand('insertText', ...)` | ✅ 可靠 |
| 写入大文件 (> 100 行) | 同上，一次写入完整内容 | ✅ 可靠（单步、无长度限制） |
| 修正已提交文件 | 导航到 `/edit/main/路径`，同上流程全选替换 | ✅ 已验证（仅限首次尝试） |
| 创建新文件 | `/new/main` + `execCommand` 写入 + Commit | ✅ 已验证 |
| 验证内容 | `cm-line` 数量 + Commit 按钮状态 | ✅ 可靠 |
| **创建后验证类型** | **Tree API `type: blob`** | ✅ **新增检查项** |
| **内容已损坏** | **Delete + Create new file** | ✅ **终极回退**（2026-07-01 验证） |
| **损坏 tree entry 删除** | **进入损坏目录 → 删除内部文件 → 空目录自动消失** | ✅ **已验证**（2026-07-01） |
| **删除后验证** | **Tree API `type: blob` + raw URL 200** | ✅ **标准验证流程** |
| **批量损坏清理** | **逐个进入损坏目录删除文件，最后统一创建正确文件** | ✅ **已验证**（2026-07-01） |
