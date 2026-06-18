#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def r2u_run(skill: str, command: Sequence[str], logpath: str) -> int:
    """在 ``.codex/logs`` 下记录日志并运行 ``command``；返回进程退出码。"""
    if not command:
        sys.stderr.write("r2u_run: command must be non-empty\n")
        return 2

    log_path = Path(logpath)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("w", encoding="utf-8") as out_file:
        completed = subprocess.run(list(command), shell=False, stdout=out_file, stderr=subprocess.STDOUT, text=True)
    exit_code = completed.returncode
    if exit_code == 0:
        message = "向用户汇报本次命令成功执行；禁止读取本次执行成功的日志原文。"
    else:
        message = "向用户汇报本次命令执行失败；允许读取本次执行失败的日志原文, 分析原因并给出解决方案。"
    sys.stdout.write(json.dumps({"exit_code": exit_code, "user_message": message}, ensure_ascii=False) + "\n")
    return exit_code
