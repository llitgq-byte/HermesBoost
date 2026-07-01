"""
<Plugin Name> Plugin
====================
[一句话描述这个 plugin 做什么]

Routes (first match wins):
  1. [模式1描述]
  2. [模式2描述]
  ...
  Others → pass through (return None)
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger("plugins.<plugin-name>")

# ---------------------------------------------------------------------------
# 匹配规则列表
# ---------------------------------------------------------------------------
# 格式: ("规则名称", 正则表达式, "rewrite 模板（用 {} 做占位符）")
# 按顺序匹配，先到先得！注意：更长的模式必须放在更短的模式前面
# ---------------------------------------------------------------------------

_RULES: list[tuple[str, re.Pattern, str]] = [
    # 示例 1：精确匹配特定关键词
    # ("关键词匹配",
    #  re.compile(r"^某个特定命令$"),
    #  "请加载 xxx skill，执行某个操作"),

    # 示例 2：带捕获组的模式
    # ("参数匹配",
    #  re.compile(r"^(.+)\s+动词\s+(.+)$"),
    #  "请加载 xxx skill，对 {} 执行 {}"),

    # 示例 3：纯数字精确匹配（如 6 位代码）
    # ("代码匹配",
    #  re.compile(r"^(\d{6})$"),
    #  "请加载 xxx skill，分析 {}"),
]


def _on_pre_gateway_dispatch(
    event: Any,
    gateway: Any = None,
    session_store: Any = None,
    **kwargs,
) -> Optional[Dict[str, str]]:
    """拦截用户消息，匹配规则后 rewrite 为明确的 skill 指令。"""
    text = getattr(event, "text", "")
    if not text:
        return None

    for name, pattern, template in _RULES:
        m = pattern.match(text.strip())
        if m:
            rewrite_text = template.format(*m.groups())
            logger.info(
                "matched [%s]: '%s' → '%s'",
                name, text.strip(), rewrite_text,
            )
            return {"action": "rewrite", "text": rewrite_text}

    return None


def register(ctx):
    """Plugin 入口：注册 pre_gateway_dispatch hook。"""
    ctx.register_hook("pre_gateway_dispatch", _on_pre_gateway_dispatch)
    logger.info("<plugin-name> plugin registered (pre_gateway_dispatch)")
