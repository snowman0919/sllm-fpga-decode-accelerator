#!/usr/bin/env python3

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from inspect_hf_model_dir import inspect_model_dir


DEFAULT_MODEL_DIR = Path("/home/monad/develop/ai_accel/gemma3-1B")
DEFAULT_OUT_DIR = Path("/home/monad/develop/ai_accel/gemma3-1B-onnx")
DEFAULT_TASK = "text-generation-with-past"
DEFAULT_OPSET = 17
DEFAULT_DEVICE = "cpu"
REQUIRED_MODULES = ["transformers", "torch", "safetensors", "onnx", "onnxruntime"]
SUPPORT_MODULES = ["psutil"]
OPTIMUM_MODULE = "optimum"
OPTIMUM_ONNX_MODULE = "optimum.exporters.onnx"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preflight and optionally export a raw Gemma HF directory to ONNX.")
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR, help="Path to the raw Hugging Face model directory.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Directory for exported ONNX artifacts.")
    parser.add_argument("--task", default=DEFAULT_TASK, help="Optimum ONNX export task, for example text-generation-with-past.")
    parser.add_argument("--opset", type=int, default=DEFAULT_OPSET, help="Target ONNX opset.")
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="Export device, usually cpu.")
    parser.add_argument("--dry-run", action="store_true", help="Print the export plan without running the export.")
    return parser.parse_args()


def module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def find_optimum_cli() -> str | None:
    path_hit = shutil.which("optimum-cli")
    if path_hit:
        return path_hit
    fallback = repo_root() / ".venv-onnx-export" / "bin" / "optimum-cli"
    if fallback.is_file():
        return str(fallback.resolve())
    return None


