#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, Dict, Optional

import r2e_hook_common as c

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


# 输入字段	类型	描述	
# session_id	string(opt)	此会话唯一标识，常与 conversation_id 相同
# subagent_type	string	subagent 的类型：generalPurpose、explore、shell 等。	
# status	string	"completed"、"error" 或 "aborted"	
# task	string	提供给 subagent 的任务描述	
# description	string	对 subagent 目的的简要描述	
# summary	string	subagent 的输出摘要	
# duration_ms	number	执行时间 (毫秒)	
# message_count	number	subagent 会话期间交换的消息数量	
# tool_call_count	number	subagent 发起的工具调用次数	
# loop_count	number	此 subagent 已触发 subagentStop 后续操作的次数 (从 0 开始)	
# modified_files	string[]	subagent 修改过的文件	
# agent_transcript_path	string	null	subagent 自身会话记录文件的路径 (与父对话分开)
@dataclass
class R2eHookSubagentStopInputBody:
    status: Optional[Any] = None
    loop_count: int = 0
    duration_ms: int = 0
    subagent_type: Optional[Any] = None
    others: Dict[str, Any] = field(default_factory=dict)
    agent_transcript_path: Optional[Any] = None
    description: Optional[Any] = None
    message_count: Optional[Any] = None
    modified_files: Optional[Any] = None
    summary: Optional[Any] = None
    task: Optional[Any] = None
    tool_call_count: Optional[Any] = None

    def to_string(self) -> str:
        payload: Dict[str, Any] = {}
        if self.status is not None:
            payload["status"] = self.status
        if self.loop_count is not None:
            payload["loop_count"] = self.loop_count
        if self.duration_ms is not None:
            payload["duration_ms"] = self.duration_ms
        if self.subagent_type is not None:
            payload["subagent_type"] = self.subagent_type
        if self.agent_transcript_path is not None:
            payload["agent_transcript_path"] = self.agent_transcript_path
        if self.description is not None:
            payload["description"] = self.description
        if self.message_count is not None:
            payload["message_count"] = self.message_count
        if self.modified_files is not None:
            payload["modified_files"] = self.modified_files
        if self.summary is not None:
            payload["summary"] = self.summary
        if self.task is not None:
            payload["task"] = self.task
        if self.tool_call_count is not None:
            payload["tool_call_count"] = self.tool_call_count
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookSubagentStopInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookSubagentStopInputBody()
    while True:
        hv = head.is_valid_Json
        empty = {
            "subagent_type": None,
            "status": None,
            "task": None,
            "description": None,
            "summary": None,
            "duration_ms": 0,
            "message_count": 0,
            "tool_call_count": 0,
            "loop_count": 0,
            "modified_files": [],
            "agent_transcript_path": None,
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
            "subagent_type": c.fallback_quoted(body_str, "subagent_type"),
            "status": c.fallback_quoted(body_str, "status"),
            "task": c.fallback_quoted(body_str, "task"),
            "description": c.fallback_quoted(body_str, "description"),
            "summary": c.fallback_quoted(body_str, "summary"),
            "duration_ms": c.fallback_long(body_str, "duration_ms") or 0,
            "message_count": c.fallback_long(body_str, "message_count") or 0,
            "tool_call_count": c.fallback_long(body_str, "tool_call_count") or 0,
            "loop_count": c.fallback_long(body_str, "loop_count") or 0,
            "modified_files": [],
            "agent_transcript_path": c.fallback_quoted(body_str, "agent_transcript_path"),
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
        for k in ("subagent_type", "status", "description", "summary", "agent_transcript_path"):
            if k in obj:
                v = obj.pop(k)
                out[k] = str(v) if v is not None else None
        if "task" in obj:
            v = obj.pop("task")
            out["task"] = str(v) if v is not None else None
        for k in ("duration_ms", "message_count", "tool_call_count", "loop_count"):
            if k in obj:
                try:
                    out[k] = int(obj.pop(k))
                except (TypeError, ValueError):
                    obj.pop(k, None)
        if "modified_files" in obj:
            mf = obj.pop("modified_files")
            if isinstance(mf, list):
                out["modified_files"] = [str(x) for x in mf]
            elif isinstance(mf, str):
                out["modified_files"] = [mf]
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
# followup_message	string (optional)	使用此消息自动继续。仅当 status 为 "completed" 时才会被处理。
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
