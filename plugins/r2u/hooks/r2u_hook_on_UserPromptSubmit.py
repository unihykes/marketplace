#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, Dict, Optional

import r2u_hook_common as c

_LOG_MASK_KEYS = frozenset({"prompt"})


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
# prompt	string	User prompt that's about to be sent
# 备注: turn_id 已在 R2eHookInputHead 中解析
@dataclass
class R2eHookBeforeSubmitPromptInputBody:
    prompt: Optional[str] = None
    others: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        payload: Dict[str, Any] = {
            "prompt": self.prompt,
        }
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookBeforeSubmitPromptInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookBeforeSubmitPromptInputBody()
    hv = head.is_valid_Json
    if not str(body_str).strip():
        return head, inst
    if not hv:
        inst.prompt = c.fallback_quoted(body_str, "prompt")
        inst.others = c.invalid_others()
        return head, inst
    try:
        obj = json.loads(body_str)
        if not isinstance(obj, dict):
            raise ValueError("body not object")
    except Exception:
        inst.others = c.invalid_others()
        return head, inst

    if "prompt" in obj:
        inst.prompt = obj.pop("prompt")
    if obj:
        inst.others = dict(obj)
    return head, inst


# Field	Effect
# continue	If false, marks that hook run as stopped
# stopReason	Recorded as the reason for stopping
# systemMessage	Surfaced as a warning in the UI or event stream
# suppressOutput	Parsed today but not yet implemented

# 添加额外上下文
#{
#  "hookSpecificOutput": {
#    "hookEventName": "UserPromptSubmit",
#    "additionalContext": "Ask for a clearer reproduction before editing files."
#  }
#}
# # 拒绝
#{
#  "decision": "block",
#  "reason": "Ask for confirmation before doing that."
#}
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