def cli_supports_onnx_export(optimum_cli: str | None) -> bool:
    if not optimum_cli:
        return False
    completed = subprocess.run(
        [optimum_cli, "export", "--help"],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return False
    help_text = "\n".join([completed.stdout, completed.stderr]).lower()
    return "onnx" in help_text


def python_modules_status(python_executable: str, modules: list[str]) -> dict[str, bool]:
    code = (
        "import importlib.util, json\n"
        f"mods = {modules!r}\n"
        "print(json.dumps({name: bool(importlib.util.find_spec(name)) for name in mods}))\n"
    )
    completed = subprocess.run(
        [python_executable, "-c", code],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return {name: False for name in modules}
    try:
        parsed = json.loads(completed.stdout.strip())
    except json.JSONDecodeError:
        return {name: False for name in modules}
    return {name: bool(parsed.get(name, False)) for name in modules}


def build_clean_python_env(python_executable: str | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    if python_executable:
        python_path = Path(python_executable).resolve()
        bin_dir = str(python_path.parent)
        env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
        if python_path.parent.parent.name:
            env["VIRTUAL_ENV"] = str(python_path.parent.parent)
    return env


def detect_optimum_cli_python(optimum_cli: str | None) -> str | None:
    if not optimum_cli:
        return None
    cli_path = Path(optimum_cli)
    if not cli_path.is_file():
        return None
    try:
        first_line = cli_path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except IndexError:
        return None
    if not first_line.startswith("#!"):
        return None
    shebang = first_line[2:].strip()
    return shebang or None


def package_status() -> dict[str, Any]:
    optimum_cli = find_optimum_cli()
    cli_python = detect_optimum_cli_python(optimum_cli)
    return {
        "current_python": sys.executable,
        "required_modules": {name: module_available(name) for name in REQUIRED_MODULES},
        "support_modules": {name: module_available(name) for name in SUPPORT_MODULES},
        "optimum_module": module_available(OPTIMUM_MODULE),
        "optimum_cli": optimum_cli,
        "optimum_cli_supports_onnx_export": cli_supports_onnx_export(optimum_cli),
        "python_onnx_export_module": module_available(OPTIMUM_ONNX_MODULE),
        "optimum_cli_python": cli_python,
        "cli_required_modules": python_modules_status(cli_python, REQUIRED_MODULES + [OPTIMUM_MODULE, OPTIMUM_ONNX_MODULE]) if cli_python else {},
        "cli_support_modules": python_modules_status(cli_python, SUPPORT_MODULES) if cli_python else {},
    }


def build_export_command(cli_executable: str, model_dir: Path, out_dir: Path, task: str, opset: int, device: str) -> list[str]:
    return [
        cli_executable,
        "export",
        "onnx",
        "--model",
        str(model_dir),
        "--task",
        task,
        "--opset",
        str(opset),
        "--device",
        device,
        str(out_dir),
    ]


def build_module_fallback_command(model_dir: Path, out_dir: Path, task: str, opset: int, device: str) -> list[str]:
    return [
        sys.executable,
        "-m",
        "optimum.exporters.onnx",
        "--model",
        str(model_dir),
        "--task",
        task,
        "--opset",
        str(opset),
        "--device",
        device,
        str(out_dir),
    ]


def print_plan(plan: dict[str, Any]) -> None:
    print(json.dumps(plan, indent=2))
    if plan.get("next_actions"):
        print("\nNext actions:")
        for action in plan["next_actions"]:
            print(f"- {action}")


def collect_export_outputs(out_dir: Path) -> dict[str, Any]:
    onnx_files = sorted(str(path.resolve()) for path in out_dir.rglob("*.onnx"))
    external_data_files = sorted(
        str(path.resolve())
        for path in out_dir.rglob("*")
        if path.is_file() and (path.suffix.lower() in {".data", ".onnx_data"} or path.name.endswith(".onnx_data"))
    )
    copied_support_files = {
        name: (out_dir / name).is_file()
        for name in [
            "config.json",
            "generation_config.json",
            "tokenizer.json",
            "tokenizer.model",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "added_tokens.json",
        ]
    }
    return {
        "onnx_files": onnx_files,
        "external_data_files": external_data_files,
        "copied_support_files": copied_support_files,
    }


def validate_export_requirements(status: dict[str, Any]) -> list[str]:
    current_backend_ready = all(status["required_modules"].values()) and status["optimum_module"]
    cli_backend_ready = bool(status["optimum_cli"]) and all(
        status["cli_required_modules"].get(name, False)
        for name in REQUIRED_MODULES + [OPTIMUM_MODULE, OPTIMUM_ONNX_MODULE]
    ) and status["optimum_cli_supports_onnx_export"]
    module_backend_ready = all(status["required_modules"].values()) and status["python_onnx_export_module"]

    if current_backend_ready or cli_backend_ready or module_backend_ready:
        return []

    missing: list[str] = []

    if status["optimum_cli"]:
        for name in REQUIRED_MODULES + [OPTIMUM_MODULE]:
            if not status["cli_required_modules"].get(name, False):
                missing.append(f"{name} (missing from optimum-cli backend)")
        if not status["optimum_cli_supports_onnx_export"]:
            missing.append("optimum-onnx exporter support for optimum-cli")
        if not status["cli_required_modules"].get(OPTIMUM_ONNX_MODULE, False):
            missing.append("optimum.exporters.onnx module (missing from optimum-cli backend)")
        return missing

    missing.extend(name for name, available in status["required_modules"].items() if not available)
    if not status["optimum_module"]:
        missing.append("optimum")
    if not status["python_onnx_export_module"]:
        missing.append("optimum.exporters.onnx module")
    return missing


def run_export(args: argparse.Namespace, status: dict[str, Any]) -> dict[str, Any]:
    cli_executable = status["optimum_cli"] or "optimum-cli"
    cli_cmd = build_export_command(cli_executable, args.model_dir, args.out_dir, args.task, args.opset, args.device)
    module_python = status["optimum_cli_python"] if status.get("cli_required_modules", {}).get(OPTIMUM_ONNX_MODULE, False) else sys.executable
    module_cmd = [
        module_python,
        "-m",
        "optimum.exporters.onnx",
        "--model",
        str(args.model_dir),
        "--task",
        args.task,
        "--opset",
        str(args.opset),
        "--device",
        args.device,
        str(args.out_dir),
    ]
    cli_env = build_clean_python_env(status.get("optimum_cli_python"))
    module_env = build_clean_python_env(module_python)

    if status["optimum_cli"] and status["optimum_cli_supports_onnx_export"]:
        completed = subprocess.run(cli_cmd, capture_output=True, text=True, env=cli_env)
        if completed.returncode == 0:
            return {"command": cli_cmd, "stdout": completed.stdout, "stderr": completed.stderr}
        cli_failure = {
            "command": cli_cmd,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "returncode": completed.returncode,
            "python_env_cleanup": {"PYTHONPATH": None, "PYTHONHOME": None},
        }
    else:
        cli_failure = {"command": cli_cmd, "stderr": "optimum-cli not found on PATH", "stdout": "", "returncode": None}

    completed = subprocess.run(module_cmd, capture_output=True, text=True, env=module_env)
    if completed.returncode == 0:
        return {"command": module_cmd, "stdout": completed.stdout, "stderr": completed.stderr}

    raise RuntimeError(
        "ONNX export failed with both Optimum CLI and Python module fallback.\n"
        f"CLI attempt: {json.dumps(cli_failure, indent=2)}\n"
        f"Module attempt: {json.dumps({'command': module_cmd, 'stdout': completed.stdout, 'stderr': completed.stderr, 'returncode': completed.returncode}, indent=2)}"
    )


def main() -> None:
    args = parse_args()
    inspection = inspect_model_dir(args.model_dir)
    status = package_status()
    cli_cmd = build_export_command(status["optimum_cli"] or "optimum-cli", args.model_dir, args.out_dir, args.task, args.opset, args.device)
    module_python = status["optimum_cli_python"] if status.get("cli_required_modules", {}).get(OPTIMUM_ONNX_MODULE, False) else sys.executable
    module_cmd = [
        module_python,
        "-m",
        "optimum.exporters.onnx",
        "--model",
        str(args.model_dir),
        "--task",
        args.task,
        "--opset",
        str(args.opset),
        "--device",
        args.device,
        str(args.out_dir),
    ]

    plan = {
        "model_dir": str(args.model_dir.resolve()),
        "out_dir": str(args.out_dir.resolve()),
        "task": args.task,
        "opset": args.opset,
        "device": args.device,
        "dry_run": args.dry_run,
        "hf_model_inspection_passed": inspection["inspection_passed"],
        "hf_model_missing_items": inspection["missing_required_items"],
        "package_status": status,
        "preferred_export_command": cli_cmd,
        "python_module_fallback_command": module_cmd,
        "next_actions": [],
    }

    if not inspection["inspection_passed"]:
        plan["next_actions"].append("Fix the missing Hugging Face model files before attempting export.")
        print_plan(plan)
        raise SystemExit("HF model directory preflight failed. Resolve the missing files and rerun.")

    missing_packages = validate_export_requirements(status)
    if missing_packages:
        plan["next_actions"].append(
            "Install the export dependencies in a dedicated venv, for example: "
            "python3 -m venv .venv-onnx-export && . .venv-onnx-export/bin/activate && pip install -r onnx_profile/requirements.txt"
        )
        plan["next_actions"].append(
            "If optimum-cli exists but lacks the ONNX exporter subcommand, install ONNX export support explicitly with: "
            "pip install 'optimum[onnxruntime]' or pip install 'optimum-onnx[onnxruntime]'"
        )
        plan["next_actions"].append("Re-run the dry-run command to verify that transformers, optimum, torch, safetensors, onnx, onnxruntime, and psutil are visible.")
        plan["missing_packages"] = missing_packages
        if args.dry_run:
            print_plan(plan)
            return
        print_plan(plan)
        raise SystemExit(f"Export dependencies are missing: {', '.join(missing_packages)}")

    plan["next_actions"].append("Verify after export that the ONNX graph exposes past/present cache inputs and outputs if decode cache reuse profiling is required.")
    plan["next_actions"].append(f"After export, inspect the graph with: python3 onnx_profile/inspect_onnx_model.py --model {args.out_dir / 'model.onnx'} --out-dir onnx_profile/results")

    if args.dry_run:
        print_plan(plan)
        return

    args.out_dir.mkdir(parents=True, exist_ok=True)
    export_result = run_export(args, status)
    export_outputs = collect_export_outputs(args.out_dir)
    plan["executed_command"] = export_result["command"]
    plan["export_stdout"] = export_result["stdout"]
    plan["export_stderr"] = export_result["stderr"]
    plan["export_outputs"] = export_outputs

    if not export_outputs["onnx_files"]:
        print_plan(plan)
        raise SystemExit("Export command completed but no .onnx file was found in the output directory.")

    primary_model = Path(export_outputs["onnx_files"][0])
    from inspect_onnx_model import inspect_onnx_model, write_outputs as write_onnx_outputs

    onnx_report = inspect_onnx_model(primary_model)
    write_onnx_outputs(onnx_report, Path("onnx_profile/results"), primary_model)
    plan["onnx_inspection"] = {
        "model": onnx_report["model_path"],
        "decode_cache_reuse_ready": onnx_report["decode_cache_reuse_ready"],
        "cache_input_names": onnx_report["cache_input_names"],
        "cache_output_names": onnx_report["cache_output_names"],
        "has_external_data": onnx_report["has_external_data"],
    }

    print_plan(plan)


if __name__ == "__main__":
    main()
