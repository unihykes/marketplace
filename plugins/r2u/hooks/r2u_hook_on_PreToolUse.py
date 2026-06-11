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
    "old_string", "new_string", "context"
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
# 备注: turn_id 已在 R2eHookInputHead 中解析
@dataclass
class R2eHookPreToolUseInputBody:
    tool_name: Optional[str] = None
    tool_use_id: Optional[str] = None
    tool_input: Optional[Any] = None
    others: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        payload: Dict[str, Any] = {
            "tool_name": self.tool_name,
            "tool_use_id": self.tool_use_id,
            "tool_input": self.tool_input,
        }
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookPreToolUseInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookPreToolUseInputBody()
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
    if obj:
        inst.others = dict(obj)
    return head, inst


# PreToolUse and PermissionRequest support systemMessage, 
# but continue, stopReason, and suppressOutput aren't currently supported for those events. 
# If a PreToolUse hook returns one of those unsupported fields, Codex marks that hook run as failed, 
# reports the error, and continues the tool call.
# 阻止工具调用
#{
#  "hookSpecificOutput": {
#    "hookEventName": "PreToolUse",
#    "permissionDecision": "deny",
#    "permissionDecisionReason": "阻止原因"
#  }
#}
# 添加上下文但不阻止
#{
#  "hookSpecificOutput": {
#    "hookEventName": "PreToolUse",
#    "additionalContext": "模型可见的提示信息"
#  }
#}
# 重写工具调用（不阻止）
#{
#  "hookSpecificOutput": {
#    "hookEventName": "PreToolUse",
#    "permissionDecision": "allow",
#    "updatedInput": { "command": "echo rewritten" }
#  }
#}
def build_hook_response() -> str:
    return json.dumps({}, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    head, body = get_hook_input_body()
    with open(c.get_hook_project_log_path(head.date_string()), "a", encoding="utf-8") as log_file:
        log_file.write(
            f"{head.to_log_prefix()}"
            f"{body.to_string()}\n"
        )
    sys.stdout.write(build_hook_response())
