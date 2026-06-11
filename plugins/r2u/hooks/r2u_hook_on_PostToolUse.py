#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, Dict, Optional

import r2u_hook_common as c

_LOG_MASK_KEYS = frozenset({
    "prompt", "text", "content",
    "output", "pattern", "task",
    "old_string", "new_string", "context",
})


def _mask_tree_for_log(node: Any, prop_name: str = "") -> Any:
    if node is None:
        return None
    if isinstance(node, str):
        return c.pretty_string(node, prop_name, _LOG_MASK_KEYS)
    if isinstance(node, bool) or isinstance(node, (int, float)):
        return node
    if isinstance(node, dict):
        return {k: _mask_tree_for_log(v, k) for k, v in node.items()}
    if isinstance(node, list):
        return [_mask_tree_for_log(x, prop_name) for x in node]
    return node


# Field	Type	Meaning
# turn_id	string	Codex-specific extension. Active Codex turn id
# tool_name	string	Canonical hook tool name, such as Bash, apply_patch, or an MCP name like mcp__fs__read
# tool_use_id	string	Tool-call id for this invocation
# tool_input	JSON value	Tool-specific input. Bash and apply_patch use tool_input.command while MCP tools send all arguments.
# tool_response	JSON value	Tool-specific output. For MCP tools, this is the MCP call result.
# 备注: turn_id 已在 R2eHookInputHead 中解析
@dataclass
class R2eHookPostToolUseInputBody:
    tool_name: Optional[str] = None
    tool_use_id: Optional[str] = None
    tool_input: Optional[Any] = None
    tool_response: Optional[Any] = None
    others: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        payload: Dict[str, Any] = {
            "tool_name": self.tool_name,
            "tool_use_id": self.tool_use_id,
            "tool_input": self.tool_input,
            "tool_response": self.tool_response,
        }
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookPostToolUseInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookPostToolUseInputBody()
    hv = head.is_valid_Json
    if not str(body_str).strip():
        return head, inst
    if not hv:
        inst.tool_name = c.fallback_quoted(body_str, "tool_name")
        inst.tool_use_id = c.fallback_quoted(body_str, "tool_use_id")
        inst.others = c.invalid_others()
        return head, inst
    try:
        obj = json.loads(body_str)
        if not isinstance(obj, dict):
            raise ValueError("body not object")
    except Exception:
        inst.others = c.invalid_others()
        return head, inst

    if "tool_name" in obj:
        inst.tool_name = obj.pop("tool_name")
    if "tool_use_id" in obj:
        inst.tool_use_id = obj.pop("tool_use_id")
    if "tool_input" in obj:
        inst.tool_input = obj.pop("tool_input")
    if "tool_response" in obj:
        inst.tool_response = obj.pop("tool_response")
    if obj:
        inst.others = dict(obj)
    return head, inst


# Field	Effect
# continue	If false, marks that hook run as stopped
# stopReason	Recorded as the reason for stopping
# systemMessage	Surfaced as a warning in the UI or event stream
# suppressOutput	Parsed today but not yet implemented
# 备注:
# PostToolUse supports systemMessage, continue: false, and stopReason. 
# suppressOutput is parsed but not currently supported for that event.

# 额外字段
#{
#  "decision": "block",
#  "reason": "The Bash output needs review before continuing.",
#  "hookSpecificOutput": {
#    "hookEventName": "PostToolUse",
#    "additionalContext": "The command updated generated files."
#  }
#}
def build_hook_response() -> str:
    return json.dumps({"continue": True}, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    head, body = get_hook_input_body()
    with open(c.get_hook_project_log_path(head.date_string()), "a", encoding="utf-8", errors="replace") as log_file:
        log_file.write(
            f"{head.to_log_prefix()}"
            f"{body.to_string()}\n"
        )
    sys.stdout.write(build_hook_response())

