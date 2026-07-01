# 跨平台零配置可移植性指南

## 设计目标

将 `s-feishu-card-v1` 和 `feishu-table-card` 设计为**零硬编码、零配置、跨平台**的可移植组件：

- **零硬编码路径**：所有路径运行时动态推断，不写死任何绝对路径
- **零配置部署**：复制到任意 Hermes 实例后无需修改代码即可运行
- **跨平台兼容**：Windows / macOS / Linux 统一通过 `pathlib` 处理
- **Skill + Plugin 共用工具**：提取 `utils.py` 避免重复代码

## 架构图（v2.0）

```
s-feishu-card-v1/
├── SKILL.md              # Skill 知识库
├── README.md             # 部署文档（面向用户）
├── templates/
│   ├── send_card.py      # 卡片构建与发送核心逻辑
│   ├── utils.py          # ★ 共用工具（路径推断、凭证读取、环境检测）
│   └── feishu_card_template.json
└── scripts/
    └── install_plugin.py # 一键安装脚本

~/.hermes/plugins/feishu-table-card/
├── __init__.py           # Plugin 入口（导入 utils.py，零硬编码）
├── plugin.yaml           # 插件声明（v2.0.0）
└── utils.py              # 复制自 Skill（避免跨目录导入）
```

## 已移除的硬编码点（v2.0 完整清单）

| # | 位置 | 旧硬编码（v1.x） | 新实现（v2.0） | 影响 |
|---|------|----------------|---------------|------|
| 1 | `send_card.py:17` | `C:\Users\macmini\...` Windows 绝对路径 | 动态 `sys.path` 推断 + `Path.home()` | 跨系统复制后无需修改 |
| 2 | `send_card.py:496` | `"/profiles/"` Unix 分隔符 | `pathlib.Path` 跨平台拼接 | Windows/Mac 统一支持 |
| 3 | `__init__.py:122` | `~/.hermes/skills/productivity/s-feishu-card-v1` | `utils.find_skill_template()` 递归搜索 | 不依赖分类名称 |
| 4 | `__init__.py:87` | `~/.hermes/.env` 重复凭证逻辑 | `utils.get_feishu_credentials()` 统一读取 | Skill + Plugin 共用 |
| 5 | `__init__.py:235` | 硬编码 fallback chat_id `oc_d6f9ed86...` | 完全移除，仅依赖参数/环境变量 | 避免发到错误窗口 |
| 6 | `__init__.py:147` | 重复实现 `.env` 解析 | 统一调用 `utils.read_env_file()` | 减少维护成本 |
| 7 | `send_card.py` | 独立实现路径推断 | 导入 `utils.get_hermes_home()` 等函数 | 代码复用 |

## utils.py 共用工具 API

```python
# 路径推断
get_hermes_home() -> Path          # 当前 Hermes 实例根目录
get_hermes_repo_path() -> str      # Hermes 源码/安装目录
find_skill_template(name) -> Path  # 查找 Skill 模板目录（递归搜索）
get_env_path() -> Path             # 当前实例的 .env 文件路径

# 凭证读取
read_env_file(path) -> dict        # 读取 .env 为字典
get_feishu_credentials() -> tuple  # 获取 (app_id, app_secret)
get_feishu_chat_id() -> str        # 获取 chat_id（零硬编码 fallback）

# 环境检测
is_profile_mode() -> bool          # 是否在 profile 模式下
get_current_profile_name() -> str  # 当前 profile 名称

# 跨平台兼容
ensure_lark_oapi()                 # 确保 lark_oapi 可导入

# 调试
dump_env_info() -> str             # 输出环境诊断信息
```

## 路径推断优先级（运行时）

```
1. HERMES_HOME 环境变量（如果已设置）
2. 当前文件位置回溯（utils.py → templates/ → skill/ → skills/ → .hermes/）
3. hermes_cli 模块文件位置 → 向上推断 hermes-agent 根目录
4. sys.path 中包含 hermes-agent 的条目
5. Path.home() / ".hermes"（最终 fallback，跨平台）
```

## 跨平台兼容性

| 平台 | 路径处理 | 额外注意事项 |
|------|---------|-------------|
| Windows | `pathlib.Path` 自动处理 `\` 和 `/` | 修改源码后必须清除 `__pycache__` 并重新编译 |
| macOS | `pathlib.Path` 自动处理 `/` | 无特殊要求 |
| Linux | `pathlib.Path` 自动处理 `/` | 无特殊要求 |
| WSL | 混合路径 | 统一用 `Path()` 包装 |

## 迁移检查清单（v2.0 简化版）

复制 Skill 到新系统后，只需执行：

```bash
# 1. 一键安装（自动复制 Plugin + 启用 + 重启）
python ~/.hermes/skills/productivity/s-feishu-card-v1/scripts/install_plugin.py

# 2. 验证
hermes logs | grep "feishu-table-card.*registered"
```

或手动执行：

```bash
# 1. 复制 Plugin
cp -r ~/.hermes/skills/productivity/s-feishu-card-v1/scripts/feishu-table-card \
      ~/.hermes/plugins/

# 2. 启用
hermes plugins enable feishu-table-card

# 3. 重启
hermes restart gateway

# 4. 清除缓存（Windows 必须）
find ~/.hermes/plugins -name "__pycache__" -exec rm -rf {} +
python -m py_compile ~/.hermes/plugins/feishu-table-card/__init__.py

# 5. 发送测试消息验证
```

## 调试命令

```bash
# 环境诊断
python ~/.hermes/skills/productivity/s-feishu-card-v1/templates/utils.py

# 插件版本扫描（多 profile）
python ~/.hermes/skills/productivity/s-feishu-card-v1/scripts/scan_plugin_versions.py
```

## Mac 复盘关键教训（2025-05）

从 Mac 系统迁移时遇到的实际问题：

1. **不要硬编码 chat_id** — 飞书聊天 ID 是动态的，每个会话不同
2. **注意 Python 私有属性命名** — `_chat_id` ≠ `chat_id`
3. **Gateway hook 参数不完整** — 官方的 `transform_llm_output` hook 只传了 4 个参数，缺少上下文信息，需要自己补传 `chat_id` 和 `user_id`
4. **插件修改后必须重启 + 新会话** — 代码修改和插件加载都在启动时完成
5. **Windows 必须清 `__pycache__`** — Python 的 `.pyc` 缓存不会自动刷新
