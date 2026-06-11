#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, Dict, Optional

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


# Input
# session_id（可选）：此会话唯一标识，常与 conversation_id 相同。
# output_tokens / input_tokens / cache_*：Cursor 可能在 stop 载荷中附带用量统计。
# {
#   "status": "completed" | "aborted" | "error",
#   "loop_count": 0
# }
@dataclass
class R2eHookStopInputBody:
    status: Optional[str] = None
    loop_count: int = 0
    output_tokens: int = 0
    input_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    others: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        payload: Dict[str, Any] = {
            "status": self.status,
            "loop_count": self.loop_count,
            "output_tokens": self.output_tokens,
            "input_tokens": self.input_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
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
        inst.status = c.fallback_quoted(body_str, "status")
        inst.loop_count = c.fallback_long(body_str, "loop_count") or 0
        inst.output_tokens = c.fallback_long(body_str, "output_tokens") or 0
        inst.input_tokens = c.fallback_long(body_str, "input_tokens") or 0
        inst.cache_read_tokens = c.fallback_long(body_str, "cache_read_tokens") or 0
        inst.cache_write_tokens = c.fallback_long(body_str, "cache_write_tokens") or 0
        inst.others = c.invalid_others()
        return head, inst
    try:
        obj = json.loads(body_str)
        if not isinstance(obj, dict):
            raise ValueError("not object")
    except Exception:
        inst.others = c.invalid_others()
        return head, inst

    if "session_id" in obj:
        obj.pop("session_id")
    if "status" in obj:
        v = obj.pop("status")
        inst.status = str(v) if v is not None else None
    if "loop_count" in obj:
        try:
            inst.loop_count = int(obj.pop("loop_count"))
        except (TypeError, ValueError):
            obj.pop("loop_count", None)
    for tf in ("output_tokens", "input_tokens", "cache_read_tokens", "cache_write_tokens"):
        if tf in obj:
            try:
                setattr(inst, tf, int(obj.pop(tf)))
            except (TypeError, ValueError):
                obj.pop(tf, None)
    if obj:
        inst.others = dict(obj)
    return head, inst


# Field	Effect
# continue	If false, marks that hook run as stopped
# stopReason	Recorded as the reason for stopping
# systemMessage	Surfaced as a warning in the UI or event stream
# suppressOutput	Parsed today but not yet implemented
def build_hook_response() -> str:
    return json.dumps({"continue": True}, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    head, body = get_hook_input_body()
    with open(c.get_hook_project_log_path(head.date_string()), "a", encoding="utf-8") as log_file:
        log_file.write(
            f"{head.to_log_prefix()}"
            f"{body.to_string()}\n"
        )
    sys.stdout.write(build_hook_response())
