# 飞书卡片 JSON 2.0 规范参考

## 卡片整体结构

```json
{
  "schema": "2.0",
  "config": {
    "wide_screen_mode": true
  },
  "header": {
    "title": {"content": "标题", "tag": "plain_text"},
    "subtitle": {"content": "副标题", "tag": "plain_text"},
    "template": "blue",
    "ud_icon": {"tag": "standard_icon", "token": "icon_name"}
  },
  "body": {
    "direction": "vertical",
    "padding": "12px 12px 12px 12px",
    "elements": [...]
  }
}
```

**关键：JSON 2.0 用 `body.elements`，不是顶层的 `elements`！**

## 可用颜色（header.template）

| 颜色 | 值 |
|------|-----|
| 蓝色 | `blue` |
| 浅蓝 | `wathet` |
| 青绿 | `turquoise` |
| 绿色 | `green` |
| 黄色 | `yellow` |
| 橙色 | `orange` |
| 红色 | `red` |
| 胭脂红 | `carmine` |
| 紫罗兰 | `violet` |
| 紫色 | `purple` |
| 靛蓝 | `indigo` |
| 灰色 | `grey` |
| 默认 | `default` |

## body.elements 支持的组件

### markdown（富文本）

```json
{
  "tag": "markdown",
  "content": "支持完整 Markdown 语法",
  "text_align": "left"
}
```

支持语法：h1-h6、加粗、斜体、删除线、超链接、代码块、有序/无序列表、引用、图片、分割线、飞书表情、标签、管道表格（最多4个/元素，5行/表）

### table（结构化表格）

```json
{
  "tag": "table",
  "page_size": 10,
  "row_height": "low",
  "header_style": {
    "text_align": "left",
    "background_style": "grey",
    "bold": true
  },
  "columns": [
    {"name": "col_name", "display_name": "显示名", "data_type": "text"}
  ],
  "rows": [
    {"col_name": "值"}
  ]
}
```

**data_type 可选值：** `text`、`lark_md`、`markdown`、`number`、`options`、`persons`、`date`

**header_style.background_style：** `grey`、`blue`、`green`、`yellow`、`red`、`violet`、`default`

### hr（分割线）

```json
{"tag": "hr"}
```

### button（按钮，可选）

```json
{
  "tag": "button",
  "text": {"tag": "plain_text", "content": "按钮文字"},
  "type": "default",
  "size": "medium",
  "behaviors": [{"type": "open_url", "default_url": "https://..."}]
}
```

## 限制汇总

| 项目 | 限制 |
|------|------|
| 卡片请求体 | 30 KB |
| 组件总数 | 200 个 |
| table 组件 | 5 个/卡片 |
| 每个 table 列数 | 50 列 |
| 每个 table 每页行数 | 10 行（page_size 1-10） |
| markdown 内管道表格 | 4 个/markdown 元素 |
| 管道表格每表可见行 | 5 行（超出自动分页） |
| 标题后缀标签 | 3 个 |

## JSON 2.0 不支持的组件

- ❌ `note` 标签（会报错 code=200861）
- ❌ 旧版 `elements` 顶层结构（必须用 `body.elements`）
