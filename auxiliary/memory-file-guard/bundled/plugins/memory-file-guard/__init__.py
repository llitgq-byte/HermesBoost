"""
Memory File Guard Plugin
========================
Intercepts Hermes memory tool writes (target=memory or target=user)
and requires user confirmation before allowing the write.

Works with a marker-file mechanism:
  1. Plugin blocks memory write → returns block message
  2. Agent asks user for confirmation
  3. User approves → Agent creates marker file
  4. Agent retries memory call → Plugin detects marker → allows + deletes marker

Marker file: /tmp/hermes-memory-guard-approved
TTL: 120 seconds (prevents stale approvals)
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("plugins.memory-file-guard")

# ---------------------------------------------------------------------------
# Marker file — hardcoded /tmp for predictability (not tempfile.gettempdir()
# which may differ between Hermes gateway and agent shell processes)
# ---------------------------------------------------------------------------
MARKER_DIR = Path("/tmp")
APPROVAL_MARKER = MARKER_DIR / "hermes-memory-guard-approved"

# TTL in seconds — prevents stale approvals from being reused
MARKER_TTL = 120


def _marker_is_valid() -> bool:
    """Check if marker file exists and is within TTL."""
    if not APPROVAL_MARKER.exists():
        return False
    try:
        age = time.time() - APPROVAL_MARKER.stat().st_mtime
        if age < MARKER_TTL:
            return True
        else:
            # Expired — clean up
            APPROVAL_MARKER.unlink(missing_ok=True)
            logger.warning("approval marker expired (age=%.0fs > TTL=%ds)", age, MARKER_TTL)
            return False
    except OSError:
        return False


def _consume_marker() -> None:
    """Delete marker file after successful approval."""
    try:
        APPROVAL_MARKER.unlink()
        logger.info("approval marker consumed")
    except OSError as e:
        logger.warning("failed to delete marker: %s", e)


def _on_pre_tool_call(
    tool_name: str = "",
    args: Any = None,
    **_: Any,
) -> Optional[Dict[str, str]]:
    """Block memory/user writes unless an approval marker exists.

    Protocol:
      - Return None        → allow (pass through)
      - Return {"action": "block", "message": "..."} → block the tool call
    """
    # Only intercept the memory tool
    if tool_name != "memory":
        return None

    # Validate args
    if not args or not isinstance(args, dict):
        return None

    target = args.get("target", "")
    action = args.get("action", "")

    # Only intercept write operations to memory or user files
    if target not in ("memory", "user"):
        return None
    if action not in ("add", "replace", "remove"):
        return None

    # Check for approval marker
    if _marker_is_valid():
        _consume_marker()
        logger.info(
            "memory write APPROVED: target=%s action=%s",
            target, action,
        )
        return None  # Allow

    # No valid marker → block
    logger.info(
        "memory write BLOCKED (no approval marker): target=%s action=%s",
        target, action,
    )
    return {
        "action": "block",
        "message": (
            "[memory-file-guard] 写入被拦截。\n"
            "请按照以下步骤操作：\n"
            "1. 先读取当前文件内容（read_file）\n"
            "2. 用 clarify() 询问用户是否允许写入，展示具体变更内容\n"
            "3. 用户确认后，执行解锁命令 + touch 标记文件\n"
            "4. 重新调用 memory 工具\n"
            "5. 写入成功后，重新上锁文件\n"
            "6. 输出完整的 memory 内容和变更对比\n"
        ),
    }


def register(ctx):
    """Plugin entry point: register pre_tool_call hook."""
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
    logger.info("memory-file-guard plugin registered (pre_tool_call)")
