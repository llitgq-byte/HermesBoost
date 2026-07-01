---
name: tools-memory-user-file-in
version: "1.0.0"
description: Memory & User 文件写入保护。Plugin 硬拦截 + Skill 工作流，写入前必须用户确认，写入后自动上锁并推送内容对比。自包含设计，跨 Agent/跨系统可移植。
triggers:
  - memory 写入被拦截
  - memory-file-guard block
  - 写入 memory
  - 写入 user
  - memory file guard
related_skills: []
---

# tools-memory-user-file-in：Memory & User 文件写入保护

## 概述

保护 Hermes 的 `MEMORY.md` 和 `USER.md` 两个持久记忆文件。当 Agent 尝试通过 `memory` 工具写入这两个文件时，Plugin 自动拦截，要求用户确认后才能继续。

**设计原则：**
- **自包含** — Plugin 源码打包在 `bundled/plugins/` 内，Skill 复制到任何 Agent 即可使用
- **跨平台** — Plugin 纯 Python 标准库，macOS/Linux 通用
- **硬拦截 + 软引导** — Plugin 提供硬拦截（无法绕过），Skill 文档引导 Agent 完成确认流程

---

## 架构

```
Agent 想写 memory
    ↓ 调用 memory 工具
Plugin 拦截（pre_tool_call）
    ↓ 无标记文件 → block，返回指引
Agent 收到 block 提示
    ↓ 加载本 Skill，按工作流执行
    ↓ 1. 读取当前文件内容
    ↓ 2. clarify() 询问用户
    ↓ 3. 用户确认
    ↓ 4. 解锁文件 + 创建标记文件
    ↓ 5. 重新调用 memory 工具
Plugin 检测标记文件 → allow（放行）→ 删除标记
    ↓ 写入成功
    ↓ 6. 重新上锁文件
    ↓ 7. 输出完整内容 + 新旧对比
```

**两层保护：**
1. **Plugin 硬拦截** — 没有"已确认"标记文件，memory 工具调用直接被拒绝
2. **文件锁**（可选）— 用户可额外对文件设置 `uchg`/`chattr +i` 锁，双重保险

---

## 第一部分：部署

### 1.1 确定目标

| 场景 | Plugin 安装路径 | config.yaml 路径 |
|------|----------------|-----------------|
| default profile | `~/.hermes/plugins/memory-file-guard/` | `~/.hermes/config.yaml` |
| 子 Agent（profile） | `~/.hermes/profiles/<name>/plugins/memory-file-guard/` | `~/.hermes/profiles/<name>/config.yaml` |

**Plugin 源码在：** `<本 skill 目录>/bundled/plugins/memory-file-guard/`

### 1.2 复制 Plugin

```bash
# 确定 HERMES_HOME
HERMES_HOME=~/.hermes   # default profile
# HERMES_HOME=~/.hermes/profiles/<name>  # 子 Agent

# 复制 plugin
cp -r <本skill>/bundled/plugins/memory-file-guard $HERMES_HOME/plugins/memory-file-guard
```

### 1.3 启用 Plugin

在目标 `config.yaml` 中添加：

```yaml
plugins:
  enabled:
    - memory-file-guard   # ← 添加此行
```

### 1.4 重启 Gateway

```bash
hermes gateway restart
# 子 Agent: hermes gateway restart --profile <name>
```

### 1.5 验证

```bash
grep "memory-file-guard.*registered" <logs目录>/agent.log | tail -3
```

应看到：
```
plugins.memory-file-guard: memory-file-guard plugin registered (pre_tool_call)
```

---

## 第二部分：Agent 工作流（被拦截后的操作指南）

当 Agent 的 `memory` 工具调用被 Plugin 拦截（收到 block 提示）时，**必须按以下步骤执行**：

### 步骤 1：读取当前文件内容

确定文件路径：

```bash
# HERMES_HOME 即当前 Agent 的根目录
# default: ~/.hermes
# 子 Agent: ~/.hermes/profiles/<name>

MEMORY_FILE=$HERMES_HOME/memories/MEMORY.md
USER_FILE=$HERMES_HOME/memories/USER.md
```

用 `read_file` 或 `terminal(cat)` 读取目标文件的当前内容。

### 步骤 2：询问用户确认

使用 `clarify()` 向用户展示：

