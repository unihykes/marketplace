#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, Dict, Optional

import r2e_hook_common as c

_LOG_MASK_KEYS = frozenset({
    "prompt", "text", "content",
    "output", "pattern", "task",
    "old_string", "new_string", "context",
})


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


# beforeMCPExecution 输入
# session_id（可选）：此会话唯一标识，常与 conversation_id 相同。
# {
#   "tool_name": "<tool name>",
#   "tool_input": "<json params>"
# }
# 加上以下之一：
# { "url": "<server url>" }
# 或：
# { "command": "<command string>" }
@dataclass
class R2eHookBeforeMCPExecutionInputBody:
    command: Optional[Any] = None
    tool_name: Optional[Any] = None
    tool_input: Optional[Any] = None
    others: Dict[str, Any] = field(default_factory=dict)
    url: Optional[Any] = None

    def to_string(self) -> str:
        payload: Dict[str, Any] = {}
        if self.command is not None:
            payload["command"] = self.command
        if self.tool_input is not None:
            payload["tool_input"] = self.tool_input
        if self.url is not None:
            payload["url"] = self.url
        if self.others:
            payload["others"] = self.others
        body = json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)
        if self.tool_name is not None and str(self.tool_name).strip():
            return f"[{self.tool_name}]\n{body}"
        return f"\n{body}"


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookBeforeMCPExecutionInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookBeforeMCPExecutionInputBody()
    while True:
        hv = head.is_valid_Json
        empty = {"tool_name": None, "tool_input": {}, "url": None, "command": None}
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
            "tool_name": c.fallback_quoted(body_str, "tool_name"),
            "tool_input": {},
            "url": c.fallback_quoted(body_str, "url"),
            "command": c.fallback_quoted(body_str, "command"),
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
            out = {"tool_input": {}, "others": c.invalid_others()}
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
        if "tool_name" in obj:
            v = obj.pop("tool_name")
            out["tool_name"] = str(v) if v is not None else None
        if "tool_input" in obj:
            out["tool_input"] = obj.pop("tool_input")
        if "url" in obj:
            v = obj.pop("url")
            out["url"] = str(v) if v is not None else None
        if "command" in obj:
            v = obj.pop("command")
            out["command"] = str(v) if v is not None else None
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

# 输出
# {
#   "permission": "allow" | "deny" | "ask",
#   "user_message": "<message shown in client>",
#   "agent_message": "<message sent to agent>"
# }
def build_hook_response() -> str:
    return json.dumps({"permission": "allow"}, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    head, body = get_hook_input_body()
    with open(c.get_hook_project_log_path(head.date_string()), "a", encoding="utf-8") as log_file:
        log_file.write(
            f"{head.to_log_prefix()}"
            f"{body.to_string()}\n"
        )
    sys.stdout.write(build_hook_response())
