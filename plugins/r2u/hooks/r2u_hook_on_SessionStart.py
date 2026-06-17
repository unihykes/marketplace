#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, Optional

import r2u_hook_common as c


# Field	Type	Meaning
# source	string	How the session started: startup, resume, clear, or compact
@dataclass
class R2eHookSessionStartInputBody:
    source: Optional[str] = None
    others: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        payload: Dict[str, Any] = {
            "source": self.source,
        }
        if self.others:
            payload["others"] = self.others
        return "\n" + json.dumps(payload, ensure_ascii=False, indent=2)


def get_hook_input_body() -> tuple[c.R2eHookInputHead, R2eHookSessionStartInputBody]:
    head, body_str = c.get_hook_input_head_and_body()
    inst = R2eHookSessionStartInputBody()
    hv = head.is_valid_Json
    if not str(body_str).strip():
        return head, inst
    if not hv:
        inst.source = c.fallback_quoted(body_str, "source")
        inst.others = c.invalid_others()
        return head, inst
    try:
        obj = json.loads(body_str)
        if not isinstance(obj, dict):
            raise ValueError("body not object")
    except Exception:
        inst.others = c.invalid_others()
        return head, inst

    if "source" in obj:
        inst.source = obj.pop("source")
    if obj:
        inst.others = dict(obj)
    return head, inst


# Field	Effect
# continue	If false, marks that hook run as stopped
# stopReason	Recorded as the reason for stopping
# systemMessage	Surfaced as a warning in the UI or event stream
# suppressOutput	Parsed today but not yet implemented
# hookSpecificOutput.hookEventName	SessionStart
# hookSpecificOutput.additionalContext	Extra developer context injected into the conversation
def _toml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _strip_toml_inline_comment(value: str) -> str:
    quote_char: Optional[str] = None
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if quote_char == '"' and char == "\\":
            escaped = True
            continue
        if char in ("'", '"'):
            if quote_char == char:
                quote_char = None
            elif quote_char is None:
                quote_char = char
            continue
        if char == "#" and quote_char is None:
            return value[:index]
    return value


def _is_toml_empty_value(value: str) -> bool:
    normalized = _strip_toml_inline_comment(value).strip()
    return normalized in ("", '""', "''")


def _ensure_context_contract_text() -> str:
    plugin_root = os.environ.get("PLUGIN_ROOT", "").strip()
    if not plugin_root:
        return ""

    context_path = Path(plugin_root) / "contexts" / "r2u_context_contract.toml"
    defaults = {
        "R2U_PLUGIN_ROOT": plugin_root,
    }
    context_path.parent.mkdir(parents=True, exist_ok=True)

    if not context_path.exists():
        context_path.write_text(
            "".join(f"{key} = {_toml_quote(value)}\n" for key, value in defaults.items()),
            encoding="utf-8",
        )
        return context_path.read_text(encoding="utf-8")

    lines = context_path.read_text(encoding="utf-8").splitlines()
    seen_keys = set()
    changed = False
    next_lines = []
    for line in lines:
        stripped = line.strip()
        if "=" not in stripped or stripped.startswith("#"):
            next_lines.append(line)
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key not in defaults:
            next_lines.append(line)
            continue
        seen_keys.add(key)
        if not _is_toml_empty_value(value):
            next_lines.append(line)
            continue
        next_lines.append(f"{key} = {_toml_quote(defaults[key])}")
        changed = True

    for key, value in defaults.items():
        if key not in seen_keys:
            next_lines.append(f"{key} = {_toml_quote(value)}")
            changed = True

    if changed:
        context_path.write_text("\n".join(next_lines) + "\n", encoding="utf-8")

    return context_path.read_text(encoding="utf-8")


def build_hook_response() -> str:
    context_parts = [
        _ensure_context_contract_text(),
        c.load_plugin_context_text("AGENTS.r2u.md"),
    ]
    additional_context = "\n\n".join(part for part in context_parts if part.strip())
    return json.dumps({
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": additional_context
        }
    }, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    head, body = get_hook_input_body()
    response = build_hook_response()
    with open(c.get_hook_project_log_path(head.date_string()), "a", encoding="utf-8", errors="replace") as log_file:
        log_file.write(
            f"{head.to_log_prefix()}"
            f"{body.to_string()}\n"
            f"{response}\n"
        )
    c.write_stdout_utf8(response)
