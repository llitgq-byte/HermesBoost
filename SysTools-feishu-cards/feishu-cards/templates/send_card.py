# ============================================================
# s-feishu-card-v1 / templates/send_card.py
# Markdown → 飞书卡片（JSON 2.0 interactive）自动转换 + 发送
# ============================================================
# 使用方式：agent 通过 execute_code 执行本模板
# 调用入口：smart_send(text, title, receive_id, ...)
# ============================================================

import os
import re
import json
import sys
import uuid
from pathlib import Path

# ---- 依赖 ----
# lark_oapi SDK（Hermes 已内置）
# 动态推断 Hermes 路径
_hermes_home = os.environ.get("HERMES_HOME", "")
if _hermes_home and ("/profiles/" in _hermes_home or "\\profiles\\" in _hermes_home):
    # profile 模式：从 profile 目录回溯到 hermes-agent
    _hermes_agent = str(Path(_hermes_home).parent.parent)
else:
    _hermes_agent = str(Path.home() / ".hermes" / "hermes-agent")

if _hermes_agent not in sys.path:
    sys.path.insert(0, _hermes_agent)

import lark_oapi as lark
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody

# ============================================================
# 配置区
# ============================================================

COLORS = ["blue", "turquoise", "violet", "green", "indigo", "orange"]

DEFAULT_MAX_CARD_SIZE = 30000   # 30KB
MAX_TABLES_PER_CARD   = 5
MAX_ELEMENTS_PER_CARD = 200
MAX_COLUMNS_PER_TABLE = 50
MAX_PAGE_SIZE         = 10


# ============================================================
# 1. 全角半角自动清洗
# ============================================================

def _looks_like_table_line(line: str) -> bool:
    """简单判断一行是否像表格行（用于清洗阶段，不依赖后续函数）"""
    stripped = line.strip()
    return bool(stripped) and stripped.startswith("|") and "|" in stripped[1:]


def clean_fullwidth(text: str) -> str:
    """将 Markdown 中的全角字符转为半角，确保飞书能识别"""

    # 全角竖线 → 半角竖线
    text = text.replace("\uff5c", "|")   # ｜ → |
    # 全角连字符 → 半角连字符
    text = text.replace("\uff0d", "-")   # － → -
    # 全角空格 → 半角空格
    text = text.replace("\u3000", " ")   # 　 → (space)

    # 确保表格块前后有空行（逐行处理，不破坏表格内部结构）
    lines = text.split("\n")
    result = []
    prev_is_table = False

    for i, line in enumerate(lines):
        curr_is_table = _looks_like_table_line(line)

        # 进入表格块：前面一行不是空行时，补一个空行
        if curr_is_table and not prev_is_table:
            if result and result[-1].strip():
                result.append("")

        result.append(line)

        # 离开表格块：后面一行不是空行时，补一个空行
        if prev_is_table and not curr_is_table:
            if line.strip():
                # 当前行是非表格非空行，在它前面补空行
                result.pop()  # 移除刚加的 line
                result.append("")  # 加空行
                result.append(line)  # 重新加 line

        prev_is_table = curr_is_table

    return "\n".join(result)


# ============================================================
# 2. Markdown 解析
# ============================================================

def is_table_line(line: str) -> bool:
    """判断一行是否属于管道表格"""
    stripped = line.strip()
    if not stripped:
        return False
    # 必须以 | 开头和结尾（容许尾部省略）
    if not stripped.startswith("|"):
        return False
    # 至少有一个 |
    return "|" in stripped[1:]


def is_separator_line(line: str) -> bool:
    """判断是否是表格分隔行 | --- | --- |"""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return False
    cells = [c.strip() for c in stripped.split("|") if c.strip()]
    return all(re.match(r'^:?-+:?$', c) for c in cells)


def _split_table_row(line: str) -> list:
    """
    安全地按 | 分割表格行，支持 \\| 转义（显示为 | 但不作为分隔符）。
    返回单元格值列表（已 strip）。
    """
    # 先按 \| 分割，保留转义标记
    parts = line.split("\\|")
    result = []
    for part in parts:
        # 每个 part 内部再按 | 分割，取第一个 | 前的内容作为当前单元格
        # 剩余部分（如果有 |）属于后续单元格
        sub_parts = part.split("|")
        # 第一个 sub_part 属于当前单元格
        if sub_parts:
            result.append(sub_parts[0])
        # 其余 sub_parts 各自成为一个单元格
        result.extend(sub_parts[1:])
    # 去掉首尾空项（由行首行尾的 | 产生）
    # 但保留中间的空单元格
    return [c.strip() for c in result]


