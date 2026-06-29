#!/usr/bin/env python3
"""Install/download and smoke-test the ai_accel_paper package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path, PureWindowsPath


DEFAULT_BASE_URL = "https://ftp.kotori9.dev/ai_accel_paper/"
USER_AGENT = "Mozilla/5.0 ai-accel-paper-installer/0.1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", help="Use a local package directory instead of downloading")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--install-dir", help="Directory where package files are downloaded/copied")
    parser.add_argument("--work-dir", help="Alias for --install-dir")
    parser.add_argument("--dest", help=argparse.SUPPRESS)
    parser.add_argument("--venv", action="store_true", help="Create/use .venv before installing requirements")
    parser.add_argument("--run-cpu", action="store_true")
    parser.add_argument("--run-ort", action="store_true")
    parser.add_argument("--run-fpga", action="store_true")
    parser.add_argument("--run-jtag", action="store_true")
    parser.add_argument("--extract-quartus-summary", action="store_true")
    parser.add_argument("--run-full-eval", action="store_true")
    parser.add_argument("--list-ports", action="store_true", help="List serial ports using the packaged FPGA UART runner")
    parser.add_argument("--port")
    parser.add_argument("--quartus-bin")
    parser.add_argument("--cable", default="USB-Blaster [USB-0]")
    parser.add_argument("--keep-tcl", action="store_true")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--runs", type=int, default=3)
    return parser.parse_args()


def looks_like_windows_path(value: str | Path) -> bool:
    text = str(value)
    return "\\" in text or (len(text) >= 2 and text[1] == ":")


def is_drive_root(path: Path | PureWindowsPath) -> bool:
    if isinstance(path, PureWindowsPath):
        return bool(path.anchor) and str(path) == path.anchor
    return path.parent == path


def path_key(path: Path | PureWindowsPath) -> str:
    if isinstance(path, PureWindowsPath):
        return str(path).replace("/", "\\").lower().rstrip("\\/")
    if os.name == "nt":
        return str(path).replace("/", "\\").lower().rstrip("\\/")
    return str(path)


def same_or_child(path: Path | PureWindowsPath, parent: Path | PureWindowsPath) -> bool:
    child_key = path_key(path)
    parent_key = path_key(parent)
    if not parent_key or child_key == parent_key:
        return child_key == parent_key
    separator = "\\" if isinstance(path, PureWindowsPath) or isinstance(parent, PureWindowsPath) or os.name == "nt" else "/"
    return child_key.startswith(parent_key + separator)


def normalized_path(value: str | Path) -> Path | PureWindowsPath:
    text = str(value)
    if looks_like_windows_path(text):
        return PureWindowsPath(text)
    return Path(text).expanduser().resolve()


def add_protected_root(roots: list[Path | PureWindowsPath], root: Path | PureWindowsPath) -> None:
    if is_drive_root(root):
        return
    roots.append(root)


def protected_roots(quartus_bin: str | None) -> list[Path | PureWindowsPath]:
    roots: list[Path | PureWindowsPath] = []
    windows_style_quartus = bool(quartus_bin and looks_like_windows_path(quartus_bin))
    if os.name == "nt" or windows_style_quartus:
        default_drive = "C:"
        if quartus_bin and windows_style_quartus:
            qdrive = PureWindowsPath(quartus_bin).drive
            if qdrive:
                default_drive = qdrive
        for env_name in ["ProgramFiles", "ProgramFiles(x86)"]:
            value = os.environ.get(env_name)
            if value:
                add_protected_root(roots, PureWindowsPath(value))
        if not os.environ.get("ProgramFiles"):
            add_protected_root(roots, PureWindowsPath(default_drive + "\\Program Files"))
        if not os.environ.get("ProgramFiles(x86)"):
            add_protected_root(roots, PureWindowsPath(default_drive + "\\Program Files (x86)"))
        system_drive = os.environ.get("SystemDrive", default_drive)
        for name in ["altera_lite", "intelFPGA_lite", "intelFPGA"]:
            add_protected_root(roots, PureWindowsPath(system_drive + "\\") / name)
    if quartus_bin:
        qpath = PureWindowsPath(quartus_bin) if looks_like_windows_path(quartus_bin) else Path(quartus_bin)
        parts_lower = [part.lower() for part in qpath.parts]
        for marker in ["altera_lite", "intelfpga_lite", "intelfpga"]:
            if marker in parts_lower:
                idx = parts_lower.index(marker)
                add_protected_root(roots, type(qpath)(*qpath.parts[: idx + 1]))
        if "quartus" in parts_lower:
            idx = parts_lower.index("quartus")
            if idx > 0:
                add_protected_root(roots, type(qpath)(*qpath.parts[:idx]))
    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        resolved = root if isinstance(root, PureWindowsPath) else root.expanduser().resolve()
        if is_drive_root(resolved):
            continue
        key = path_key(resolved)
        if key not in seen:
            unique.append(resolved)
            seen.add(key)
    return unique


def assert_safe_package_root(package_root: Path, quartus_bin: str | None) -> None:
    resolved = normalized_path(package_root)
    for root in protected_roots(quartus_bin):
        if same_or_child(resolved, root):
            raise SystemExit(
                "\n".join(
                    [
                        "Refusing to install package files into a protected toolchain directory.",
                        f"package root: {resolved}",
                        f"protected root: {root}",
                        "Choose a normal working directory with --install-dir or --work-dir.",
                    ]
                )
            )


def resolve_package_root(args: argparse.Namespace) -> Path:
    requested = [value for value in [args.install_dir, args.work_dir, args.dest] if value]
    if len(set(requested)) > 1:
        raise SystemExit("--install-dir, --work-dir, and legacy --dest must not disagree")
    root = Path(requested[0]) if requested else Path.cwd()
    resolved = root.expanduser().resolve()
    assert_safe_package_root(resolved, args.quartus_bin)
    return resolved


def resolve_quartus_tool_arg(quartus_bin: str | None) -> str | None:
    if not quartus_bin:
        return None
    path = Path(quartus_bin)
    names = ["system-console.exe", "system-console", "quartus_stp.exe", "quartus_stp"]
    if path.is_dir():
        for name in names:
            candidate = path / name
            if candidate.exists():
                return str(candidate)
        raise SystemExit(f"--quartus-bin directory does not contain system-console.exe or quartus_stp.exe: {path}")
    if path.is_file() or path.name.lower() in names:
        return quartus_bin
    return quartus_bin


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest_local(base: Path) -> dict:
    return json.loads((base / "manifest.json").read_text(encoding="utf-8"))


def fetch_url(url: str, timeout: int) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise SystemExit(
            "\n".join(
                [
                    f"HTTP download failed: {url}",
                    f"status: {exc.code} {exc.reason}",
                    f"User-Agent: {USER_AGENT}",
                    "The server may block Python urllib's default User-Agent; this installer already retries with an explicit browser-like User-Agent.",
                    "If this still fails, verify the URL with curl/browser or ask the server administrator to allow this User-Agent.",
                ]
            )
        ) from exc


def load_manifest_remote(base_url: str) -> dict:
    url = base_url.rstrip("/") + "/manifest.json"
    return json.loads(fetch_url(url, timeout=20).decode("utf-8"))


def copy_or_download(args: argparse.Namespace, dest: Path) -> None:
    if args.local:
        src = Path(args.local).resolve()
        manifest = load_manifest_local(src)
        for item in manifest.get("files", []):
            rel = item["path"]
            src_path = src / rel
            dst_path = dest / rel
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            if src_path.resolve() != dst_path.resolve():
                dst_path.write_bytes(src_path.read_bytes())
    else:
        manifest = load_manifest_remote(args.base_url)
        for item in manifest.get("files", []):
            rel = item["path"]
            dst_path = dest / rel
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            url = args.base_url.rstrip("/") + "/" + rel
            dst_path.write_bytes(fetch_url(url, timeout=60))
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    failures = []
    for item in manifest.get("files", []):
        path = dest / item["path"]
        if not path.exists() or sha256(path) != item["sha256"]:
            failures.append(item["path"])
    if failures:
        raise SystemExit("checksum verification failed for: " + ", ".join(failures))


def python_cmd(args: argparse.Namespace, dest: Path) -> list[str]:
    if not args.venv:
        return [sys.executable]
    venv = dest / ".venv"
    if not venv.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    if os.name == "nt":
        return [str(venv / "Scripts/python.exe")]
    return [str(venv / "bin/python")]


def run_step(cmd: list[str], cwd: Path, summary: list[dict[str, object]]) -> None:
    print("+ " + " ".join(cmd))
    proc = subprocess.run(cmd, cwd=cwd)
    summary.append({"cmd": cmd, "returncode": proc.returncode})


def main() -> None:
    args = parse_args()
    if sys.version_info < (3, 9):
        raise SystemExit("Python 3.9 or newer is required")
    dest = resolve_package_root(args)
    quartus_tool = resolve_quartus_tool_arg(args.quartus_bin)
    log_dir = dest / "logs" / datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"package root: {dest}", flush=True)
    print(f"base url: {args.base_url}", flush=True)
    print(f"quartus tool path: {quartus_tool or '(auto-detect)'}", flush=True)
    print(f"log dir: {log_dir}", flush=True)
    dest.mkdir(parents=True, exist_ok=True)
    copy_or_download(args, dest)

    py = python_cmd(args, dest)
    subprocess.run(py + ["-m", "pip", "install", "-r", "windows/requirements.txt"], cwd=dest, check=False)

    log_dir.mkdir(parents=True, exist_ok=True)
    summary: list[dict[str, object]] = []
    if args.run_full_eval:
        args.run_cpu = True
        args.run_ort = True
        args.run_jtag = True
        args.extract_quartus_summary = True
    if args.list_ports:
        run_step(py + ["windows/run_fpga_uart_matvec.py", "--list-ports"], dest, summary)
    if args.run_cpu:
        run_step(py + ["windows/run_cpu_matvec_baseline.py", "--runs", str(args.runs), "--log-dir", str(log_dir)], dest, summary)
    if args.run_ort:
        run_step(py + ["windows/run_ort_matvec_baseline.py", "--runs", str(args.runs), "--log-dir", str(log_dir)], dest, summary)
    if args.run_fpga:
        cmd = py + ["windows/run_fpga_uart_matvec.py", "--runs", str(args.runs), "--baud", str(args.baud), "--log-dir", str(log_dir)]
        if args.port:
            cmd += ["--port", args.port]
        run_step(cmd, dest, summary)
    if args.run_jtag:
        cmd = py + [
            "windows/run_fpga_jtag_matvec.py",
            "--runs",
            str(args.runs),
            "--cable",
            args.cable,
            "--log-dir",
            str(log_dir),
        ]
        if quartus_tool:
            cmd += ["--quartus-bin", quartus_tool]
        if args.keep_tcl:
            cmd += ["--keep-tcl"]
        run_step(cmd, dest, summary)
    if args.extract_quartus_summary:
        run_step(
            py
            + [
                "scripts/extract_quartus_summary.py",
                "--quartus-dir",
                "quartus/de10_lite_jtag_matvec/output_files",
            ],
            dest,
            summary,
        )
    if args.run_full_eval:
        run_step(py + ["scripts/build_ort_fpga_comparison.py"], dest, summary)
    (log_dir / "install_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"summary: {log_dir / 'install_summary.json'}")


if __name__ == "__main__":
    main()
