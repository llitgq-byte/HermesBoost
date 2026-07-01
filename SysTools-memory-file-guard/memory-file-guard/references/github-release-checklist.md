# GitHub 公开发布 Checklist

> 适用于任何 Hermes Skill 从内部使用 → 公开 GitHub 的场景。
> 来源：2026-07-01 对 `tools-memory-user-file-in` 发布流程的实际操作总结。

---

## 1️⃣ 安全检查

审查所有文件（特别是 `bundled/plugins/`）：

- [ ] 无硬编码 API key、token、secret、密码
- [ ] 无个人数据（用户名、profile、UID、手机号、邮箱）
- [ ] 无机器指纹（主机名、MAC、序列号）
- [ ] 路径为通用写法（`~/.hermes/...`，不含 `/Users/xxx`）
- [ ] 临时目录通用化（`/tmp/...` 或通过 `tempfile.gettempdir()` 获取）

## 2️⃣ 准备发布包

**方式 A（推荐）：在已 clone 的仓库内直接编辑**
```bash
cd ~/Documents/public_github/<repo>/auxiliary/<sub-skill>/
# 直接编辑文件，完成后 git push
```

**方式 B：独立副本（未 clone 时）**
```bash
cp -r ~/.hermes/skills/Always/<your-skill> ~/Documents/public_github/<your-skill>
```

在副本上工作 ← 从不修改原位 skill。

## 3️⃣ README 五维度

每份公开 README **必须覆盖以下 5 维度**：

| # | 维度 | 该维度必须回答 |
|---|------|---------------|
| 1 | **项目描述** | 这个工具解决什么问题？保护/增强什么能力？核心理念是什么？ |
| 2 | **安装方法** | 复制哪些文件到哪个目录？config.yaml 改动什么？需要什么重启？ |
| 3 | **使用流程** | 触发条件是什么？被触发后走哪些步骤？用户需要做什么？ |
| 4 | **跟 Agent 的交互** | 用户需不需要学新的命令/句式？Agent 如何处理拦截/事件？ |
| 5 | **配置方法** | 哪些是 mandatory（必须配置），哪些是 optional？硬件/OS 依赖？ |

## 4️⃣ 双语策略

**双文件方案**推荐（非单文件 tab 切换）：
- `README.md` — 英文，面向国际
- `README.zh.md` — 中文，面向中文用户
- 两文件顶部交叉锚链表示切换

**为什么不用单文件混排**：单文件要么篇幅臃肿，要么一方被另一方稀释。双文件让每份语言在各自文件中完整、沉浸。

### 高效批量创建：delegate_task 并行

当需要同时为多个目录创建双语 README 时，用 `delegate_task` 并行处理（最多 3 个子任务并发）：

```python
delegate_task(tasks=[
  {"goal": "写 auxiliary/README.md（英文）", "toolsets": ["file"]},
  {"goal": "写 finance/README.md（英文）", "toolsets": ["file"]},
  {"goal": "写 life/README.md（英文）", "toolsets": ["file"]},
])
# 完成后再批量创建中文版
delegate_task(tasks=[
  {"goal": "读取 auxiliary/README.md，翻译为 README.zh.md", "toolsets": ["file"]},
  {"goal": "读取 finance/README.md，翻译为 README.zh.md", "toolsets": ["file"]},
  {"goal": "读取 life/README.md，翻译为 README.zh.md", "toolsets": ["file"]},
])
```

**要点**：中文版必须先读取英文版再翻译（子 Agent 无上下文），context 参数需提供文件路径和格式要求。

## 5️⃣ 分段结构模板

```
# 工具名

[🇨🇳 中文](README.zh.md) · English    ← 顶部语言切换

---

一句话说清是什么

## 核心特性（5 条以内 bullet）

## 1. 项目描述
## 2. 安装方法
## 3. 使用流程
## 4. 使用方式
## 5. 配置说明

## 许可证（MIT 推荐）
```

## 6️⃣ 推送到 GitHub

### 推荐方式：本地 Git + SSH key（无需 gh CLI）

**永远优先用本地仓库操作**，浏览器 UI 是最后手段。

```bash
# 1. 生成 SSH key（如果没有）
mkdir -p ~/.ssh
ssh-keygen -t ed25519 -C "<email>" -f ~/.ssh/id_ed25519 -N ""
# 将 ~/.ssh/id_ed25519.pub 添加到 GitHub → Settings → SSH and GPG keys

# 2. Clone 到本地工作目录
mkdir -p ~/Documents/public_github
cd ~/Documents/public_github
git clone git@github.com:<owner>/<repo>.git

# 3. 在本地编辑文件（用 write_file / patch / 终端）

# 4. 提交并推送
cd ~/Documents/public_github/<repo>
git add -A
git commit -m "描述"
git push
```

### 备选方式：本地 Git + gh CLI

