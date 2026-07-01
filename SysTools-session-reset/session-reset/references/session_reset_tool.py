#!/usr/bin/env python3
"""
Session Reset Tool — Deferred session clearing after agent finishes its turn.

This tool lets the agent request a session reset that executes AFTER the final
response is delivered to the user.  The agent calls session_reset(reason=...)
during its tool loop; the actual reset is deferred to the gateway's post-agent
cleanup phase (in run.py), so all messages — feishu cards, text replies — are
sent before the session is cleared.

Use this in Skill instructions to automatically clear bloated context after
complex multi-step tasks (e.g. stock analysis, multi-search reports).

How it works:
  1. Agent calls session_reset(reason="...") during tool loop
  2. Tool handler sets agent._pending_session_reset = True
  3. Agent continues generating its final text response
  4. Gateway delivers all messages (cards, text, voice, etc.)
  5. Gateway checks the flag and executes the real session reset
  6. Next user message starts with a clean session
"""

import json
import logging

logger = logging.getLogger(__name__)


SESSION_RESET_SCHEMA = {
    "type": "function",
    "function": {
        "name": "session_reset",
        "description": (
            "Request a session reset that takes effect AFTER this reply is delivered. "
            "Use this at the END of complex tasks (multi-step analysis, heavy tool usage) "
            "to clear bloated context. The current reply will be delivered normally; "
            "the next message starts fresh with a clean session. "
            "Do NOT use this for simple queries or conversations where retaining context matters."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": (
                        "Why the session is being reset. "
                        "Example: 'Completed stock analysis for 5 stocks' "
                        "This is logged for auditing."
                    )
                }
            },
            "required": ["reason"]
        }
    }
}


def session_reset_tool(reason: str, **kw) -> str:
    """Set a pending-reset flag on the agent instance.

    The actual reset happens in the gateway's post-agent cleanup phase
    (run.py), after all messages have been delivered to the user.

    Args:
        reason: Why the session should be reset (for logging).
        **kw: Keyword args — unused, present for registry compatibility.

    Returns:
        Confirmation string shown to the model in the tool result.
    """
    return (
        "✅ Session reset requested. "
        f"Reason: {reason[:200]}. "
        "The session will be cleared after this reply is delivered."
    )


# --- Registry ---
from tools.registry import registry, tool_error

registry.register(
    name="session_reset",
    toolset="hermes-cli",
    schema=SESSION_RESET_SCHEMA,
    handler=lambda args, **kw: session_reset_tool(
        reason=args.get("reason", "no reason provided"),
        **kw
    ),
    emoji="🔄",
)