- **动作**：add / replace / remove
- **目标**：memory 或 user
- **当前内容**：文件现有内容
- **变更内容**：即将写入的内容

示例：

```
即将执行以下 memory 写入操作：

**动作：** replace（替换）
**目标：** memory（MEMORY.md）
**旧内容：** xxx
**新内容：** yyy

是否允许写入？
```

### 步骤 3：处理用户回复

- 用户选"可以" / 回复"1" / 回复"可以" / 回复"确认" → **继续**
- 用户选"取消" / 回复"0" / 回复"不" / 回复"取消" → **终止，不执行任何写入操作**

### 步骤 4：解锁文件 + 创建标记文件

**解锁命令（二选一，按平台）：**

```bash
# macOS
chflags nouchg <文件路径>
xattr -cr <文件路径>

# Linux
chattr -i <文件路径>
```

**创建标记文件：**

```bash
touch /tmp/hermes-memory-guard-approved
```

⚠️ 标记文件有 **120 秒 TTL**，超时后 Plugin 会忽略它。

### 步骤 5：重新调用 memory 工具

使用与被拦截时完全相同的参数，重新调用 `memory` 工具。Plugin 检测到标记文件后会放行。

### 步骤 6：重新上锁文件

写入成功后，立即重新上锁：

```bash
# macOS
chflags uchg <文件路径>

# Linux
chattr +i <文件路径>
```

### 步骤 7：输出内容对比

读取并推送完整的文件内容，同时展示新旧对比：

```
✅ memory 文件写入完成，已重新上锁。

当前 MEMORY.md 全部内容：
---
（完整内容）

变更对比：
| 项目 | 内容 |
|------|------|
| 旧内容 | xxx |
| 新内容 | yyy |
```

---

## 第三部分：文件路径速查

| 文件 | 环境变量方式 | default 路径 |
|------|------------|-------------|
| MEMORY.md | `$HERMES_HOME/memories/MEMORY.md` | `~/.hermes/memories/MEMORY.md` |
| USER.md | `$HERMES_HOME/memories/USER.md` | `~/.hermes/memories/USER.md` |

**在 Agent 中动态获取：**

```bash
echo $HERMES_HOME
# 输出即为当前 Agent 的根目录
```

---

## 第四部分：锁机制说明

### macOS 锁

```bash
# 上锁
chflags uchg <文件>        # 系统级不可变标志
xattr -w com.apple.metadata:kMDLabel_o5suazj6iuatk44mgrboz5aeum "" <文件>  # 扩展属性

# 解锁
chflags nouchg <文件>
xattr -cr <文件>
```

验证状态：`ls -laO <文件>` — 看到 `uchg` 表示已锁定，看到 `@` 表示有扩展属性。

### Linux 锁

```bash
# 上锁
chattr +i <文件>           # 不可变属性

# 解锁
chattr -i <文件>
```

验证状态：`lsattr <文件>` — 看到 `----i--------e--` 表示已锁定。

---

## 第五部分：标记文件机制

| 属性 | 值 |
|------|---|
| 路径 | `/tmp/hermes-memory-guard-approved` |
| 创建方式 | `touch` 命令 |
| TTL | 120 秒 |
| 消费方式 | Plugin 检测到后自动删除（一次性） |
| 跨平台 | ✅ 使用 Python `tempfile.gettempdir()`，macOS/Linux 通用 |

**安全设计：**
- 标记文件是临时的，用完即删
- 120 秒 TTL 防止过期标记被复用
- 不包含任何写入内容信息（安全无泄露）

---

## 第六部分：故障排查

| 症状 | 可能原因 | 解决方法 |
|------|---------|---------|
| Plugin 未加载 | 放错目录 / config.yaml 未启用 | 检查 plugins 目录和 config.yaml |
| 写入被 block 但标记文件已创建 | 标记文件过期（>120s） | 重新 `touch` 标记文件 |
| 解锁失败 | 文件权限不足 | 检查文件属主和权限 |
| 写入成功但重新上锁失败 | 文件被其他进程占用 | 检查是否有其他进程访问 |

---

## 第七部分：自包含清单

本 Skill 所有依赖资源：

```
tools-memory-user-file-in/
├── SKILL.md                              ← 你正在阅读的文件
└── bundled/
    └── plugins/
        └── memory-file-guard/
            ├── __init__.py               ← Plugin 源码
            └── plugin.yaml               ← Plugin 声明
```

