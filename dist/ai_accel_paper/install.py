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
from pathlib import Path


DEFAULT_BASE_URL = "https://ftp.kotori9.dev/ai_accel_paper/"
USER_AGENT = "Mozilla/5.0 ai-accel-paper-installer/0.1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", help="Use a local package directory instead of downloading")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--dest", default=".")
    parser.add_argument("--venv", action="store_true", help="Create/use .venv before installing requirements")
    parser.add_argument("--run-cpu", action="store_true")
    parser.add_argument("--run-ort", action="store_true")
    parser.add_argument("--run-fpga", action="store_true")
    parser.add_argument("--list-ports", action="store_true", help="List serial ports using the packaged FPGA UART runner")
    parser.add_argument("--port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--runs", type=int, default=3)
    return parser.parse_args()


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
    dest = Path(args.dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    copy_or_download(args, dest)

    py = python_cmd(args, dest)
    subprocess.run(py + ["-m", "pip", "install", "-r", "windows/requirements.txt"], cwd=dest, check=False)

    log_dir = dest / "logs" / datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir.mkdir(parents=True, exist_ok=True)
    summary: list[dict[str, object]] = []
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
    (log_dir / "install_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"summary: {log_dir / 'install_summary.json'}")


if __name__ == "__main__":
    main()
