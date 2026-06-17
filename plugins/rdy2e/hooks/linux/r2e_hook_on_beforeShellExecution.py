#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import sys
from typing import Any, Dict, Optional

import r2e_hook_common as c

_LOG_MASK_KEYS: frozenset[str] = frozenset()


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


# beforeShellExecution 输入
# session_id（可选）：此会话唯一标识，常与 conversation_id 相同；Cursor 可能在 body 中附带。
# {
#   "command": "<full terminal command>",
#   "cwd": "<current working directory>",
#   "sandbox": false
# }
@dataclass
class R2eHookBeforeShellExecutionInputBody:
    cwd: Optional[str] = None
    command: Optional[str] = None
    sandbox: bool = False
    others: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        payload: Dict[str, Any] = {
            "cwd": self.cwd,
            "command": self.command,
            "sandbox": self.sandbox,
        }
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookBeforeShellExecutionInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookBeforeShellExecutionInputBody()
    hv = head.is_valid_Json
    if not str(body_str).strip():
        return head, inst
    if not hv:
        inst.command = c.fallback_quoted(body_str, "command")
        inst.cwd = c.fallback_quoted(body_str, "cwd")
        inst.sandbox = c.fallback_bool(body_str, "sandbox") or False
        inst.others = c.invalid_others()
        return head, inst
    try:
        obj = json.loads(body_str)
        if not isinstance(obj, dict):
            raise ValueError("not object")
    except Exception:
        inst.sandbox = False
        inst.others = c.invalid_others()
        return head, inst

    if "session_id" in obj:
        obj.pop("session_id")
    if "command" in obj:
        v = obj.pop("command")
        inst.command = str(v) if v is not None else None
    if "cwd" in obj:
        v = obj.pop("cwd")
        inst.cwd = str(v) if v is not None else None
    if "sandbox" in obj:
        inst.sandbox = bool(obj.pop("sandbox"))
    if obj:
        inst.others = dict(obj)
    return head, inst


# 输出
# {
#   "permission": "allow" | "deny" | "ask",
#   "user_message": "<message shown in client>",
#   "agent_message": "<message sent to agent>"
# }
def build_hook_response() -> str:
    return json.dumps({"permission": "allow"}, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    head, body = get_hook_input_body()
    with open(c.get_hook_project_log_path(head.date_string()), "a", encoding="utf-8") as log_file:
        log_file.write(
            f"{head.to_log_prefix()}"
            f"{body.to_string()}\n"
        )
    sys.stdout.write(build_hook_response())
