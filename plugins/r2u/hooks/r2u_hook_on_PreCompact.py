#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, Dict, Optional

import r2u_hook_common as c


# Field	Type	Meaning
# turn_id	string	Codex-specific extension. Active Codex turn id
# trigger	string	What triggered compaction: manual or auto
# 备注: turn_id 已在 R2eHookInputHead 中解析
@dataclass
class R2eHookPreCompactInputBody:
    trigger: Optional[str] = None
    others: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        payload: Dict[str, Any] = {
            "trigger": self.trigger,
        }
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(payload, ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookPreCompactInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookPreCompactInputBody()
    hv = head.is_valid_Json
    if not str(body_str).strip():
        return head, inst
    if not hv:
        inst.trigger = c.fallback_quoted(body_str, "trigger")
        inst.others = c.invalid_others()
        return head, inst
    try:
        obj = json.loads(body_str)
        if not isinstance(obj, dict):
            raise ValueError("body not object")
    except Exception:
        inst.others = c.invalid_others()
        return head, inst

    if "trigger" in obj:
        inst.trigger = obj.pop("trigger")
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
    response = build_hook_response()
    with open(c.get_hook_project_log_path(head.date_string()), "a", encoding="utf-8", errors="replace") as log_file:
        log_file.write(
            f"{head.to_log_prefix()}"
            f"{body.to_string()}\n"
            f"{response}\n"
        )
    c.write_stdout_utf8(response)