def parse_pipe_table(lines: list) -> dict:
    """
    解析管道表格，返回 table 组件 dict
    输入：表格相关的行（表头 + 分隔行 + 数据行）
    支持 \\| 转义：在单元格内容中显示为 | 但不作为列分隔符
    """
    if len(lines) < 2:
        return None

    # 解析表头
    header_line = lines[0].strip()
    # 去掉首尾的 |
    if header_line.startswith("|"):
        header_line = header_line[1:]
    if header_line.endswith("|"):
        header_line = header_line[:-1]
    headers = _split_table_row(header_line)
    headers = [h.strip() for h in headers if h.strip()]

    # 跳过分隔行（lines[1]）
    data_lines = lines[2:]

    # 构建 columns
    columns = []
    for i, h in enumerate(headers):
        col_name = f"col_{i}"
        columns.append({
            "name": col_name,
            "display_name": h,
            "data_type": "text"
        })

    # 构建 rows
    rows = []
    for dl in data_lines:
        dl = dl.strip()
        # 去掉首尾的 |
        if dl.startswith("|"):
            dl = dl[1:]
        if dl.endswith("|"):
            dl = dl[:-1]
        cells = _split_table_row(dl)
        cells = [c.strip() for c in cells]
        row = {}
        for i in range(len(columns)):
            val = cells[i] if i < len(cells) else ""
            # 将 \| 还原为 |
            val = val.replace("\\|", "|")
            row[columns[i]["name"]] = val
        rows.append(row)

    # 推断 data_type
    for i, col in enumerate(columns):
        all_numeric = True
        has_markdown_link = False
        for row in rows:
            val = row[col["name"]]
            if val and not re.match(r'^-?\d+\.?\d*$', val):
                all_numeric = False
            if re.search(r'\[.+?\]\(.+?\)', val):
                has_markdown_link = True
        if has_markdown_link:
            col["data_type"] = "lark_md"
        elif all_numeric and any(row[col["name"]] for row in rows):
            col["data_type"] = "number"

    return {
        "tag": "table",
        "page_size": min(len(rows), MAX_PAGE_SIZE),
        "row_height": "low",
        "header_style": {
            "text_align": "left",
            "background_style": "grey",
            "bold": True
        },
        "columns": columns,
        "rows": rows
    }


def parse_markdown(text: str) -> list:
    """
    将 Markdown 文本解析为元素列表
    每个元素: {"type": "paragraph"|"table"|"hr", "content": str|dict}
    """
    lines = text.split("\n")
    elements = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # --- 空行 ---
        if not line.strip():
            i += 1
            continue

        # --- 分割线 ---
        if line.strip() in ("---", "***", "___"):
            elements.append({"type": "hr", "content": None})
            i += 1
            continue

        # --- 代码块 ---
        if line.strip().startswith("```"):
            code_lines = [line]
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                code_lines.append(lines[i])  # 闭合 ```
                i += 1
            elements.append({"type": "paragraph", "content": "\n".join(code_lines)})
            continue

        # --- 管道表格 ---
        if is_table_line(line):
            table_lines = []
            while i < len(lines) and is_table_line(lines[i]):
                table_lines.append(lines[i])
                i += 1
            table_obj = parse_pipe_table(table_lines)
            if table_obj:
                elements.append({"type": "table", "content": table_obj})
            else:
                # 解析失败，当普通段落保留
                elements.append({"type": "paragraph", "content": "\n".join(table_lines)})
            continue

        # --- 普通段落（标题、列表、引用、普通文本）---
        para_lines = [line]
        i += 1
        while i < len(lines):
            next_line = lines[i]
            # 遇到以下情况停止合并
            if not next_line.strip():
                break
            if next_line.strip() in ("---", "***", "___"):
                break
            if next_line.strip().startswith("```"):
                break
            if is_table_line(next_line):
                break
            para_lines.append(next_line)
            i += 1

        elements.append({"type": "paragraph", "content": "\n".join(para_lines)})

    return elements


# ============================================================
# 3. 构建卡片 JSON
# ============================================================

def extract_first_heading(text: str) -> str:
    """提取第一个 # 标题作为卡片标题"""
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#") and not stripped.startswith("##"):
            title = stripped.lstrip("#").strip()
            if title:
                return title
    return ""


