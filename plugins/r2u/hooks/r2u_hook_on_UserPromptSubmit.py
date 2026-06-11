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


# 输入
# session_id（可选）：此会话唯一标识，常与 conversation_id 相同。
# composer_mode（可选）：如 agent / ask / edit，与 Cursor 实际载荷一致。
# {
#   "prompt": "<user prompt text>",
#   "attachments": [ ... ]
# }
@dataclass
class R2eHookBeforeSubmitPromptInputBody:
    attachments: list[Any] = field(default_factory=list)
    composer_mode: Optional[Any] = None
    others: Dict[str, Any] = field(default_factory=dict)
    prompt: Optional[Any] = None

    def to_string(self) -> str:
        payload: Dict[str, Any] = {}
        if self.attachments is not None:
            payload["attachments"] = self.attachments
        if self.composer_mode is not None:
            payload["composer_mode"] = self.composer_mode
        if self.prompt is not None:
            payload["prompt"] = self.prompt
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookBeforeSubmitPromptInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookBeforeSubmitPromptInputBody()
    while True:
        hv = head.is_valid_Json
        empty = {"composer_mode": None, "prompt": None, "attachments": []}
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
            "composer_mode": c.fallback_quoted(body_str, "composer_mode"),
            "prompt": c.fallback_quoted(body_str, "prompt"),
            "attachments": [],
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
            out = {"attachments": [], "others": c.invalid_others()}
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
        if "composer_mode" in obj:
            v = obj.pop("composer_mode")
            out["composer_mode"] = str(v) if v is not None else None
        if "prompt" in obj:
            v = obj.pop("prompt")
            out["prompt"] = str(v) if v is not None else None
        if "attachments" in obj:
            out["attachments"] = obj.pop("attachments")
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


# 输出字段	类型	描述
# continue	boolean	是否允许提示词提交继续进行
# user_message	string (optional)	当提示词被阻止时向用户显示的消息
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
