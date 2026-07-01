# 硬编码路径迁移指南

## 背景

旧版本 `s-feishu-card-v1` 和 `feishu-table-card` 插件中存在多处硬编码路径，导致跨系统复制时失效。本文件记录所有已修复的硬编码点，供迁移时参考。

## 已修复的硬编码点

| # | 文件 | 行号 | 旧硬编码 | 新实现 | 影响 |
|---|------|------|---------|--------|------|
| 1 | `send_card.py` | 17 | `C:\Users\macmini\AppData\Local\hermes\hermes-agent` | 动态 `sys.path` 推断 + `Path.home()` | Windows 绝对路径，其他系统直接崩溃 |
| 2 | `send_card.py` | 496 | `os.path.join(os.environ.get("HERMES_HOME", ""), ".hermes", "profiles")` + `"/profiles/"` Unix 分隔符 | `pathlib.Path` 跨平台拼接 | Unix 分隔符在 Windows 上失效 |
| 3 | `__init__.py` | 122-123 | `Path.home() / ".hermes" / "skills" / "productivity" / "s-feishu-card-v1"` | 运行时从 `sys.path` / `hermes_cli` 位置推断 | 子 agent 加载了主 agent 的 Skill 路径 |
| 4 | `__init__.py` | 87 | `Path.home() / ".hermes" / ".env"` | 统一抽取到 `utils.py`，多层级 fallback | 子 agent 读取了主 agent 的凭证 |
| 5 | Profile 检测 | - | 遍历所有 profile 目录对比 FEISHU_APP_ID | `FEISHU_APP_ID` 精确匹配 | 遍历逻辑脆弱，容易误判 |

## 迁移建议

1. **优先使用 v1.1.0+ 版本**：已内置零硬编码设计
2. **如果复制旧版本**：按上表手动修改对应位置
3. **必须同步复制**：Skill + Plugin + Config + `.env` 凭证（详见 `plugin-hook-setup.md` 第六部分）
4. **Windows 特别注意**：修改源码后必须清除 `__pycache__` 并重新编译

## 路径推断优先级

```
1. HERMES_HOME 环境变量（如果已设置）
2. hermes_cli 模块文件位置 → 向上推断 hermes-agent 根目录
3. sys.path 中包含 hermes-agent 的条目
4. Path.home() / ".hermes"（fallback，跨平台）
```