def build_card(elements: list, title: str, template_color: str = "blue") -> dict:
    """
    将元素列表组装为完整卡片 JSON 2.0
    """
    card_elements = []
    table_count = 0
    md_parts = []

    def flush_md():
        """将累积的段落合并为一个 markdown 组件"""
        nonlocal md_parts
        if md_parts:
            card_elements.append({
                "tag": "markdown",
                "content": "\n\n".join(md_parts)
            })
            md_parts = []

    for elem in elements:
        if elem["type"] == "hr":
            flush_md()
            card_elements.append({"tag": "hr"})
        elif elem["type"] == "table":
            flush_md()
            if table_count < MAX_TABLES_PER_CARD:
                card_elements.append(elem["content"])
                table_count += 1
            else:
                # 超过5个表格，降级为 markdown 管道语法
                # 从 table 对象还原管道文本
                cols = elem["content"]["columns"]
                rows = elem["content"]["rows"]
                header = "| " + " | ".join(c["display_name"] for c in cols) + " |"
                sep = "| " + " | ".join("---" for _ in cols) + " |"
                data_lines = []
                for row in rows:
                    data_lines.append("| " + " | ".join(row.get(c["name"], "") for c in cols) + " |")
                pipe_text = header + "\n" + sep + "\n" + "\n".join(data_lines)
                md_parts.append(pipe_text)
        elif elem["type"] == "paragraph":
            md_parts.append(elem["content"])

    flush_md()

    # 去掉标题行（如果和卡片标题一致的话）
    # 检查第一个 markdown 组件是否以 # 开头且与 title 匹配
    if card_elements and card_elements[0].get("tag") == "markdown":
        first_md = card_elements[0]["content"]
        first_line = first_md.split("\n")[0].strip()
        if first_line.startswith("#") and not first_line.startswith("##"):
            clean_title = first_line.lstrip("#").strip()
            if clean_title == title:
                remaining = "\n".join(first_md.split("\n")[1:]).strip()
                if remaining:
                    card_elements[0]["content"] = remaining
                else:
                    card_elements.pop(0)

    card = {
        "schema": "2.0",
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"content": title, "tag": "plain_text"},
            "template": template_color,
        },
        "body": {
            "direction": "vertical",
            "elements": card_elements
        }
    }
    return card


# ============================================================
# 4. 限制检查
# ============================================================

def check_limits(card: dict) -> dict:
    """
    检查卡片是否符合所有限制
    返回 {"ok": bool, "size": int, "tables": int, "elements": int, "error": str}
    """
    card_json_str = json.dumps(card, ensure_ascii=False)
    size = len(card_json_str.encode("utf-8"))

    elements = card.get("body", {}).get("elements", [])
    elem_count = len(elements)
    table_count = sum(1 for e in elements if e.get("tag") == "table")

    errors = []
    if size > DEFAULT_MAX_CARD_SIZE:
        errors.append(f"JSON 大小 {size} 字节超过限制 {DEFAULT_MAX_CARD_SIZE}")
    if table_count > MAX_TABLES_PER_CARD:
        errors.append(f"表格数 {table_count} 超过限制 {MAX_TABLES_PER_CARD}")
    if elem_count > MAX_ELEMENTS_PER_CARD:
        errors.append(f"组件数 {elem_count} 超过限制 {MAX_ELEMENTS_PER_CARD}")

    return {
        "ok": len(errors) == 0,
        "size": size,
        "tables": table_count,
        "elements": elem_count,
        "error": "; ".join(errors) if errors else None
    }


# ============================================================
# 5. 拆分逻辑
# ============================================================

def find_split_point(elements: list, max_tables: int = MAX_TABLES_PER_CARD) -> int:
    """
    找到合适的拆分点索引
    优先级：## 二级标题 > --- 分割线 > 空行（段落之间）
    返回拆分索引（在该元素之前拆分）
    """
    # 从后往前找，确保每部分尽量大
    table_count = 0
    for i, elem in enumerate(elements):
        if elem["type"] == "table":
            table_count += 1

    # 从头开始累计表格数，在达到 max_tables 时寻找最近的拆分点
    running_tables = 0
    last_heading = -1
    last_hr = -1
    last_para = -1

    for i, elem in enumerate(elements):
        if elem["type"] == "table":
            running_tables += 1
            if running_tables > max_tables:
                # 超了，在之前的最佳拆分点拆
                if last_heading > 0:
                    return last_heading
                elif last_hr > 0:
                    return last_hr
                elif last_para > 0:
                    return last_para
                else:
                    return i  # 实在找不到好点，就在当前位置
        elif elem["type"] == "paragraph":
            content = elem["content"]
            first_line = content.split("\n")[0].strip()
            if first_line.startswith("##"):
                last_heading = i
            else:
                last_para = i
        elif elem["type"] == "hr":
            last_hr = i

    return len(elements)  # 不需要拆分


