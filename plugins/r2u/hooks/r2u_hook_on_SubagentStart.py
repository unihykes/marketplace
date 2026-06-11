#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, Dict, Optional

import r2u_hook_common as c

_LOG_MASK_KEYS = frozenset({"task"})


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



# 输入字段                类型        描述
# session_id              string(opt) 此会话唯一标识，常与 conversation_id 相同
# subagent_id             string      此子代理实例的唯一标识符
# subagent_type           string      子代理类型：generalPurpose、explore、shell 等
# task                    string      分配给子代理的任务描述
# parent_conversation_id  string      父级代理会话的对话 ID
# tool_call_id            string      触发该子代理的工具调用 ID
# subagent_model          string      子代理将使用的模型
# is_parallel_worker      boolean     此子代理是否作为并行工作线程运行
# git_branch              string(opt) 子代理要操作的 Git 分支（如适用）
@dataclass
class R2eHookSubagentStartInputBody:
    subagent_type: Optional[Any] = None
    others: Dict[str, Any] = field(default_factory=dict)
    git_branch: Optional[Any] = None
    is_parallel_worker: Optional[Any] = None
    parent_conversation_id: Optional[Any] = None
    subagent_id: Optional[Any] = None
    subagent_model: Optional[Any] = None
    task: Optional[Any] = None
    tool_call_id: Optional[Any] = None

    def to_string(self) -> str:
        payload: Dict[str, Any] = {}
        if self.subagent_type is not None:
            payload["subagent_type"] = self.subagent_type
        if self.git_branch is not None:
            payload["git_branch"] = self.git_branch
        if self.is_parallel_worker is not None:
            payload["is_parallel_worker"] = self.is_parallel_worker
        if self.parent_conversation_id is not None:
            payload["parent_conversation_id"] = self.parent_conversation_id
        if self.subagent_id is not None:
            payload["subagent_id"] = self.subagent_id
        if self.subagent_model is not None:
            payload["subagent_model"] = self.subagent_model
        if self.task is not None:
            payload["task"] = self.task
        if self.tool_call_id is not None:
            payload["tool_call_id"] = self.tool_call_id
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookSubagentStartInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookSubagentStartInputBody()
    while True:
        hv = head.is_valid_Json
        empty = {
            "subagent_id": None,
            "subagent_type": None,
            "task": None,
            "parent_conversation_id": None,
            "tool_call_id": None,
            "subagent_model": None,
            "is_parallel_worker": False,
            "git_branch": None,
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
            ip = c.fallback_bool(body_str, "is_parallel_worker")
            out = {
            "subagent_id": c.pretty_uuid(c.fallback_quoted(body_str, "subagent_id") or ""),
            "subagent_type": c.fallback_quoted(body_str, "subagent_type"),
            "task": c.fallback_quoted(body_str, "task"),
            "parent_conversation_id": c.pretty_uuid(c.fallback_quoted(body_str, "parent_conversation_id") or ""),
            "tool_call_id": c.pretty_uuid(c.fallback_quoted(body_str, "tool_call_id") or ""),
            "subagent_model": c.fallback_quoted(body_str, "subagent_model"),
            "is_parallel_worker": ip if ip is not None else False,
            "git_branch": c.fallback_quoted(body_str, "git_branch"),
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
            err = dict(empty)
            err["others"] = c.invalid_others()
            out = err
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
        if "subagent_id" in obj:
            out["subagent_id"] = c.pretty_uuid(str(obj.pop("subagent_id")))
        for k in ("subagent_type", "subagent_model", "git_branch"):
            if k in obj:
                v = obj.pop(k)
                out[k] = str(v) if v is not None else None
        if "task" in obj:
            v = obj.pop("task")
            out["task"] = str(v) if v is not None else None
        if "parent_conversation_id" in obj:
            out["parent_conversation_id"] = c.pretty_uuid(str(obj.pop("parent_conversation_id")))
        if "tool_call_id" in obj:
            out["tool_call_id"] = c.pretty_uuid(str(obj.pop("tool_call_id")))
        if "is_parallel_worker" in obj:
            out["is_parallel_worker"] = bool(obj.pop("is_parallel_worker"))
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
# permission	string	"allow" 表示继续，"deny" 表示阻止。subagentStart 不支持 "ask"，并将其视为 "deny"。
# user_message	string (optional)	子代理被拒绝时向用户显示的消息
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
