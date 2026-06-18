#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def prepare_prerun(skill: str) -> Path:
    log_dir = Path.cwd().resolve() / ".codex" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{skill}_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')}.log"


def main() -> int:
    parser = argparse.ArgumentParser(description="r2u prerun preparation")
    parser.add_argument("--skill", required=True, help="skill name used as the log file prefix")
    args = parser.parse_args()

    log_path = prepare_prerun(args.skill)
    message = "本次命令正在运行；运行期间禁止agent读取本次运行日志原文。"
    sys.stdout.write(json.dumps({"log_path": str(log_path), "agent_message": message}, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
