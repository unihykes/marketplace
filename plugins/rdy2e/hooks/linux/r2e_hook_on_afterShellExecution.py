#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, Dict, Optional

import r2e_hook_common as c

_LOG_MASK_KEYS = frozenset({"output"})


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


# Field	Type	Description
# session_id	string (opt)	此会话唯一标识，常与 conversation_id 相同；Cursor 可能在 body 中附带
# command	string	执行的完整终端命令
# output	string	从终端捕获的完整输出
# duration	number	执行该 shell 命令所花费的时间（毫秒），不包括等待审批的时间
# sandbox	boolean	该命令是否在沙盒环境中运行
@dataclass
class R2eHookAfterShellExecutionInputBody:
    command: Optional[Any] = None
    sandbox: bool = False
    duration: Optional[Any] = None
    others: Dict[str, Any] = field(default_factory=dict)
    output: Optional[Any] = None

    def to_string(self) -> str:
        payload: Dict[str, Any] = {}
        if self.command is not None:
            payload["command"] = self.command
        if self.sandbox is not None:
            payload["sandbox"] = self.sandbox
        if self.duration is not None:
            payload["duration"] = self.duration
        if self.output is not None:
            payload["output"] = self.output
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookAfterShellExecutionInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookAfterShellExecutionInputBody()
    while True:
        hv = head.is_valid_Json
        empty = {"command": None, "output": None, "duration": 0, "sandbox": False}
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
            "command": c.fallback_quoted(body_str, "command"),
            "output": c.fallback_quoted(body_str, "output"),
            "duration": c.fallback_long(body_str, "duration") or 0,
            "sandbox": c.fallback_bool(body_str, "sandbox") or False,
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
            out = {"duration": 0, "sandbox": False, "others": c.invalid_others()}
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
        if "command" in obj:
            v = obj.pop("command")
            out["command"] = str(v) if v is not None else None
        if "output" in obj:
            v = obj.pop("output")
            out["output"] = str(v) if v is not None else None
        if "duration" in obj:
            try:
                out["duration"] = int(obj.pop("duration"))
            except (TypeError, ValueError):
                obj.pop("duration", None)
        if "sandbox" in obj:
            out["sandbox"] = bool(obj.pop("sandbox"))
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
