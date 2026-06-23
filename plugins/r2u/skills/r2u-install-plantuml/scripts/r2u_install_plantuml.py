#!/usr/bin/env python3
"""Install Java, Graphviz, and the latest PlantUML jar for the r2u plugin."""

from __future__ import annotations

import argparse
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


OFFICIAL_DOWNLOAD_PAGE = "https://plantuml.com/download"
FALLBACK_LATEST_JAR_URL = "https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar"


def run_command(args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    print(f"[run] {' '.join(args)}", flush=True)
    return subprocess.run(
        args,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def command_available(command: str) -> bool:
    return shutil.which(command) is not None


def print_command_output(prefix: str, result: subprocess.CompletedProcess[str]) -> None:
    output = (result.stdout or "").strip()
    if output:
        print(f"{prefix}\n{output}", flush=True)


def java_installed() -> bool:
    if not command_available("java"):
        return False
    result = run_command(["java", "-version"])
    print_command_output("[java]", result)
    return result.returncode == 0


def graphviz_installed() -> bool:
    if not command_available("dot"):
        return False
    result = run_command(["dot", "-V"])
    print_command_output("[graphviz]", result)
    return result.returncode == 0


def install_with_candidates(candidates: list[list[str]], label: str) -> None:
    attempted: list[str] = []
    for command in candidates:
        if not command_available(command[0]):
            continue
        attempted.append(" ".join(command))
        result = run_command(command)
        print_command_output(f"[{label} installer]", result)
        if result.returncode == 0:
            print(f"[ok] {label} installed", flush=True)
            return

    if attempted:
        raise RuntimeError(f"failed to install {label}; attempted: " + " | ".join(attempted))
    raise RuntimeError(f"no supported package manager found to install {label}; install it manually")


def install_java() -> None:
    system = platform.system().lower()
    if system == "windows":
        install_with_candidates(
            [
                [
                    "winget",
                    "install",
                    "--id",
                    "EclipseAdoptium.Temurin.21.JRE",
                    "--exact",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                ],
                ["choco", "install", "temurinjre", "-y"],
                ["scoop", "install", "temurin21-jre"],
            ],
            "Java",
        )
    elif system == "darwin":
        install_with_candidates([["brew", "install", "openjdk"]], "Java")
    else:
        install_with_candidates(
            [
                ["apt-get", "install", "-y", "default-jre"],
                ["dnf", "install", "-y", "java-21-openjdk"],
                ["yum", "install", "-y", "java-21-openjdk"],
                ["apk", "add", "openjdk21-jre"],
                ["pacman", "-S", "--noconfirm", "jre-openjdk"],
            ],
            "Java",
        )


def install_graphviz() -> None:
    system = platform.system().lower()
    if system == "windows":
        install_with_candidates(
            [
                [
                    "winget",
                    "install",
                    "--id",
                    "Graphviz.Graphviz",
                    "--exact",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                ],
                ["choco", "install", "graphviz", "-y"],
                ["scoop", "install", "graphviz"],
            ],
            "Graphviz",
        )
    elif system == "darwin":
        install_with_candidates([["brew", "install", "graphviz"]], "Graphviz")
    else:
        install_with_candidates(
            [
                ["apt-get", "install", "-y", "graphviz"],
                ["dnf", "install", "-y", "graphviz"],
                ["yum", "install", "-y", "graphviz"],
                ["apk", "add", "graphviz"],
                ["pacman", "-S", "--noconfirm", "graphviz"],
            ],
            "Graphviz",
        )


def read_url(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "r2u-install-plantuml/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def resolve_latest_jar_url() -> str:
    try:
        html = read_url(OFFICIAL_DOWNLOAD_PAGE)
    except urllib.error.URLError as exc:
        print(f"[warn] failed to read official download page: {exc}", flush=True)
        return FALLBACK_LATEST_JAR_URL

    patterns = [
        r"https://github\.com/plantuml/plantuml/releases/download/v[0-9.]+/plantuml-[0-9.]+\.jar",
        r"https://github\.com/plantuml/plantuml/releases/latest/download/plantuml\.jar",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, html)
        if matches:
            return matches[0]

    print("[warn] official page did not expose a jar link; using latest fallback", flush=True)
    return FALLBACK_LATEST_JAR_URL


def download_file(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jar") as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        print(f"[download] {url}", flush=True)
        request = urllib.request.Request(url, headers={"User-Agent": "r2u-install-plantuml/1.0"})
        with urllib.request.urlopen(request, timeout=300) as response:
            with tmp_path.open("wb") as output:
                shutil.copyfileobj(response, output)
        if tmp_path.stat().st_size <= 0:
            raise RuntimeError("downloaded jar is empty")
        shutil.move(str(tmp_path), str(target))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def verify_plantuml(jar_path: Path) -> None:
    if not jar_path.exists():
        raise RuntimeError(f"PlantUML jar not found: {jar_path}")
    if command_available("java"):
        result = run_command(["java", "-jar", str(jar_path), "-version"])
        print_command_output("[plantuml]", result)
        if result.returncode != 0:
            raise RuntimeError("PlantUML jar verification failed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Java, Graphviz, and the latest PlantUML jar.")
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "assets",
        help="Directory where plantuml.jar will be stored.",
    )
    parser.add_argument("--check-only", action="store_true", help="Check status only; do not install or download.")
    parser.add_argument("--skip-install", action="store_true", help="Do not install missing Java or Graphviz.")
    parser.add_argument("--skip-download", action="store_true", help="Do not download PlantUML jar.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    jar_path = args.assets_dir / "plantuml.jar"

    has_java = java_installed()
    has_graphviz = graphviz_installed()
    print(f"[status] java={'yes' if has_java else 'no'}", flush=True)
    print(f"[status] graphviz={'yes' if has_graphviz else 'no'}", flush=True)
    print(f"[status] plantuml_jar={'yes' if jar_path.exists() else 'no'} {jar_path}", flush=True)

    if args.check_only:
        return 0 if has_java and has_graphviz and jar_path.exists() else 1

    if not has_java:
        if args.skip_install:
            print("[skip] Java is missing and --skip-install was set", flush=True)
        else:
            install_java()
            has_java = java_installed()

    if not has_graphviz:
        if args.skip_install:
            print("[skip] Graphviz is missing and --skip-install was set", flush=True)
        else:
            install_graphviz()
            has_graphviz = graphviz_installed()

    if args.skip_download:
        print("[skip] PlantUML jar download skipped by --skip-download", flush=True)
    elif jar_path.exists():
        print(f"[skip] PlantUML jar already exists at {jar_path}", flush=True)
    else:
        download_file(resolve_latest_jar_url(), jar_path)
        print(f"[ok] PlantUML jar installed at {jar_path}", flush=True)

    verify_plantuml(jar_path)

    if not has_java:
        raise RuntimeError("Java is still missing")
    if not has_graphviz:
        raise RuntimeError("Graphviz is still missing")

    print("[ok] PlantUML environment is ready", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1)

