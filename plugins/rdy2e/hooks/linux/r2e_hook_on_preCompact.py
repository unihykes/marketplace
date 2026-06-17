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
# session_id	string(opt)	此会话唯一标识，常与 conversation_id 相同
# trigger	string	触发压缩的方式："auto" 或 "manual"
# context_usage_percent	number	当前上下文窗口的使用百分比 (0-100)
# context_tokens	number	当前上下文窗口中的 token 数
# context_window_size	number	最大上下文窗口大小 (按 token 计)
# message_count	number	会话中的消息数量
# messages_to_compact	number	将要被汇总的消息数量
# is_first_compaction	boolean	此会话是否为首次执行压缩
@dataclass
class R2eHookPreCompactInputBody:
    others: Dict[str, Any] = field(default_factory=dict)
    context_tokens: Optional[Any] = None
    context_usage_percent: Optional[Any] = None
    context_window_size: Optional[Any] = None
    is_first_compaction: Optional[Any] = None
    message_count: Optional[Any] = None
    messages_to_compact: Optional[Any] = None
    trigger: Optional[Any] = None

    def to_string(self) -> str:
        payload: Dict[str, Any] = {}
        if self.context_tokens is not None:
            payload["context_tokens"] = self.context_tokens
        if self.context_usage_percent is not None:
            payload["context_usage_percent"] = self.context_usage_percent
        if self.context_window_size is not None:
            payload["context_window_size"] = self.context_window_size
        if self.is_first_compaction is not None:
            payload["is_first_compaction"] = self.is_first_compaction
        if self.message_count is not None:
            payload["message_count"] = self.message_count
        if self.messages_to_compact is not None:
            payload["messages_to_compact"] = self.messages_to_compact
        if self.trigger is not None:
            payload["trigger"] = self.trigger
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookPreCompactInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookPreCompactInputBody()
    while True:
        hv = head.is_valid_Json
        empty = {
            "trigger": None,
            "context_usage_percent": 0.0,
            "context_tokens": 0,
            "context_window_size": 0,
            "message_count": 0,
            "messages_to_compact": 0,
            "is_first_compaction": False,
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
            ib = c.fallback_bool(body_str, "is_first_compaction")
            out = {
            "trigger": c.fallback_quoted(body_str, "trigger"),
            "context_usage_percent": c.fallback_double(body_str, "context_usage_percent") or 0.0,
            "context_tokens": c.fallback_long(body_str, "context_tokens") or 0,
            "context_window_size": c.fallback_long(body_str, "context_window_size") or 0,
            "message_count": c.fallback_long(body_str, "message_count") or 0,
            "messages_to_compact": c.fallback_long(body_str, "messages_to_compact") or 0,
            "is_first_compaction": ib if ib is not None else False,
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
            out = {**empty, "others": c.invalid_others()}
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
        if "trigger" in obj:
            v = obj.pop("trigger")
            out["trigger"] = str(v) if v is not None else None
        if "context_usage_percent" in obj:
            try:
                out["context_usage_percent"] = float(obj.pop("context_usage_percent"))
            except (TypeError, ValueError):
                obj.pop("context_usage_percent", None)
        for k in ("context_tokens", "context_window_size"):
            if k in obj:
                try:
                    out[k] = int(obj.pop(k))
                except (TypeError, ValueError):
                    obj.pop(k, None)
        for k in ("message_count", "messages_to_compact"):
            if k in obj:
                try:
                    out[k] = int(obj.pop(k))
                except (TypeError, ValueError):
                    obj.pop(k, None)
        if "is_first_compaction" in obj:
            out["is_first_compaction"] = bool(obj.pop("is_first_compaction"))
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
# user_message	string (optional)	发生压缩时展示给用户的消息
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
