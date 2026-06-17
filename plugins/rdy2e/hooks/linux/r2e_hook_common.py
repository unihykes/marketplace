# r2e Linux hooks 公共逻辑

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import AbstractSet, Any, Dict, Optional, Tuple

RUNTIME_DIR = Path(__file__).resolve().parent


def pretty_uuid(id_val: Any) -> str:
    """将 UUID 简写为首段，便于日志展示。"""
    if id_val is None:
        return ""
    s = str(id_val).strip()
    if not s:
        return s
    return s.split("-", 1)[0]


def pretty_string(node: str, prop_name: str, mask_keys: AbstractSet[str]) -> str:
    """对命中 ``mask_keys`` 的字符串做日志友好截断。

    - ``prop_name`` 不在 ``mask_keys`` 中：原样返回。
    - 命中且 UTF-8 字节数不超过 ``limit``：原样返回。
    - 命中且超过 ``limit``：按 UTF-8 安全截断至该长度（``errors='ignore'`` 丢弃尾部
      不完整续字节，避免中文/Emoji 乱码），输出 ``<前缀>...+<剩余字节数>``；其中
      ``剩余 = 总字节 - 实际前缀字节数``，保证 ``前缀字节数 + 剩余 == 总字节数``。
    """
    limit = 128
    if prop_name not in mask_keys:
        return node
    b = node.encode("utf-8")
    if len(b) <= limit:
        return node
    prefix = b[:limit].decode("utf-8", errors="ignore")
    return f"{prefix}...+{len(b) - len(prefix.encode('utf-8'))}"


def repair_missing_closing_quote_after_text(raw: str) -> Optional[str]:
    """尝试修复 text 字段缺少结束引号的常见 JSON 破损。"""
    m = re.search(r'"text"\s*:\s*"', raw)
    if not m:
        return None
    value_start = m.end()
    if value_start >= len(raw):
        return None
    tail = raw[value_start:]
    nx = re.search(r",\s*\"(?:\\.|[^\"\\])*\"\s*:", tail)
    if not nx:
        return None
    comma_rel = nx.start()
    if comma_rel < 1 or tail[comma_rel - 1] == '"':
        return None
    abs_comma = value_start + comma_rel
    return raw[:abs_comma] + '"' + raw[abs_comma:]


def re_capture(text: str, pattern: str, group: int = 1) -> Optional[str]:
    """执行正则搜索并返回指定捕获组，未匹配返回 None。"""
    m = re.search(pattern, text)
    return m.group(group) if m else None


def fallback_quoted(text: str, key: str) -> Optional[str]:
    """在原始文本中回退提取双引号字符串字段。"""
    return re_capture(text, '"' + re.escape(key) + r'"\s*:\s*"([^"]*)"')


def fallback_bool(text: str, key: str) -> Optional[bool]:
    """在原始文本中回退提取布尔字段 true/false。"""
    cap = re_capture(text, '"' + re.escape(key) + r'"\s*:\s*(true|false)')
    if cap is None:
        return None
    return cap == "true"


def fallback_long(text: str, key: str) -> Optional[int]:
    """在原始文本中回退提取整数字段。"""
    cap = re_capture(text, '"' + re.escape(key) + r'"\s*:\s*(-?\d+)')
    return int(cap) if cap is not None else None


def fallback_double(text: str, key: str) -> Optional[float]:
    """在原始文本中回退提取浮点数字段。"""
    cap = re_capture(text, '"' + re.escape(key) + r'"\s*:\s*(-?\d+(?:\.\d+)?)')
    return float(cap) if cap is not None else None


def fallback_duration(text: str) -> Optional[float]:
    """回退解析 duration 字段，兼容科学计数法。"""
    cap = re_capture(text, r'"duration"\s*:\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)')
    if cap is None:
        return None
    try:
        return float(cap)
    except ValueError:
        return None


def fallback_workspace_leaf(text: str) -> Optional[str]:
    """回退提取首个 workspace 路径并返回目录名。"""
    cap = re_capture(text, r'"workspace_roots"\s*:\s*\[\s*"([^"]*)"')
    if not cap:
        return None
    normalized = cap.rstrip("/")
    leaf = os.path.basename(normalized)
    return leaf or None


def get_hook_project_log_path(log_date: str) -> Path:
    """获取按日切分的日志文件路径，必要时自动创建日志目录。"""
    project_dir = os.environ.get("CURSOR_PROJECT_DIR", "").strip()
    if not project_dir:
        #project_dir = str(RUNTIME_DIR.parent)
        project_dir = os.getcwd()
    log_dir = Path(project_dir) / ".cursor" / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    dd = log_date.strip() or datetime.now().strftime("%Y-%m-%d")
    return log_dir / f"r2e_hook_event_{dd}.log"

