#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, Dict, Optional

import r2u_hook_common as c

_LOG_MASK_KEYS = frozenset({"last_assistant_message"})


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
# stop_hook_active	boolean	Whether this turn was already continued by Stop
# last_assistant_message	string | null	Latest assistant message text, if available
@dataclass
class R2eHookStopInputBody:
    stop_hook_active: bool = False
    last_assistant_message: Optional[str] = None
    others: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        payload: Dict[str, Any] = {
            "stop_hook_active": self.stop_hook_active,
            "last_assistant_message": self.last_assistant_message,
        }
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookStopInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookStopInputBody()
    hv = head.is_valid_Json
    if not str(body_str).strip():
        return head, inst
    if not hv:
        inst.stop_hook_active = c.fallback_bool(body_str, "stop_hook_active") or False
        inst.last_assistant_message = c.fallback_quoted(body_str, "last_assistant_message")
        inst.others = c.invalid_others()
        return head, inst
    try:
        obj = json.loads(body_str)
        if not isinstance(obj, dict):
            raise ValueError("not object")
    except Exception:
        inst.others = c.invalid_others()
        return head, inst

    if "stop_hook_active" in obj:
        inst.stop_hook_active = bool(obj.pop("stop_hook_active"))
    if "last_assistant_message" in obj:
        v = obj.pop("last_assistant_message")
        inst.last_assistant_message = str(v) if v is not None else None
    if obj:
        inst.others = dict(obj)
    return head, inst


# Field	Effect
# continue	If false, marks that hook run as stopped
# stopReason	Recorded as the reason for stopping
# systemMessage	Surfaced as a warning in the UI or event stream
# suppressOutput	Parsed today but not yet implemented

# 阻止 agent 停止（即继续运行）
#{
#  "decision": "block",
#  "reason": "Run one more pass over the failing tests."
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