**零外部依赖** — 所有代码均为 Python 标准库，可直接复制到任何 Hermes 系统。

### 复制到其他 Agent

```bash
# 复制整个 Skill
cp -r ~/.hermes/skills/Always/tools-memory-user-file-in <目标Agent>/skills/Always/

# 部署 Plugin
cp -r <目标Agent>/skills/Always/tools-memory-user-file-in/bundled/plugins/memory-file-guard <目标Agent>/plugins/

# 启用 Plugin（编辑 config.yaml）
# plugins:
#   enabled:
#     - memory-file-guard

# 重启
hermes gateway restart --profile <目标Agent>
```

### 复制到其他机器

```bash
scp -r ~/.hermes/skills/Always/tools-memory-user-file-in user@other:~/.hermes/skills/Always/
```

---

## 第八部分：公开分发 / 发布

当决定将本 Skill 作为独立项目公开到 GitHub 时，遵循以下工作流。详细清单见 [`references/github-release-checklist.md`](references/github-release-checklist.md)。

### 8.1 安全检查

发布前审查 `bundled/plugins/` 下的全部代码：
- **无 API key / Token / Secret / 密码** — 不应出现任何硬编码凭证
- **无个人数据** — 不含用户特定的 profile、ID、目录、联系方式
- **无机器指纹** — 不含主机名、MAC 地址、硬件序列号
- **路径通用化** — 所有路径使用 `~/.hermes/...` 这种 generic 写法，不含 `llitgq-byte`、`/Users/macmini` 等个人路径

✅ 本 Skill 已通过安全审查（2026-07-01）：纯 Python 标准库，路径通用，零凭证泄露。

### 8.2 准备发布包

```
mkdir -p ~/Documents/public_github
cp -r ~/.hermes/skills/Always/tools-memory-user-file-in ~/Documents/public_github/
```

在副本上修改，绝不直接公开原件。推荐在 `~/Documents/public_github/` 下 clone 仓库后直接编辑。

### 8.3 GitHub README 五维度模板

每份必须具备：

| 维度 | 内容 |
|------|------|
| 1️⃣ 项目描述 | 解决什么问题、保护哪些文件、触发条件 |
| 2️⃣ 安装方法 | 复制 Skill → 复制 Plugin → 启用 → 重启 |
| 3️⃣ 使用流程 | 被拦截后的完整工作流（7 步或类似） |
| 4️⃣ 跟 Agent 的交互 | 是否需要用户学习特殊指令（本 Skill 不需要） |
| 5️⃣ 配置方法 | config.yaml 加哪行条目、可选的 OS 级文件锁 |

模板结构：
- `README.zh.md`（中文）为 SKILL 内部引用的默认文档
- `README.md`（英文）为面向国际用户的公开介绍，与 SKILL 内容独立维护
- 项目定位为「探索性经验分享」，不宣称「生产就绪」
- 明确说明哪些是通用内容、哪些来自个人配置经验

### 8.4 推到 GitHub

**推荐方式：本地 git clone + SSH key（无需 gh CLI）。** 见 `references/github-release-checklist.md` Section 6。

关键步骤：
1. 生成 SSH key：`ssh-keygen -t ed25519 -C "hermes@<machine>" -f ~/.ssh/id_ed25519 -N ""`
2. 公钥添加到 GitHub → Settings → SSH and GPG keys → New SSH key
3. ⚠️ **Hermes `$HOME` 陷阱**：子 Agent 的 `$HOME` ≠ 系统 `/Users/<realuser>`，需复制 key 到真实 home 或用 `git config core.sshCommand`。详见 checklist。
4. Clone 到工作目录：`cd ~/Documents/public_github && git clone git@github.com:<owner>/<repo>.git`
5. 本地编辑后 `git add . && git commit -m "msg" && git push`

**浏览器 UI 仅作为 fallback**（仅适合简单删除操作），已知问题：
- CodeMirror 编辑器无法注入内容、`browser_type` 对长文本不可靠
- 文件路径含 `<` 会污染 git tree
- 提交消息使用 Copilot-Generated，手动检查无多余 `<` 符号

### 8.5 后期维护

- 每次修改 Plugin 代码后重新复审核
- README 与代码版本保持同步
- 每新增一份独立 Skill 到 GitHub，重复此工作流
