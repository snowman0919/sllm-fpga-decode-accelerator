#!/usr/bin/env python3
"""Push and run ONNX Runtime micrograph benchmarks on a Y700 Android device via adb."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs/y700_onnx_runtime"
REMOTE_ROOT = "/data/local/tmp/sllm_fpga_y700"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR))
    parser.add_argument("--serial")
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--remote-root", default=REMOTE_ROOT)
    parser.add_argument("--suite", choices=["smoke", "projection", "all"], default="smoke")
    parser.add_argument(
        "--providers",
        default="CPUExecutionProvider,NNAPIExecutionProvider,QNNExecutionProvider",
        help="Comma-separated provider attempts. Each provider is attempted separately.",
    )
    return parser.parse_args()


def run_cmd(args: list[str], timeout_s: int = 60) -> dict[str, object]:
    try:
        proc = subprocess.run(args, check=False, capture_output=True, text=True, timeout=timeout_s)
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
        rows.append({"serial": parts[0], "state": parts[1] if len(parts) > 1 else "unknown"})
    return rows


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_summary_md(path: Path, payload: dict[str, object]) -> None:
    lines = ["# Y700 ONNX Runtime Micrograph Benchmark", ""]
    for key, value in payload.items():
        if key == "commands":
            continue
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Interpretation", ""])
    lines.append(str(payload.get("claim_boundary", "")))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def model_specs(suite: str) -> list[dict[str, object]]:
    smoke = [
        {
            "name": "matvec_cpu_baseline.onnx",
            "kind": "float_matmul",
            "input_dim": 16,
            "output_dim": 4,
        },
        {
            "name": "matvec_int8_matmulinteger.onnx",
            "kind": "matmulinteger",
            "input_dim": 16,
            "output_dim": 4,
        },
    ]
    projection = [
        {
            "name": "gemma_mlp_projection_1152x6912_float.onnx",
            "kind": "float_matmul",
            "input_dim": 1152,
            "output_dim": 6912,
        },
        {
            "name": "gemma_mlp_projection_1152x6912_matmulinteger.onnx",
            "kind": "matmulinteger",
            "input_dim": 1152,
            "output_dim": 6912,
        },
        {
            "name": "gemma_lm_head_tile_1152x4096_float.onnx",
            "kind": "float_matmul",
            "input_dim": 1152,
            "output_dim": 4096,
        },
        {
            "name": "gemma_lm_head_tile_1152x4096_matmulinteger.onnx",
            "kind": "matmulinteger",
            "input_dim": 1152,
            "output_dim": 4096,
        },
        {
            "name": "gemma_attention_output_projection_1024x1152_float.onnx",
            "kind": "float_matmul",
            "input_dim": 1024,
            "output_dim": 1152,
        },
        {
            "name": "gemma_attention_output_projection_1024x1152_matmulinteger.onnx",
            "kind": "matmulinteger",
            "input_dim": 1024,
            "output_dim": 1152,
        },
    ]
    if suite == "smoke":
        return smoke
    if suite == "projection":
        return projection
    return smoke + projection


def finish(log_dir: Path, payload: dict[str, object]) -> None:
    write_json(log_dir / "benchmark_summary.json", payload)
    write_summary_md(log_dir / "benchmark_summary.md", payload)
    print(json.dumps({"status": payload.get("status"), "log_dir": str(log_dir)}, ensure_ascii=False))


def adb_shell(serial: str | None, command: str, timeout_s: int = 60) -> dict[str, object]:
    return run_cmd(adb_base(serial) + ["shell", command], timeout_s=timeout_s)


def main() -> None:
    args = parse_args()
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    captured_at = datetime.now().isoformat(timespec="seconds")
    payload: dict[str, object] = {
        "captured_at": captured_at,
        "status": "unknown",
        "requested_serial": args.serial or "",
        "remote_root": args.remote_root,
        "warmup": args.warmup,
        "runs": args.runs,
        "suite": args.suite,
        "commands": {},
        "claim_boundary": "This micrograph harness does not imply whole-model or whole-runtime acceleration.",
    }

    if not shutil.which("adb"):
        payload["status"] = "adb_missing"
        finish(log_dir, payload)
        return

    devices_cmd = run_cmd(["adb", "devices", "-l"], timeout_s=20)
    payload["commands"]["adb_devices_l"] = devices_cmd
    devices = parse_devices(str(devices_cmd.get("stdout", "")))
    payload["devices"] = devices
    online = [row for row in devices if row.get("state") == "device"]
    if args.serial:
        online = [row for row in online if row.get("serial") == args.serial]
    if not online:
        payload["status"] = "no_device"
        finish(log_dir, payload)
        return

    serial = args.serial or online[0]["serial"]
    payload["selected_serial"] = serial

    python_probe = adb_shell(serial, "command -v python3 || command -v python || true", timeout_s=20)
    payload["commands"]["python_probe"] = python_probe
    python_path = str(python_probe.get("stdout", "")).strip().splitlines()
    python = python_path[0] if python_path else ""
    if not python:
        payload["status"] = "integration_blocked"
        payload["reason"] = "No python executable found on Android shell. Install/enable Termux Python or use a native benchmark path."
        finish(log_dir, payload)
        return

    remote = args.remote_root.rstrip("/")
    setup_cmd = adb_shell(serial, f"rm -rf {remote} && mkdir -p {remote}/models {remote}/results", timeout_s=30)
    payload["commands"]["remote_setup"] = setup_cmd
    if setup_cmd.get("returncode") != 0:
        payload["status"] = "integration_blocked"
        payload["reason"] = "Could not prepare remote benchmark directory."
        finish(log_dir, payload)
        return

    pushes: dict[str, tuple[Path, str]] = {
        "runner": (PROJECT_ROOT / "scripts/android_ort_micrograph_runner.py", f"{remote}/android_ort_micrograph_runner.py"),
    }
    specs = model_specs(args.suite)
    for spec in specs:
        model_name = str(spec["name"])
        pushes[model_name] = (PROJECT_ROOT / "onnx_micrographs" / model_name, f"{remote}/models/{model_name}")

    for name, (local, remote_path) in pushes.items():
        cmd = run_cmd(adb_base(serial) + ["push", str(local), remote_path], timeout_s=60)
        payload["commands"][f"push_{name}"] = cmd
        if cmd.get("returncode") != 0:
            payload["status"] = "integration_blocked"
            payload["reason"] = f"adb push failed for {name}"
            finish(log_dir, payload)
            return

    provider_attempts = [provider.strip() for provider in args.providers.split(",") if provider.strip()]
    run_results: list[dict[str, object]] = []
    for provider in provider_attempts:
        for spec in specs:
            kind = str(spec["kind"])
            model_name = str(spec["name"])
            input_dim = int(spec["input_dim"])
            output_dim = int(spec["output_dim"])
            remote_out = f"{remote}/results/{provider}_{Path(model_name).stem}"
            remote_model = f"{remote}/models/{model_name}"
            cmdline = (
                f"{python} {remote}/android_ort_micrograph_runner.py "
                f"--model {remote_model} --kind {kind} --out-dir {remote_out} "
                f"--providers {provider} --warmup {args.warmup} --runs {args.runs} "
                f"--input-dim {input_dim} --output-dim {output_dim}"
            )
            cmd = adb_shell(serial, cmdline, timeout_s=180)
            key = f"run_{provider}_{kind}"
            payload["commands"][key] = cmd
            run_results.append(
                {
                    "provider": provider,
                    "kind": kind,
                    "model_name": model_name,
                    "input_dim": input_dim,
                    "output_dim": output_dim,
                    "returncode": cmd.get("returncode"),
                    "stdout": str(cmd.get("stdout", "")).strip(),
                    "stderr": str(cmd.get("stderr", "")).strip(),
                }
            )

    pull_cmd = run_cmd(adb_base(serial) + ["pull", f"{remote}/results", str(log_dir / "results")], timeout_s=120)
    payload["commands"]["pull_results"] = pull_cmd
    payload["run_results"] = run_results
    completed = [row for row in run_results if '"status": "completed"' in str(row.get("stdout", ""))]
    skipped = [row for row in run_results if '"status": "skipped"' in str(row.get("stdout", ""))]
    payload["completed_runs"] = len(completed)
    payload["skipped_runs"] = len(skipped)
    payload["status"] = "completed" if completed else "attempted_but_not_used"
    if not completed:
        payload["reason"] = "No provider/model attempt completed. See command stdout/stderr and pulled result summaries."
    finish(log_dir, payload)


if __name__ == "__main__":
    main()
