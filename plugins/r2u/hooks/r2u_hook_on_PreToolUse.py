#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, Dict, Optional

import r2u_hook_common as c

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


# 输入字段        类型    描述
# session_id      string  此会话的唯一标识符 (与 conversation_id 相同)
# tool_name       string  即将使用的工具名称
# tool_use_id     string  调用标识
# cwd             string  当前工作目录
# model           string  模型标识
# agent_message   string  agent 侧消息上下文
# tool_input      object  工具调用参数对象
@dataclass
class R2eHookPreToolUseInputBody:
    cwd: Optional[Any] = None
    tool_name: Optional[Any] = None
    tool_input: Optional[Any] = None
    agent_message: Optional[Any] = None
    others: Dict[str, Any] = field(default_factory=dict)
    model: Optional[Any] = None
    tool_use_id: Optional[Any] = None

    def to_string(self) -> str:
        payload: Dict[str, Any] = {}
        if self.cwd is not None:
            payload["cwd"] = self.cwd
        if self.tool_input is not None:
            payload["tool_input"] = self.tool_input
        if self.agent_message is not None:
            payload["agent_message"] = self.agent_message
        if self.model is not None:
            payload["model"] = self.model
        if self.others:
            payload["others"] = self.others
        body = json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)
        prefix = ""
        if self.tool_use_id is not None and str(self.tool_use_id).strip():
            prefix += f"[{self.tool_use_id}]"
        if self.tool_name is not None and str(self.tool_name).strip():
            prefix += f"[{self.tool_name}]"
        if prefix:
            return f"{prefix}\n{body}"
        return f"\n{body}"


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookPreToolUseInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookPreToolUseInputBody()
    while True:
        hv = head.is_valid_Json
        empty = {
            "tool_name": None,
            "tool_use_id": None,
            "cwd": None,
            "model": None,
            "agent_message": None,
            "tool_input": {},
        }
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
            "tool_use_id": c.pretty_uuid(c.fallback_quoted(body_str, "tool_use_id") or ""),
            "cwd": c.fallback_quoted(body_str, "cwd"),
            "model": c.fallback_quoted(body_str, "model"),
            "agent_message": c.fallback_quoted(body_str, "agent_message"),
            "tool_input": {},
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
        for k in ("tool_name", "cwd", "model", "agent_message"):
            if k in obj:
                v = obj.pop(k)
                out[k] = str(v) if v is not None else None
        if "tool_use_id" in obj:
            out["tool_use_id"] = c.pretty_uuid(str(obj.pop("tool_use_id")))
        if "tool_input" in obj:
            out["tool_input"] = obj.pop("tool_input")
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
