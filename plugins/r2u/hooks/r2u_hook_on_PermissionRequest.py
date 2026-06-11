#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, Dict

import r2u_hook_common as c

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


# TODO: 待补充 PermissionRequest 的输入字段定
@dataclass
class R2eHookPermissionRequestInputBody:
    others: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        return "\n" + json.dumps(_mask_tree_for_log(self.others), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookPermissionRequestInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookPermissionRequestInputBody()
    hv = head.is_valid_Json
    if not str(body_str).strip():
        return head, inst
    if not hv:
        inst.others = c.invalid_others()
        return head, inst
    try:
        obj = json.loads(body_str)
        if not isinstance(obj, dict):
            raise ValueError("body not object")
    except Exception:
        inst.others = c.invalid_others()
        return head, inst

    # TODO: ´ý²¹³ä¾ßÌå×Ö¶Î½âÎö
    if obj:
        inst.others = dict(obj)
    return head, inst


# PreToolUse and PermissionRequest support systemMessage, 
# but continue, stopReason, and suppressOutput aren’t currently supported for those events. 
# If a PreToolUse hook returns one of those unsupported fields, Codex marks that hook run as failed, 
# reports the error, and continues the tool call.
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
