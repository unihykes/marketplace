#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, Dict, Optional

import r2u_hook_common as c


# Field	Type	Meaning
# turn_id	string	Codex-specific extension. Active Codex turn id
# agent_id	string	Identifier for the subagent
# agent_type	string	Subagent type or profile
# permission_mode	string	Current permission mode
# 备注: turn_id 和 permission_mode 已在 R2eHookInputHead 中解析
@dataclass
class R2eHookSubagentStartInputBody:
    agent_id: Optional[str] = None
    agent_type: Optional[str] = None
    others: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        payload: Dict[str, Any] = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
        }
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(payload, ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookSubagentStartInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookSubagentStartInputBody()
    hv = head.is_valid_Json
    if not str(body_str).strip():
        return head, inst
    if not hv:
        inst.agent_id = c.fallback_quoted(body_str, "agent_id")
        inst.agent_type = c.fallback_quoted(body_str, "agent_type")
        inst.others = c.invalid_others()
        return head, inst
    try:
        obj = json.loads(body_str)
        if not isinstance(obj, dict):
            raise ValueError("body not object")
    except Exception:
        inst.others = c.invalid_others()
        return head, inst

    if "agent_id" in obj:
        inst.agent_id = obj.pop("agent_id")
    if "agent_type" in obj:
        inst.agent_type = obj.pop("agent_type")
    if obj:
        inst.others = dict(obj)
    return head, inst


# Field	Effect
# continue	If false, marks that hook run as stopped
# stopReason	Recorded as the reason for stopping
# systemMessage	Surfaced as a warning in the UI or event stream
# suppressOutput	Parsed today but not yet implemented
# 
# {
#  "hookSpecificOutput": {
#    "hookEventName": "SubagentStart",
#    "additionalContext": "Review the repository test conventions first."
#  }
#}
def build_hook_response() -> str:
    return json.dumps({
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "SubagentStart",
            "additionalContext": ""
        }
    }, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    head, body = get_hook_input_body()
    with open(c.get_hook_project_log_path(head.date_string()), "a", encoding="utf-8", errors="replace") as log_file:
        log_file.write(
            f"{head.to_log_prefix()}"
            f"{body.to_string()}\n"
        )
    sys.stdout.write(build_hook_response())

