#!/usr/bin/env python3

from __future__ import annotations

import csv
import os
import platform
import shutil
import subprocess
from pathlib import Path


TABLE_PATH = Path("assets/c15.csv")
DOC_PATH = Path("onnx_profile/results/reports/experiment_environment.md")


def read_first_cpu_model() -> str:
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.is_file():
        return platform.processor() or "unknown"
    for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lower().startswith("model name"):
            return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def read_mem_total() -> str:
    meminfo = Path("/proc/meminfo")
    if not meminfo.is_file():
        return "unknown"
    for line in meminfo.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("MemTotal:"):
            return line.split(":", 1)[1].strip()
    return "unknown"


def run_version(command: list[str]) -> str:
    if shutil.which(command[0]) is None:
        return "not found"
    try:
        completed = subprocess.run(command, check=False, text=True, capture_output=True, timeout=20)
    except Exception as exc:
        return f"unavailable: {type(exc).__name__}"
    text = "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip().splitlines()
    for line in text:
        if line.startswith("Version "):
            return line
    for line in text:
        if line and not line.startswith("["):
            return line
    return "unknown"


def python_package_version(package: str) -> str:
    try:
        module = __import__(package)
    except ImportError:
        return "not installed"
    return getattr(module, "__version__", "unknown")


def main() -> None:
    rows = [
        {"item": "CPU model", "value": read_first_cpu_model(), "source": "/proc/cpuinfo"},
        {"item": "CPU logical threads", "value": str(os.cpu_count() or "unknown"), "source": "os.cpu_count()"},
        {"item": "RAM", "value": read_mem_total(), "source": "/proc/meminfo"},
        {"item": "OS", "value": platform.platform(), "source": "platform.platform()"},
        {"item": "Python", "value": platform.python_version(), "source": "platform.python_version()"},
        {"item": "onnxruntime", "value": python_package_version("onnxruntime"), "source": "Python package"},
        {"item": "onnx", "value": python_package_version("onnx"), "source": "Python package"},
        {"item": "Quartus", "value": run_version(["quartus_sh", "--version"]), "source": "quartus_sh --version"},
        {"item": "FPGA device", "value": "10M50DAF484", "source": "assets/decode_matvec_board_validation.csv"},
        {"item": "ORT provider for sweeps", "value": "CPUExecutionProvider", "source": "sweep configuration"},
    ]
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TABLE_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["item", "value", "source"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Experiment Environment",
        "",
        "| item | value | source |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| {row['item']} | {row['value']} | `{row['source']}` |")
    lines.extend(
        [
            "",
            "The ONNX Runtime sweeps use `CPUExecutionProvider` and are host-side profiles.",
            "The Quartus and FPGA device entries document the primitive-validation tool/device environment only; they are not end-to-end ONNX Runtime acceleration evidence.",
        ]
    )
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
