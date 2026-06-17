#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, Dict, Optional

import r2e_hook_common as c
from r2e_hook_on_afterFileEdit import parse_after_file_edit

_LOG_MASK_KEYS = frozenset({"old_string", "new_string"})


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


# 输入
# session_id（可选）：此会话唯一标识，常与 conversation_id 相同。
# {
#   "file_path": "<absolute path>",
#   "edits": [
#     {
#       "old_string": "<search>",
#       "new_string": "<replace>",
#       "range": {
#         "start_line_number": 10,
#         "start_column": 5,
#         "end_line_number": 10,
#         "end_column": 20
#       },
#       "old_line": "<line before edit>",
#       "new_line": "<line after edit>"
#     }
#   ]
# }
@dataclass
class R2eHookAfterTabFileEditInputBody:
    others: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        payload: Dict[str, Any] = {}
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookAfterTabFileEditInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookAfterTabFileEditInputBody()
    while True:
        out = parse_after_file_edit(head, body_str)
        if isinstance(out, dict):
            for k, v in out.items():
                if hasattr(inst, k):
                    setattr(inst, k, v)
                else:
                    inst.others[k] = v
        else:
            inst.others = {"_value": out}
        break
    return head, inst


#  No output fields currently supported
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
