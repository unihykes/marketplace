# 公共封装

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
    """将 ID 简写为首段，便于日志展示。"""
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
      ``剩余 = 总字节数 - 实际前缀字节数``，保证 ``前缀字节数 + 剩余 == 总字节数``。
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




def get_hook_project_log_path(log_date: str) -> Path:
    """获取按日切分的日志文件路径，必要时自动创建日志目录。"""
    project_dir = os.environ.get("CODEX_PROJECT_DIR", "").strip()
    if not project_dir:
        project_dir = os.getcwd()
    log_dir = Path(project_dir) / ".codex" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    dd = log_date.strip() or datetime.now().strftime("%Y-%m-%d")
    return log_dir / f"r2u_hook_event_{dd}.log"


# Codex Hook 通用 head 字段:
# Field            Type          Meaning
# session_id       string        Current Codex session id. Subagent hooks use the parent session id.
# transcript_path  string|null   Path to the session transcript file, if any
# cwd              string        Working directory for the session
# hook_event_name  string        Current hook event name
# model            string        Codex-specific extension. Active model slug

# 其他字段
# turn_id          string        Turn-scoped hooks list turn_id as a Codex-specific extension in their event-specific tables.
# permission_mode  string        describes the current permission mode as default, acceptEdits, plan, dontAsk, or bypassPermissions

# 备注
# hook PreCompact  不存在 permission_mode 字段
# hook PostCompact 不存在 permission_mode 字段

class R2eHookInputHead:
    def __init__(self) -> None:
        """初始化 Hook 头部字段，先填充默认占位值。"""
        self.captured_at: datetime = datetime.now()
        self.session_id: str = "-"
        self.model: str = "-"
        self.hook_event_name: str = "-"
        self.cwd: str = "-"
        self.transcript_path: Optional[str] = None
        self.turn_id: str = "-"
        self.permission_mode: str = "-"
        self.is_valid_Json: bool = True

    def date_string(self) -> str:
        """返回日期字符串。"""
        return self.captured_at.strftime("%Y-%m-%d")

    def cwd_leaf(self) -> str:
        """返回 cwd 的最后一级目录名，用于日志前缀。"""
        if self.cwd == "-":
            return "-"
        normalized = self.cwd.rstrip("/")
        leaf = os.path.basename(normalized)
        return leaf or self.cwd

    def to_log_prefix(self) -> str:
        """生成日志前缀，拼接时刻与核心上下文字段（仅含当日时刻 ``HH:MM:SS``，不含日期）。"""
        ts = self.captured_at.strftime("%H:%M:%S")
        return (
            f"[{ts}]"
            f"[{self.cwd_leaf()}]"
            f"[{pretty_uuid(self.session_id)}]"
            f"[{pretty_uuid(self.turn_id)}]"
            f"[{self.model}]"
            f"[{self.permission_mode}]"
            f"[{self.hook_event_name}]"
        )


def get_hook_input_head_and_body(raw_input: Optional[str] = None) -> Tuple[R2eHookInputHead, str]:
    """解析 Hook 输入并拆分手部信息与正文字符串。"""
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

        # Codex head 字段提取
        if isinstance(obj.get("session_id"), str):
            head.session_id = obj.pop("session_id")
        if isinstance(obj.get("model"), str):
            head.model = obj.pop("model")
        if isinstance(obj.get("hook_event_name"), str):
            head.hook_event_name = obj.pop("hook_event_name")
        if isinstance(obj.get("cwd"), str):
            head.cwd = obj.pop("cwd")
        if "transcript_path" in obj:
            v = obj.pop("transcript_path")
            if v is None:
                head.transcript_path = None
            elif isinstance(v, str):
                head.transcript_path = v if v else None
        if isinstance(obj.get("turn_id"), str):
            head.turn_id = obj.pop("turn_id")
        if isinstance(obj.get("permission_mode"), str):
            head.permission_mode = obj.pop("permission_mode")

        body_str = json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        head.is_valid_Json = False
        body_str = raw_input
        # 回退提取 Codex head 字段
        c = fallback_quoted(raw_input, "session_id")
        if c is not None:
            head.session_id = c
        c = fallback_quoted(raw_input, "model")
        if c is not None:
            head.model = c
        c = fallback_quoted(raw_input, "hook_event_name")
        if c is not None:
            head.hook_event_name = c
        c = fallback_quoted(raw_input, "cwd")
        if c is not None:
            head.cwd = c
        c = fallback_quoted(raw_input, "transcript_path")
        if c is not None:
            head.transcript_path = c if c else None
        c = fallback_quoted(raw_input, "turn_id")
        if c is not None:
            head.turn_id = c
        c = fallback_quoted(raw_input, "permission_mode")
        if c is not None:
            head.permission_mode = c

    return head, body_str


def invalid_others() -> Dict[str, str]:
    """构造统一的无效 JSON 错误对象。"""
    return {"_errorMessage": "invalid json"}