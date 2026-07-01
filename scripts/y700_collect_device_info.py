#!/usr/bin/env python3
"""Collect read-only Lenovo Y700 Android/ADB environment evidence."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs/y700_onnx_runtime"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR))
    parser.add_argument("--serial", help="Optional adb device serial.")
    return parser.parse_args()


def run_cmd(args: list[str], timeout_s: int = 20) -> dict[str, object]:
    try:
        proc = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        return {
            "cmd": args,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": args,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timed_out": True,
        }


def adb_base(serial: str | None) -> list[str]:
    base = ["adb"]
    if serial:
        base.extend(["-s", serial])
    return base


def parse_devices(stdout: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("List of devices"):
            continue
        parts = line.split()
        serial = parts[0]
        state = parts[1] if len(parts) > 1 else "unknown"
        rows.append({"serial": serial, "state": state})
    return rows


def adb_shell(serial: str | None, command: str, timeout_s: int = 20) -> dict[str, object]:
    return run_cmd(adb_base(serial) + ["shell", command], timeout_s=timeout_s)


def main() -> None:
    args = parse_args()
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    adb_path = shutil.which("adb")
    captured_at = datetime.now().isoformat(timespec="seconds")
    payload: dict[str, object] = {
        "captured_at": captured_at,
        "adb_available": bool(adb_path),
        "requested_serial": args.serial or "",
        "status": "unknown",
        "commands": {},
        "device": {},
        "claim_boundary": "Read-only Android environment evidence. No ONNX Runtime benchmark result is implied.",
    }

    if not adb_path:
        payload["status"] = "adb_missing"
        (log_dir / "device_info.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        write_runtime_env(log_dir, payload)
        print("adb not found")
        return

    devices_cmd = run_cmd(["adb", "devices", "-l"])
    payload["commands"]["adb_devices_l"] = devices_cmd
    devices = parse_devices(str(devices_cmd.get("stdout", "")))
    payload["devices"] = devices
    online = [row for row in devices if row.get("state") == "device"]

    if args.serial:
        online = [row for row in online if row.get("serial") == args.serial]

    if not online:
        payload["status"] = "no_device"
        (log_dir / "device_info.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        write_runtime_env(log_dir, payload)
        print(f"no adb device; wrote {log_dir / 'device_info.json'}")
        return

    serial = args.serial or online[0]["serial"]
    payload["status"] = "device_connected"
    payload["selected_serial"] = serial

    checks = {
        "ro.product.model": "getprop ro.product.model",
        "ro.product.manufacturer": "getprop ro.product.manufacturer",
        "ro.board.platform": "getprop ro.board.platform",
        "ro.hardware": "getprop ro.hardware",
        "ro.build.version.release": "getprop ro.build.version.release",
        "ro.build.version.sdk": "getprop ro.build.version.sdk",
        "ro.product.cpu.abi": "getprop ro.product.cpu.abi",
        "meminfo": "cat /proc/meminfo | head -40",
        "thermalservice": "dumpsys thermalservice",
        "storage": "df -h /data /sdcard 2>/dev/null",
        "python": "command -v python3 || command -v python || true",
    }

    device: dict[str, object] = {}
    for key, shell_cmd in checks.items():
        result = adb_shell(serial, shell_cmd, timeout_s=30)
        payload["commands"][key] = result
        stdout = str(result.get("stdout", "")).strip()
        if key.startswith("ro."):
            device[key] = stdout
        elif key == "python":
            device["python_path"] = stdout
    payload["device"] = device

    (log_dir / "device_info.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_runtime_env(log_dir, payload)
    print(f"wrote {log_dir / 'device_info.json'}")


def write_runtime_env(log_dir: Path, payload: dict[str, object]) -> None:
    lines = [
        "# Lenovo Y700 ONNX Runtime Environment",
        "",
        f"- captured_at: {payload.get('captured_at', '')}",
        f"- status: {payload.get('status', '')}",
        f"- adb_available: {payload.get('adb_available', '')}",
        f"- selected_serial: {payload.get('selected_serial', '')}",
        f"- claim_boundary: {payload.get('claim_boundary', '')}",
        "",
        "## Device",
        "",
    ]
    device = payload.get("device")
    if isinstance(device, dict) and device:
        for key, value in device.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- device: not connected")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This file records Android/ADB environment state only. It is not an ONNX Runtime latency result.",
        ]
    )
    (log_dir / "runtime_env.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
