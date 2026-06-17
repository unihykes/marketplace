#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, Dict, Optional

import r2e_hook_common as c

_LOG_MASK_KEYS = frozenset({"text"})


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
#   "text": "<fully aggregated thinking text>",
#   "duration_ms": 5000
# }
@dataclass
class R2eHookAfterAgentThoughtInputBody:
    duration_ms: int = 0
    text: Optional[Any] = None
    others: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        payload: Dict[str, Any] = {}
        if self.duration_ms is not None:
            payload["duration_ms"] = self.duration_ms
        if self.text is not None:
            payload["text"] = self.text
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookAfterAgentThoughtInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookAfterAgentThoughtInputBody()
    while True:
        hv = head.is_valid_Json
        empty = {"text": None, "duration_ms": 0}
        if not str(body_str).strip():
            out = empty
            if isinstance(out, dict):
                for k, v in out.items():
                    if hasattr(inst, k):
                        setattr(inst, k, v)
                    else:
                        inst.others[k] = v
            else:
                inst.others = {"_value": out}
            break
        if not hv:
            out = {
            "text": c.fallback_quoted(body_str, "text"),
            "duration_ms": c.fallback_long(body_str, "duration_ms") or 0,
            "others": c.invalid_others(),
        }
            if isinstance(out, dict):
                for k, v in out.items():
                    if hasattr(inst, k):
                        setattr(inst, k, v)
                    else:
                        inst.others[k] = v
            else:
                inst.others = {"_value": out}
            break
        try:
            obj = json.loads(body_str)
            if not isinstance(obj, dict):
                raise ValueError("not object")
        except Exception:
            out = {"duration_ms": 0, "others": c.invalid_others()}
            if isinstance(out, dict):
                for k, v in out.items():
                    if hasattr(inst, k):
                        setattr(inst, k, v)
                    else:
                        inst.others[k] = v
            else:
                inst.others = {"_value": out}
            break
        others: Dict[str, Any] = {}
        out = dict(empty)
        if "session_id" in obj:
            obj.pop("session_id")
        if "text" in obj:
            v = obj.pop("text")
            out["text"] = str(v) if v is not None else None
        if "duration_ms" in obj:
            try:
                out["duration_ms"] = int(obj.pop("duration_ms"))
            except (TypeError, ValueError):
                obj.pop("duration_ms", None)
        for k, v in obj.items():
            others[k] = v
        if others:
            out["others"] = others
        out = out
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