def _count_raw_tables(elements: list) -> int:
    """统计原始元素中的表格数量（不受 build_card 降级影响）"""
    return sum(1 for e in elements if e["type"] == "table")


def _estimate_card_size(elements: list, title: str) -> int:
    """预估卡片 JSON 大小（不实际构建，快速估算）"""
    # 粗略估算：文本内容 + JSON 结构开销
    text_size = 0
    for e in elements:
        if e["type"] == "table":
            cols = e["content"].get("columns", [])
            rows = e["content"].get("rows", [])
            text_size += sum(len(c["display_name"]) for c in cols)
            for row in rows:
                text_size += sum(len(str(v)) for v in row.values())
            text_size += 200  # table JSON 结构开销
        elif e["type"] == "paragraph" and e["content"]:
            text_size += len(e["content"])
        else:
            text_size += 20  # hr 等
    # 加上卡片外壳、header、config 等固定开销
    return text_size + len(title) + 500


def split_elements(elements: list, title: str) -> list[list]:
    """
    将元素列表拆分为多个子列表，每个子列表对应一张卡片
    在原始元素层面检查表格数量，不受 build_card 降级影响
    """
    raw_tables = _count_raw_tables(elements)
    est_size = _estimate_card_size(elements, title)

    # 快速检查：不需要拆分
    if raw_tables <= MAX_TABLES_PER_CARD and est_size <= DEFAULT_MAX_CARD_SIZE:
        test_card = build_card(elements, title, "blue")
        check = check_limits(test_card)
        if check["ok"]:
            return [elements]

    # 需要拆分：逐段累积元素，达到限制时拆分
    result = []
    current_chunk = []

    for elem in elements:
        # 检查加入这个元素后是否超限
        test_chunk = current_chunk + [elem]
        chunk_tables = _count_raw_tables(test_chunk)
        chunk_size = _estimate_card_size(test_chunk, title)

        if chunk_tables > MAX_TABLES_PER_CARD or chunk_size > DEFAULT_MAX_CARD_SIZE:
            # 当前 chunk 已满，先保存
            if current_chunk:
                result.append(current_chunk)
            current_chunk = [elem]
        else:
            current_chunk.append(elem)

    # 保存最后一个 chunk
    if current_chunk:
        result.append(current_chunk)

    return result


# ============================================================
# 6. 发送到飞书
# ============================================================

def send_to_feishu(card: dict, receive_id: str, receive_id_type: str = "chat_id",
                   app_id: str = None, app_secret: str = None) -> dict:
    """
    发送单张卡片到飞书
    返回 {"success": bool, "message_id": str, "error": str}
    """
    # 获取凭证（优先参数 > 环境变量 > .env 文件）
    _app_id = app_id or os.environ.get("FEISHU_APP_ID", "")
    _app_secret = app_secret or os.environ.get("FEISHU_APP_SECRET", "")

    # 环境变量为空时，尝试直接读取 .env 文件
    # 原因：terminal grep 会屏蔽含 "secret" 的值，导致通过 terminal 设置的 env 可能丢失
    # 修复：支持子 agent（profile）模式，优先读取当前 profile 的 .env
    # 修复：Windows 路径用反斜杠，Unix 用正斜杠，两种都要检查
    if not _app_id or not _app_secret:
        hermes_home = os.environ.get("HERMES_HOME", "")
        if hermes_home and ("/profiles/" in hermes_home or "\\profiles\\" in hermes_home):
            env_path = os.path.join(hermes_home, ".env")
        else:
            env_path = os.path.expanduser("~/.hermes/.env")
        
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        if k == "FEISHU_APP_ID" and not _app_id:
                            _app_id = v
                        elif k == "FEISHU_APP_SECRET" and not _app_secret:
                            _app_secret = v

    if not _app_id or not _app_secret:
        return {
            "success": False,
            "message_id": None,
            "error": "缺少 app_id 或 app_secret，请设置环境变量 FEISHU_APP_ID / FEISHU_APP_SECRET，或确保 ~/.hermes/.env 文件存在"
        }

    try:
        # 构建 SDK 客户端
        client = (
            lark.Client.builder()
            .app_id(_app_id)
            .app_secret(_app_secret)
            .domain(lark.FEISHU_DOMAIN)
            .log_level(lark.LogLevel.WARNING)
            .build()
        )

        # 序列化卡片 JSON
        card_str = json.dumps(card, ensure_ascii=False)

        # 构建请求
        body = (
            CreateMessageRequestBody.builder()
            .receive_id(receive_id)
            .msg_type("interactive")
            .content(card_str)
            .uuid(str(uuid.uuid4()))
            .build()
        )

        request = (
            CreateMessageRequest.builder()
            .receive_id_type(receive_id_type)
            .request_body(body)
            .build()
        )

        # 发送
        response = client.im.v1.message.create(request)

        # 修复：response.success() 不可靠，同时检查 response.code == 0
        response_code = getattr(response, 'code', None)
        is_success = response.success() or (response_code == 0)

        if is_success:
            msg_id = response.data.message_id if response.data else None
            return {"success": True, "message_id": msg_id, "error": None}
        else:
            error_msg = f"code={response.code}, msg={response.msg}"
            return {"success": False, "message_id": None, "error": error_msg}

    except Exception as e:
        return {"success": False, "message_id": None, "error": str(e)}


