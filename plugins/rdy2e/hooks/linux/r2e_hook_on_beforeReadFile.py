#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, Dict, Optional

import r2e_hook_common as c

_LOG_MASK_KEYS = frozenset({"content"})


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
# {
#   "file_path": "<absolute path>",
#   "content": "<file contents>",
#   "attachments": [
#     {
#       "type": "file" | "rule",
#       "file_path": "<absolute path>"
#     }
#   ]
# }
# 输入字段	类型	描述
# session_id	string(opt)	此会话唯一标识，常与 conversation_id 相同
# file_path	string	将要读取的文件的绝对路径
# content	string	文件的完整内容
# attachments	array	与提示关联的上下文附件。每个条目都包含一个 type ("file" 或 "rule") 和一个 file_path。
@dataclass
class R2eHookBeforeReadFileInputBody:
    file_path: Optional[Any] = None
    attachments: list[Any] = field(default_factory=list)
    content: Optional[Any] = None
    others: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        payload: Dict[str, Any] = {}
        if self.file_path is not None:
            payload["file_path"] = self.file_path
        if self.attachments is not None:
            payload["attachments"] = self.attachments
        if self.content is not None:
            payload["content"] = self.content
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(_mask_tree_for_log(payload), ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookBeforeReadFileInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookBeforeReadFileInputBody()
    while True:
        hv = head.is_valid_Json
        empty = {"file_path": None, "content": None, "attachments": []}
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
            "file_path": c.fallback_quoted(body_str, "file_path"),
            "content": c.fallback_quoted(body_str, "content"),
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
        if "file_path" in obj:
            v = obj.pop("file_path")
            out["file_path"] = str(v) if v is not None else None
        if "content" in obj:
            v = obj.pop("content")
            out["content"] = str(v) if v is not None else None
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
# permission	string	"allow" 表示继续，"deny" 表示阻止
# user_message	string (optional)	被拒绝时向用户显示的消息
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
