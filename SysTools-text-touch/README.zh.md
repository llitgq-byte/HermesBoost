# SysTools-text-touch

> Gateway 入口消息拦截与路由框架——把模糊短消息改写成明确指令。

## 它是什么

**Text-Touch** 是一个 Python Plugin 框架，挂钩在 Hermes 的 `pre_gateway_dispatch` 事件上——也就是用户消息进入 Gateway、还没送到 Agent 之前的那个瞬间。通过正则匹配将短消息（`#12 done`、`601138 S`、`茅台 vs 五粮液`）改写成明确的 skill 指令，让 Agent **不再需要猜测意图**。

## 为什么需要它

用户经常发送简短指令（代码、股票代号、ID、状态词），LLM 经常把它们路由到错误的 skill，或者反问"请详细说明"。Text-Touch 让路由**100% 确定性**——先匹配，再改写，最后执行。

### 没有 Text-Touch

```
用户：601138 S
Agent：「嗯，601138 是个数字，S 是个字母……应该做什么？」
      → 可能猜错，或者反问
```

### 有 Text-Touch

```
用户：601138 S
Text-Touch 匹配 → 改写为：
  "请加载 stock-chromeJJ skill，对 601138 执行诊股+巨潮测评+F10全景"
Agent：「明确指令，执行！」
      → 100% 准确，零误判
```

## 核心特性

- **零依赖 Python Plugin**——纯标准库（`re`、`logging`），无需 pip install
- **先到先得优先级**——长模式放前面避免被截断
- **支持 3 种动作**：`rewrite`（改写）/ `skip`（丢弃）/ `allow`（原样放行）
- **Per-Agent 隔离**——Plugin 放在 `~/.hermes/plugins/`（默认）或 `~/.hermes/profiles/<name>/plugins/`
- **热重启**——改完规则 `hermes gateway restart` 即生效
- **自带完整 walkthrough 与维护指南**——支持人和 Agent 两种操作方式

## 仓库结构

```
SysTools-text-touch/
├── README.md                          # 英文文档
├── README.zh.md                       # 本文件（中文）
└── text-touch/
    ├── SKILL.md                       # 完整 Agent 指令（700 行）
    └── templates/
        ├── __init__.py                # 可复制的 Plugin 模板（含注释）
        └── plugin.yaml                # 可复制的 Plugin 声明模板
```

## 快速开始

skill 自带可复制模板。直接对 Agent 说：

```bash
# 1. 确定你的 plugins 目录
#    - default profile → ~/.hermes/plugins/
#    - 子 Agent profile → ~/.hermes/profiles/<name>/plugins/

# 2. 创建 plugin 目录
mkdir -p ~/.hermes/plugins/my-router

# 3. 复制模板
cp ~/.hermes/skills/Always/text-touch/templates/* ~/.hermes/plugins/my-router/

# 4. 修改 plugin.yaml → 填写 name
# 5. 修改 __init__.py → 填写 _RULES

# 6. 在 config.yaml 启用：
#    plugins:
#      enabled:
#        - my-router

# 7. 重启 Gateway
hermes gateway restart
```

完整示例（任务管理：把 `#12 done` 改成标记完成，把 `5` 改成查看任务 #5）见 `text-touch/SKILL.md` 第四部分。

## Hook 协议

`pre_gateway_dispatch` 是 Hermes 消息流水线的入口 hook：

```
平台 WebSocket 收消息
    ↓
Gateway (gateway/run.py)
    ↓
┌──────────────────────────────────┐
│ pre_gateway_dispatch hook        │  ← Text-Touch 在这里拦截
│   接收 MessageEvent              │
│   返回 rewrite/skip/allow        │
└──────────────────────────────────┘
    ↓
Agent (LLM + 工具)
    ↓
┌──────────────────────────────────┐
│ transform_llm_output hook        │  ← 飞书卡片等在这里拦截
└──────────────────────────────────┘
    ↓
平台推送回复给用户
```

返回值说明：

| 返回值 | 效果 |
|--------|------|
| `None` | 原样放行 |
| `{"action": "rewrite", "text": "..."}` | 替换 event.text，继续传给 Agent |
| `{"action": "skip", "reason": "..."}` | 丢弃消息，Agent 完全看不到 |

## ⚠️ 关键：Shell Hook 不支持 rewrite（致命）

Hermes 也支持 Shell Hooks 注册到 `pre_gateway_dispatch`，但 **`_parse_response()` 只识别 `pre_tool_call` 的 `block` action**，不认识 `rewrite` / `skip`。想做改写，**必须用 Python Plugin**。详见 SKILL.md 第 7.1 节。

## 来源

本模块来自 `~/.hermes/skills/Always/text-touch/`—— Hermes 发行版的官方 always-loaded 版本。这里发布的代码、文档、walkthrough 与原版完全一致。

## Agent-Ready Prompt

复制到新 Agent 直接用：

```
从 https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-text-touch/text-touch/ 下载所有文件。

仔细读 SKILL.md，然后帮我为 Hermes Agent 搭一个正则消息路由 plugin。先问清楚：
  1. 我在哪个 profile（默认还是子 Agent）？
  2. 用户目前发送哪些短消息经常被错误路由？
  3. 每个模式应该改写到哪个 skill？

然后把 `templates/` 里的模板复制到正确的 `plugins/` 目录，按照"先长后短"的优先级顺序填入正则规则，在 config.yaml 里启用 plugin，重启 gateway。验证 `agent.log` 里出现 plugin registered 日志。
```

## 许可协议

与父仓库一致。
