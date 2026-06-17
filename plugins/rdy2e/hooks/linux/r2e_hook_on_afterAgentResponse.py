#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
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
# input_tokens / output_tokens / cache_*：Cursor 可能在正文或 others 中附带用量统计。
# {
#   "text": "<assistant final text>"
# }
@dataclass
class R2eHookAfterAgentResponseInputBody:
    session_id: Optional[str] = None
    text: Optional[str] = None
    output_tokens: int = 0
    input_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    others: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        payload: Dict[str, Any] = {
            "output_tokens": self.output_tokens,
            "input_tokens": self.input_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
        }
        if self.text is not None:
            payload = {"text": self.text, **payload}
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookAfterAgentResponseInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookAfterAgentResponseInputBody()
    if not str(body_str).strip():
        return head, inst

    if not head.is_valid_Json:
        inst.session_id = c.fallback_quoted(body_str, "session_id")
        inst.text = c.fallback_quoted(body_str, "text")
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
        v = obj.pop("session_id")
        inst.session_id = str(v) if v is not None else None
    if "text" in obj:
        v = obj.pop("text")
        inst.text = str(v) if v is not None else None

    _TOKEN_FIELDS = ("output_tokens", "input_tokens", "cache_read_tokens", "cache_write_tokens")
    oth = obj.pop("others", None)
    if isinstance(oth, dict):
        rem = dict(oth)
        for tf in _TOKEN_FIELDS:
            if tf in rem:
                try:
                    setattr(inst, tf, int(rem.pop(tf)))
                except (TypeError, ValueError):
                    rem.pop(tf, None)
        if rem:
            inst.others.update(rem)
    for tf in _TOKEN_FIELDS:
        if tf in obj:
            try:
                setattr(inst, tf, int(obj.pop(tf)))
            except (TypeError, ValueError):
                obj.pop(tf, None)
    if obj:
        inst.others.update(dict(obj))
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
