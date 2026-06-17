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
# session_id	string	此会话的唯一标识符 (与 conversation_id 相同)
# is_background_agent	boolean	该会话是后台 agent 会话还是交互式会话
# composer_mode	string (optional)	composer 启动时的模式 (例如 "agent"、"ask"、"edit")
@dataclass
class R2eHookSessionStartInputBody:
    is_background_agent: bool = False
    composer_mode: Optional[Any] = None
    others: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        payload: Dict[str, Any] = {
            "is_background_agent": self.is_background_agent,
            "composer_mode": self.composer_mode,
        }
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookSessionStartInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookSessionStartInputBody()
    hv = head.is_valid_Json
    if not str(body_str).strip():
        return head, inst
    if not hv:
        ib = c.fallback_bool(body_str, "is_background_agent")
        if ib is not None:
            inst.is_background_agent = ib
        inst.composer_mode = c.fallback_quoted(body_str, "composer_mode")
        inst.others = c.invalid_others()
        return head, inst
    try:
        obj = json.loads(body_str)
        if not isinstance(obj, dict):
            raise ValueError("body not object")
    except Exception:
        inst.others = c.invalid_others()
        return head, inst

    if "session_id" in obj:
        obj.pop("session_id")
    if "is_background_agent" in obj:
        inst.is_background_agent = bool(obj.pop("is_background_agent"))
    if "composer_mode" in obj:
        v = obj.pop("composer_mode")
        inst.composer_mode = v if isinstance(v, str) else v
    if obj:
        inst.others = dict(obj)
    return head, inst


# 输出字段	类型	描述
# env	object (optional)	为此会话设置的环境变量。对后续所有 hook 的执行均可用
# additional_context	string (optional)	要添加到对话初始系统上下文中的额外上下文
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
