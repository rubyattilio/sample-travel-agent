"""The provider-agnostic run record every eval scores.

    {"input": str, "output": str, "replies": [str], "tool_calls": [{"name", "args", "result"}]}

Evals never see agent internals; any agent (or a production trace) only needs an
adapter that produces this shape. `from_messages` is the adapter for this agent's
Anthropic-format message history.
"""

import json


def _get(block, key):
    return block.get(key) if isinstance(block, dict) else getattr(block, key, None)


def from_messages(messages: list) -> dict:
    user_turns, replies, calls, results = [], [], [], {}
    for msg in messages:
        content = msg["content"]
        if msg["role"] == "user":
            if isinstance(content, str):
                user_turns.append(content)
            else:  # tool results
                for b in content:
                    if _get(b, "type") == "tool_result":
                        results[_get(b, "tool_use_id")] = json.loads(_get(b, "content"))
            continue
        uses = [b for b in content if _get(b, "type") == "tool_use"]
        calls += [{"id": _get(b, "id"), "name": _get(b, "name"), "args": _get(b, "input")} for b in uses]
        if not uses:  # an assistant message without tool calls is the reply the user sees
            replies.append("".join(_get(b, "text") or "" for b in content if _get(b, "type") == "text"))
    return {
        "input": "\n---\n".join(user_turns),
        "output": "\n---\n".join(replies),
        "replies": replies,
        "tool_calls": [{"name": c["name"], "args": c["args"], "result": results.get(c["id"])} for c in calls],
    }