如果已安装 gh CLI 且已认证：
```bash
brew install gh && gh auth login
git clone https://github.com/<owner>/<repo>.git ~/Documents/public_github/<repo>
# 编辑后 git push
```

### ⚠️ Pitfall A：`~` 在 Hermes 终端中会被双重展开

Hermes 子 Agent 的 shell 环境中，`~` 先被 Hermes 展开为 `$HOME`（即 `~/.hermes/profiles/<name>/home/`），再被 shell 展开。结果路径变成嵌套重复：

```
实际执行：cp ~/.hermes/profiles/code/home/.ssh/id_ed25519 ~/.ssh/id_ed25519
错误路径：/path/to/hermes/home/.ssh/id_ed25519
```

**修复：** 在 Hermes 终端中操作文件时，**永远用绝对路径**，不要用 `~`：
```bash
# ❌ 错误 — 会双重展开
cp ~/.ssh/id_ed25519 /Users/<realuser>/.ssh/

# ✅ 正确 — 绝对路径
cp /path/to/hermes/home/.ssh/id_ed25519 /Users/<realuser>/.ssh/
```

### ⚠️ Pitfall B：$HOME 与系统 $HOME 不一致

在 Hermes 子 Agent（profile）中，`$HOME` 指向 `~/.hermes/profiles/<name>/home/`，而 SSH 客户端和 git 默认按 `$HOME/.ssh/` 寻找密钥和 known_hosts。

**症状：** `ssh -T git@github.com` 报 `Permission denied (publickey)`，即使 key 已正确生成并添加到 GitHub。

**修复：** 将 key 复制到系统真实 home 目录（必须用绝对路径，见 Pitfall A）：
```bash
mkdir -p /Users/<realuser>/.ssh
cp /path/to/hermes/home/.ssh/id_ed25519 /Users/<realuser>/.ssh/
cp /path/to/hermes/home/.ssh/id_ed25519.pub /Users/<realuser>/.ssh/
chmod 700 /Users/<realuser>/.ssh
chmod 600 /Users/<realuser>/.ssh/id_ed25519

# 或者在仓库内配置 git 使用指定 key 文件（绝对路径）
git config core.sshCommand "ssh -i /Users/<realuser>/.ssh/id_ed25519 -o StrictHostKeyChecking=no"
```

在仓库 `.gitconfig` 中设置 `core.sshCommand` 是最稳妥的方案，因为它不依赖 `$HOME` 路径解析。

### ⚠️ Pitfall C：SSH 端口 22 被网络阻断

某些网络环境（企业防火墙、运营商封锁）会阻断到 `github.com:22` 的连接，表现为 `Connection closed by <ip> port 22`。

**验证：**
```bash
ssh -T git@github.com          # → Connection closed? → 端口 22 被阻
ssh -p 443 -T ssh.github.com   # → Permission denied? → 端口 443 通，但密钥问题
ssh -p 443 -T ssh.github.com   # → Hi <user>!? → 完全正常
```

**修复：** 在 `~/.ssh/config`（系统级 `/Users/<realuser>/.ssh/config`）中配置端口 443：
```
Host github.com
  HostName ssh.github.com
  Port 443
  User git
  IdentityFile ~/.ssh/id_ed25519
  StrictHostKeyChecking accept-new
```

配置后 `git push origin main` 等命令会自动走 443 端口，无需每次指定 `-p`。

### ⚠️ 浏览器 UI 的已知问题（仅在无法使用 git 时作为 fallback）

- GitHub 网页编辑器使用 **CodeMirror**，`browser_console` 的 `textarea` 注入无效
- `browser_type` 对大段 markdown 内容不可靠（超长文本截断、格式丢失）
- 文件路径含 `<` 符号会导致 git tree 嵌套污染（难以修复）
- 删除目录必须逐个文件操作，非常低效

如果必须使用浏览器 UI：
1. 打开 `https://github.com/<owner>/<repo>/new/main`
2. **文件名栏输入路径**：例如 `auxiliary/memory-file-guard/README.md`（支持自动创建子目录）
3. Commit：标题由 Copilot 生成，**手动检查有无多余 `<` 字符**
4. 发布后用 API 或刷新验证页面正常渲染

## 7️⃣ 发布后

- [ ] 页面正常渲染，无多余 HTML 残留
- [ ] 两语言文件互相可跳转
- [ ] 安装命令可直接复制运行
- [ ] 截图/演示展示了真实场景（可选但推荐）

---

## 8️⃣ HermesBoost 特殊规则

此流程用在 HermesBoost（https://github.com/llitgq-byte/HermesBoost）项目中时：

- 文件放在 `auxiliary/<sub-skill>/` 目录下
- 主 README 中加一条指向该子项目的链接
- 每个子 Skill 保持独立 README（双语），再被主项目汇总
- 主 README 只体现分类和三言两语定位，不展开细节