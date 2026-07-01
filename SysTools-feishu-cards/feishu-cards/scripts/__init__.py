"""
Feishu Table Card Plugin
========================
Automatically detects markdown tables in agent responses on Feishu platform
and sends them as interactive Feishu cards (JSON 2.0) instead of plain text.

How it works:
1. Registers a transform_llm_output hook
2. Before each response is delivered, checks if it contains markdown tables
3. If yes: sends the response as a Feishu card via API, strips tables from text
4. If no: passes through unchanged

The card building logic is imported from s-feishu-card-v1 Skill's send_card.py.

SETUP: See references/plugin-hook-setup.md for full installation guide.
"""

from __future__ import annotations

import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("plugins.feishu-table-card")

# ---------------------------------------------------------------------------
# Table detection
# ---------------------------------------------------------------------------

# Matches markdown pipe table: header row + separator row + 1+ data rows
# Supports full-width pipes (｜) and mixed spacing
_TABLE_RE = re.compile(
    r"(\|[^|\n]+\|\s*\n)"          # header row (at least one pipe-delimited cell)
    r"(\|[\s\-:|｜]+?\|\s*\n)"      # separator row (dashes, colons, optional spaces/pipes)
    r"((?:\|[^|\n]+\|\s*\n?)+)",    # data rows (1 or more)
    re.MULTILINE,
)

# Simpler fallback: just look for the separator line pattern
_TABLE_SEP_RE = re.compile(
    r"^\|[\s\-:]+?\|$",
    re.MULTILINE,
)


def _contains_table(text: str) -> bool:
    """Check if text contains at least one markdown pipe table."""
    if _TABLE_RE.search(text):
        return True
    # Fallback: just look for separator pattern
    if _TABLE_SEP_RE.search(text):
        return True
    return False


def _strip_tables(text: str) -> str:
    """Replace each table block with a card reference."""
    return _TABLE_RE.sub("\n*表格内容见上方卡片*\n", text)


# ---------------------------------------------------------------------------
# Card sending (reuses s-feishu-card-v1 Skill logic)
# ---------------------------------------------------------------------------

_card_module = None  # Lazy-loaded


def _get_card_module():
    """Lazy-import the send_card module from the Skill."""
    global _card_module
    if _card_module is not None:
        return _card_module

    skill_path = (
        Path.home()
        / ".hermes"
        / "skills"
        / "productivity"
        / "s-feishu-card-v1"
        / "templates"
    )

    if not skill_path.exists():
        logger.warning("s-feishu-card-v1 Skill templates not found at %s", skill_path)
        return None

    if str(skill_path) not in sys.path:
        sys.path.insert(0, str(skill_path))

    try:
        import send_card as mod
        _card_module = mod
        logger.info("Loaded send_card from Skill: %s", skill_path)
        return mod
    except Exception as e:
        logger.error("Failed to load send_card module: %s", e)
        return None


def _get_feishu_credentials() -> tuple[str, str]:
    """Read Feishu APP_ID and APP_SECRET from .env file."""
    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")

    if app_id and app_secret:
        return app_id, app_secret

    # Fallback: read from .env directly (terminal grep masks secrets)
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k == "FEISHU_APP_ID" and not app_id:
                    app_id = v
                elif k == "FEISHU_APP_SECRET" and not app_secret:
                    app_secret = v

    return app_id, app_secret


def _extract_chat_id(session_id: str, **kwargs) -> str:
    """Try to extract Feishu chat_id from session context."""
    # 1. Check kwargs first
    for key in ("chat_id", "receive_id", "group_id"):
        val = kwargs.get(key)
        if val and val.startswith("oc_"):
            return val

    # 2. Parse session_id (format may be "feishu:ou_xxx:oc_xxx" or similar)
    if session_id and "oc_" in session_id:
        parts = session_id.split(":")
        for part in parts:
            if part.startswith("oc_"):
                return part

    # 3. Fallback to env or default
    return os.environ.get(
        "FEISHU_DEFAULT_CHAT_ID",
        "<default_chat_id>",
    )


def _send_card(response_text: str, receive_id: str) -> dict:
    """Build and send a Feishu card from the response text."""
    mod = _get_card_module()
    if mod is None:
        return {"success": False, "error": "send_card module not available"}

    # Ensure credentials are in env
    app_id, app_secret = _get_feishu_credentials()
    if not os.environ.get("FEISHU_APP_ID"):
        os.environ["FEISHU_APP_ID"] = app_id
    if not os.environ.get("FEISHU_APP_SECRET"):
        os.environ["FEISHU_APP_SECRET"] = app_secret

    try:
        result = mod.smart_send(
            text=response_text,
            title=None,  # Auto-detect from first line
            receive_id=receive_id,
        )
        return result
    except Exception as e:
        logger.error("smart_send failed: %s", e, exc_info=True)
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Hook callback
# ---------------------------------------------------------------------------


def _on_transform_llm_output(
    response_text: str,
    session_id: str,
    model: str,
    platform: str,
    **kwargs,
) -> Optional[str]:
    """
    transform_llm_output hook.

    - Only activates for Feishu/Lark platform
    - Only when response contains markdown tables
    - Sends card via API, returns text with tables stripped
    """
    # Only for Feishu
    if platform not in ("feishu", "lark"):
        return None

    # Check for tables
    if not _contains_table(response_text):
        return None

    logger.info(
        "Detected table in Feishu response (%d chars), sending as card",
        len(response_text),
    )

    # Get receive_id
    receive_id = _extract_chat_id(session_id, **kwargs)
    logger.info("Sending card to receive_id=%s", receive_id)

    # Send card
    result = _send_card(response_text, receive_id)

    if result.get("success"):
        logger.info("Card sent OK: %s", result.get("message_ids"))
        # Return text with tables stripped (non-table content still delivered as text)
        stripped = _strip_tables(response_text).strip()
        if stripped:
            return stripped
        # If nothing left after stripping, return a minimal marker
        return "📊 *内容已通过上方卡片发送*"
    else:
        logger.warning(
            "Card send failed: %s — falling back to plain text",
            result.get("error"),
        )
        return None  # Fall back to original text


# ---------------------------------------------------------------------------
# Plugin registration
# ---------------------------------------------------------------------------


def register(ctx):
    """Called by Hermes plugin loader to register hooks."""
    ctx.register_hook("transform_llm_output", _on_transform_llm_output)
    logger.info("feishu-table-card plugin registered (transform_llm_output)")
