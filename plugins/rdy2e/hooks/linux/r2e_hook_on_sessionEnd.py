#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, Dict, Optional

import r2e_hook_common as c

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


# 输入字段	类型	描述
# session_id	string	即将结束的会话的唯一标识符
# reason	string	会话的结束方式："completed"、"aborted"、"error"、"window_close" 或 "user_close"
# duration_ms	number	会话的总持续时间 (毫秒)
# is_background_agent	boolean	该会话是否为后台 agent 会话
# final_status	string	会话的最终状态
# error_message	string (optional)	当 reason 为 "error" 时的错误消息
@dataclass
class R2eHookSessionEndInputBody:
    duration_ms: int = 0
    is_background_agent: bool = False
    others: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[Any] = None
    final_status: Optional[Any] = None
    reason: Optional[Any] = None

    def to_string(self) -> str:
        payload: Dict[str, Any] = {}
        if self.duration_ms is not None:
            payload["duration_ms"] = self.duration_ms
        if self.is_background_agent is not None:
            payload["is_background_agent"] = self.is_background_agent
        if self.error_message is not None:
            payload["error_message"] = self.error_message
        if self.final_status is not None:
            payload["final_status"] = self.final_status
        if self.reason is not None:
            payload["reason"] = self.reason
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookSessionEndInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookSessionEndInputBody()
    while True:
        hv = head.is_valid_Json
        if not str(body_str).strip():
            out = {
            "reason": None,
            "duration_ms": 0,
            "is_background_agent": False,
            "final_status": None,
            "error_message": None,
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
        if not hv:
            d = {
                "reason": c.fallback_quoted(body_str, "reason"),
                "duration_ms": c.fallback_long(body_str, "duration_ms") or 0,
                "is_background_agent": c.fallback_bool(body_str, "is_background_agent"),
                "final_status": c.fallback_quoted(body_str, "final_status"),
                "error_message": c.fallback_quoted(body_str, "error_message"),
                "others": c.invalid_others(),
            }
            if d["is_background_agent"] is None:
                d["is_background_agent"] = False
            out = d
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
            out = {"others": c.invalid_others()}
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
        out = {
            "reason": None,
            "duration_ms": 0,
            "is_background_agent": False,
            "final_status": None,
            "error_message": None,
        }
        if "session_id" in obj:
            obj.pop("session_id")
        if "reason" in obj:
            out["reason"] = str(obj.pop("reason")) if obj["reason"] is not None else None
        if "duration_ms" in obj:
            try:
                out["duration_ms"] = int(obj.pop("duration_ms"))
            except (TypeError, ValueError):
                obj.pop("duration_ms", None)
        if "is_background_agent" in obj:
            out["is_background_agent"] = bool(obj.pop("is_background_agent"))
        if "final_status" in obj:
            v = obj.pop("final_status")
            out["final_status"] = str(v) if v is not None else None
        if "error_message" in obj:
            v = obj.pop("error_message")
            out["error_message"] = str(v) if v is not None else None
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