# 字段	类型	描述	
# conversation_id	string	跨多轮对话保持稳定的会话 ID	
# generation_id	string	会随着每条用户消息变化的当前生成 ID	
# model	string	触发该 hook 的 composer 所配置的模型	
# hook_event_name	string	当前正在运行的 hook	
# cursor_version	string	Cursor 应用版本 (例如 "1.7.2")	
# workspace_roots	string[]	工作区中的根文件夹列表 (通常只有一个，但多根工作区可能有多个)	
# user_email	string	null	已认证用户的电子邮箱地址 (如果可用)
# transcript_path	string	null	主会话记录文件的路径 (如果禁用了会话记录，则为 null)
class R2eHookInputHead:
    def __init__(self) -> None:
        """初始化 Hook 头部字段，先填充默认占位值。"""
        self.captured_at: datetime = datetime.now()
        self.conversation_id: str = "-"
        self.generation_id: str = "-"
        self.model: str = "-"
        self.hook_event_name: str = "-"
        self.cursor_version: str = "-"
        self.workspace_root: str = "-"
        self.user_email: Optional[str] = None
        self.transcript_path: Optional[str] = None
        self.is_valid_Json: bool = True

    def date_string(self) -> str:
        """返回日期字符串。"""
        return self.captured_at.strftime("%Y-%m-%d")

    def to_log_prefix(self) -> str:
        """生成日志前缀，拼接时间与核心上下文字段（仅含当日时刻 ``HH:MM:SS``，不含日期）。"""
        ts = self.captured_at.strftime("%H:%M:%S")
        return (
            f"[{ts}]"
            f"[{self.workspace_root}]"
            f"[{pretty_uuid(self.conversation_id)}]"
            f"[{pretty_uuid(self.generation_id)}]"
            f"[{self.model}]"
            f"[{self.hook_event_name}]"
        )


def get_hook_input_head_and_body(raw_input: Optional[str] = None) -> Tuple[R2eHookInputHead, str]:
    """解析 Hook 输入并拆分头部信息与正文字符串。"""
    head = R2eHookInputHead()
    if raw_input is None:
        raw_input = sys.stdin.read()
    raw_input = raw_input.lstrip("\ufeff")
    body_str = raw_input

    try:
        try:
            obj = json.loads(raw_input)
        except json.JSONDecodeError:
            repaired = repair_missing_closing_quote_after_text(raw_input)
            if repaired is not None:
                obj = json.loads(repaired)
            else:
                raise
        if not isinstance(obj, dict):
            raise ValueError("root not object")

        if isinstance(obj.get("conversation_id"), str):
            head.conversation_id = obj.pop("conversation_id")
        if isinstance(obj.get("generation_id"), str):
            head.generation_id = obj.pop("generation_id")
        if isinstance(obj.get("model"), str):
            head.model = obj.pop("model")
        if isinstance(obj.get("hook_event_name"), str):
            head.hook_event_name = obj.pop("hook_event_name")

        if "workspace_roots" in obj:
            wr = obj.pop("workspace_roots")
            first = None
            if isinstance(wr, list) and wr:
                first = str(wr[0])
            elif isinstance(wr, str):
                first = wr
            if first and first.strip():
                normalized = first.rstrip("/")
                leaf = os.path.basename(normalized)
                if leaf:
                    head.workspace_root = leaf

        if "cursor_version" in obj:
            v = obj.pop("cursor_version")
            if isinstance(v, str):
                head.cursor_version = v if v else "-"
        if "user_email" in obj:
            v = obj.pop("user_email")
            if v is None:
                head.user_email = None
            elif isinstance(v, str):
                head.user_email = v if v else None
        if "transcript_path" in obj:
            v = obj.pop("transcript_path")
            if v is None:
                head.transcript_path = None
            elif isinstance(v, str):
                head.transcript_path = v if v else None

        body_str = json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        head.is_valid_Json = False
        body_str = raw_input
        c = fallback_quoted(raw_input, "conversation_id")
        if c is not None:
            head.conversation_id = c
        c = fallback_quoted(raw_input, "generation_id")
        if c is not None:
            head.generation_id = c
        c = fallback_quoted(raw_input, "model")
        if c is not None:
            head.model = c
        c = fallback_quoted(raw_input, "hook_event_name")
        if c is not None:
            head.hook_event_name = c
        c = fallback_quoted(raw_input, "cursor_version")
        if c is not None:
            head.cursor_version = c if c else "-"
        c = fallback_quoted(raw_input, "user_email")
        if c is not None:
            head.user_email = c if c else None
        c = fallback_quoted(raw_input, "transcript_path")
        if c is not None:
            head.transcript_path = c if c else None
        leaf = fallback_workspace_leaf(raw_input)
        if leaf:
            head.workspace_root = leaf

    return head, body_str


def invalid_others() -> Dict[str, str]:
    """构造统一的无效 JSON 错误对象。"""
    return {"_errorMessage": "invalid json"}
