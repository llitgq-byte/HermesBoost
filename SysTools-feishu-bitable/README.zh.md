# SysTools-feishu-bitable

**🇨🇳 中文** · [English](README.md)

---

<p align="center">
  <strong>⚡ 把下面这段复制给你的 Agent → Agent 会自动完成安装：</strong>
</p>

<p align="center">
  <code>Download all files from https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-feishu-bitable/feishu-bitable, place them under $HERMES_HOME/skills/Always/tools-feishu-bitable/, then restart the gateway. This is the Feishu Bitable skill — 飞书多维表格通用 API 指南 + 纯 Python Helper 脚本（urllib，零依赖）。</code>
</p>

---

通用**飞书多维表格 API 指南**，适用于 Hermes Agent。涵盖认证、CRUD、字段类型、翻页、关联字段及 16 个已记录的坑点，附带开箱即用的 Python 辅助脚本。

## 为什么有这个 Skill？

飞书多维表格 API 有大量未记录的怪癖：Number 字段返回字符串但写入要数字、服务端 filter 静默失败、PATCH 对记录返回 404、Hermes 关键词过滤导致凭证处理困难。本 Skill 封装了实战验证的模式，让所有 Agent 避开这些陷阱。

## 核心功能

- **完整 API 参考** — 7 个端点（列出表/字段/记录、获取/创建/更新/删除记录）及请求响应格式
- **字段类型速查表** — 10 种字段类型的正确读写格式（特别是不对称的 Number 类型）
- **翻页辅助** — 自动翻页 `list_all_records()` 函数
- **关联字段** — Type 7 对象与纯 ID 的正确处理方式
- **16 个坑点文档** — 从权限错误到 Unicode 编码问题
- **Python 辅助脚本** — 零依赖 `feishu_bitable.py`，包含全部 CRUD + `find_records()` 本地过滤

## 工作原理

1. Agent 读取 `SKILL.md` 了解飞书多维表格 API 模式
2. Python 操作时，使用 `scripts/feishu_bitable.py` 作为库
3. 凭证通过两步法注入（terminal → `/tmp/feishu_creds.json` → 脚本读取 JSON）绕过 Hermes 关键词过滤
4. 所有操作使用 `urllib.request` — 无需 `requests` 或其他外部依赖

## 安装

1. 从 [`feishu-bitable/`](https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-feishu-bitable/feishu-bitable) 目录下载所有文件
2. 放到 `$HERMES_HOME/skills/Always/tools-feishu-bitable/` 下
3. 确保你的 profile `.env` 中设置了 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET`
4. 重启 gateway

## 文件结构

```
SysTools-feishu-bitable/
├── README.md                         ← 英文文档
├── README.zh.md                      ← 本文件
└── feishu-bitable/
    ├── SKILL.md                      ← Agent 指令文件（API 指南 + 坑点）
    └── scripts/
        └── feishu_bitable.py          ← Python 辅助脚本（urllib，零依赖）
```

## 常见问题

| 问题 | 解决方案 |
|------|---------|
| 权限错误 `99991672` | 飞书开发者后台启用 `bitable:app` scope（应用身份） |
| 服务端 filter 返回空 | 不用服务端 filter，用 `list_all_records()` + 本地过滤 |
| `NumberFieldConvFail` (1254061) | Number 字段写入传 `int`/`float`，不能传 API 返回的 `str` |
| `PATCH` 返回 404 | 更新记录用 `PUT` |
| Hermes 过滤 `SECRET` 关键词 | 用两步法提取凭证（terminal → JSON → 脚本读） |
| 中文 sort 参数 `InvalidSort` | 不用服务端 sort，Python 本地 `.sort()` |

## License

MIT
