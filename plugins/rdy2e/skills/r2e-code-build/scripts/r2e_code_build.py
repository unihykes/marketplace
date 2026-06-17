#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path


def create_command(kind: str, module: str) -> list[str]:
    """生成待执行命令。

    :param kind: ``debug`` 或 ``release``（对应命令行 ``--kind``，忽略大小写），追加到 ``makec.sh -j8`` 之后。
    :param module: 项目内相对子路径（对应 ``--module``）；为空表示编译所有模块。不得为绝对路径。
    """
    bt = kind.strip().lower()
    if bt not in ("debug", "release"):
        raise ValueError(f"--kind 须为 debug 或 release，收到: {kind!r}")

    if module and Path(module).is_absolute():
        raise ValueError("仅支持项目内相对路径（不得为绝对路径）")

    project_root = Path.cwd().resolve()
    script = (
        "set -eo pipefail && "
        'ABPLATFORM="Linux_el7a3_x64" &&'
        f"PROJECT_ROOT={shlex.quote(str(project_root))} && "
        f"REL={shlex.quote(module)} && "
        f"cd {shlex.quote(str(project_root / 'cmake'))} && "
        "source ./abenv.sh && "
        'if [ -n "$REL" ]; then cd "$PROJECT_ROOT/$REL"; fi && '
        f"makec.sh -j8 {bt}"
    )
    return ["bash", "-lc", script]


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
    from r2e_run import r2e_run  # noqa: PLC0415 — 需在补全 import 路径之后（``skills/common``）

    parser = argparse.ArgumentParser(description="r2e C++ 代码构建入口")
    parser.add_argument(
        "--module",
        default="",
        help="项目内相对路径（可选；为空表示编译所有模块；不得为绝对路径）",
    )
    parser.add_argument(
        "--kind",
        dest="kind",
        default="debug",
        metavar="debug|release",
        help="debug 或 release（忽略大小写；默认 debug）",
    )
    args = parser.parse_args()

    try:
        command = create_command(args.kind, args.module)
    except ValueError as e:
        sys.stderr.write(f"{e}\n")
        return 1

    return r2e_run(Path(__file__).stem, command)


if __name__ == "__main__":
    raise SystemExit(main())