# ============================================================
# 7. 总入口
# ============================================================

def smart_send(text: str, title: str, receive_id: str,
               receive_id_type: str = "chat_id",
               app_id: str = None, app_secret: str = None,
               max_card_size: int = DEFAULT_MAX_CARD_SIZE) -> dict:
    """
    一次性完成：清洗 → 解析 → 转换 → 判定 → 拆分 → 发送

    参数:
        text:             Markdown 文本内容
        title:            卡片标题（agent 总结）
        receive_id:       目标聊天窗口 ID
        receive_id_type:  "chat_id" 或 "open_id"
        app_id:           飞书 App ID（可选，默认读环境变量）
        app_secret:       飞书 App Secret（可选，默认读环境变量）
        max_card_size:    单张卡片最大字节数（默认 30000）

    返回:
        {
            "success": bool,
            "cards_sent": int,
            "message_ids": [str, ...],
            "cards": [dict, ...],   # 生成的卡片 JSON（调试用）
            "error": str or None,
            "suggestion": str or None
        }
    """
    global DEFAULT_MAX_CARD_SIZE
    DEFAULT_MAX_CARD_SIZE = max_card_size

    # 1. 清洗
    cleaned = clean_fullwidth(text)

    # 2. 确定标题
    if not title:
        title = extract_first_heading(cleaned)
    if not title:
        first_line = cleaned.strip().split("\n")[0][:20]
        title = first_line + ("..." if len(first_line) >= 20 else "")

    # 3. 解析
    elements = parse_markdown(cleaned)

    if not elements:
        return {
            "success": False,
            "cards_sent": 0,
            "message_ids": [],
            "cards": [],
            "error": "解析后无内容",
            "suggestion": "请检查 Markdown 文本是否为空"
        }

    # 4. 拆分
    chunks = split_elements(elements, title)

    # 5. 构建卡片并发送
    cards = []
    message_ids = []
    errors = []

    for idx, chunk in enumerate(chunks):
        # 标题
        if idx == 0:
            card_title = title
        else:
            card_title = f"{title}（续 {idx + 1}）"

        # 颜色轮换
        color = COLORS[idx % len(COLORS)]

        # 构建卡片
        card = build_card(chunk, card_title, color)
        cards.append(card)

        # 检查限制
        check = check_limits(card)
        if not check["ok"]:
            errors.append(f"卡片 {idx + 1} 限制检查失败: {check['error']}")
            continue

        # 发送
        result = send_to_feishu(card, receive_id, receive_id_type, app_id, app_secret)
        if result["success"]:
            message_ids.append(result["message_id"])
        else:
            errors.append(f"卡片 {idx + 1} 发送失败: {result['error']}")
            break  # 发送失败，停止后续

    # 6. 汇总结果
    success = len(errors) == 0 and len(message_ids) > 0
    return {
        "success": success,
        "cards_sent": len(message_ids),
        "message_ids": message_ids,
        "cards": cards,
        "error": "; ".join(errors) if errors else None,
        "suggestion": "如果仍然失败，可尝试缩减内容或拆分表格" if errors else None
    }


# ============================================================
# 8. 调用示例（agent 使用 execute_code 时替换参数）
# ============================================================
#
# result = smart_send(
#     text="""
# ## 功能对比
#
# | 类型 | 表格 | 标题 |
# |------|------|------|
# | text | ❌   | ❌   |
# | card | ✅   | ✅   |
#
# 正文内容...
# """,
#     title="功能对比",
#     receive_id="<chat_id>",
# )
# print(json.dumps(result, ensure_ascii=False, indent=2))
