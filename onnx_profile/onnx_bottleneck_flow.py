#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import onnx
import onnxruntime as ort

from run_profile import profile_model


DEFAULT_MODEL_DIR = Path("/home/monad/develop/ai_accel/gemma3-1B")
DEFAULT_ONNX_DIR = Path("/home/monad/develop/ai_accel/gemma3-1B-onnx")
DEFAULT_RESULTS_DIR = Path("onnx_profile/results_onnx")
DEFAULT_TABLES_DIR = Path("paper_assets/tables")
DEFAULT_REPORT_PATH = Path("onnx_profile/results/reports/onnx_bottleneck_report.md")

PRIMARY_TASK = "text-generation-with-past"
FALLBACK_TASK = "text-generation"
DEFAULT_OPSET = 17
DEFAULT_DEVICE = "cpu"

KEY_OPS = [
    "MatMul",
    "Gemm",
    "Softmax",
    "Gather",
    "Reshape",
    "Transpose",
    "Cast",
    "LayerNormalization",
    "SimplifiedLayerNormalization",
    "RMSNorm",
    "SkipSimplifiedLayerNormalization",
]
CACHE_KEYWORDS = ("past", "present", "cache", "key_values")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect ONNX export/inspection/ORT profiling artifacts for the bottleneck report.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    common.add_argument("--onnx-dir", type=Path, default=DEFAULT_ONNX_DIR)
    common.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    common.add_argument("--paper-tables-dir", type=Path, default=DEFAULT_TABLES_DIR)
    common.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)

    export_parser = subparsers.add_parser("export", parents=[common])
    export_parser.add_argument("--opset", type=int, default=DEFAULT_OPSET)
    export_parser.add_argument("--device", default=DEFAULT_DEVICE)

    inspect_parser = subparsers.add_parser("inspect", parents=[common])
    inspect_parser.add_argument("--model", type=Path, default=None)

    profile_parser = subparsers.add_parser("profile", parents=[common])
    profile_parser.add_argument("--model", type=Path, default=None)
    profile_parser.add_argument("--prompt-len", type=int, default=32)
    profile_parser.add_argument("--decode-tokens", type=int, default=2)
    profile_parser.add_argument("--cuda-prompt-len", type=int, default=8)
    profile_parser.add_argument("--cuda-decode-tokens", type=int, default=1)

    report_parser = subparsers.add_parser("report", parents=[common])
    report_parser.add_argument("--model", type=Path, default=None)

    all_parser = subparsers.add_parser("all", parents=[common])
    all_parser.add_argument("--opset", type=int, default=DEFAULT_OPSET)
    all_parser.add_argument("--device", default=DEFAULT_DEVICE)
    all_parser.add_argument("--prompt-len", type=int, default=32)
    all_parser.add_argument("--decode-tokens", type=int, default=2)
    all_parser.add_argument("--cuda-prompt-len", type=int, default=8)
    all_parser.add_argument("--cuda-decode-tokens", type=int, default=1)

    return parser.parse_args()


def ensure_dirs(results_dir: Path, paper_tables_dir: Path, report_path: Path) -> tuple[Path, Path]:
    raw_dir = results_dir / "raw"
    logs_dir = results_dir / "logs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    paper_tables_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    return raw_dir, logs_dir


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def default_model_path(args_model: Path | None, onnx_dir: Path) -> Path:
    return args_model if args_model is not None else onnx_dir / "model.onnx"


def run_and_capture(command: list[str], log_path: Path, cwd: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        env=env,
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        f"$ {' '.join(command)}\n\n[stdout]\n{completed.stdout}\n\n[stderr]\n{completed.stderr}\n",
        encoding="utf-8",
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_log": str(log_path.resolve()),
        "stdout_bytes": len(completed.stdout.encode("utf-8")),
        "stderr_bytes": len(completed.stderr.encode("utf-8")),
    }


def collect_file_size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return None


def export_attempt(
    model_dir: Path,
    onnx_dir: Path,
    results_dir: Path,
    task: str,
    opset: int,
    device: str,
    log_name: str,
) -> dict[str, Any]:
    _, logs_dir = ensure_dirs(results_dir, DEFAULT_TABLES_DIR, DEFAULT_REPORT_PATH)
    command = [
        "nix",
        "develop",
        "-c",
        "python3",
        "onnx_profile/export_gemma_to_onnx.py",
        "--model-dir",
        str(model_dir),
        "--out-dir",
        str(onnx_dir),
        "--task",
        task,
        "--opset",
        str(opset),
        "--device",
        device,
    ]
    result = run_and_capture(command, logs_dir / log_name, repo_root())
    model_path = onnx_dir / "model.onnx"
    data_path = onnx_dir / "model.onnx_data"
    result.update(
        {
            "task": task,
            "model_path": str(model_path.resolve()) if model_path.exists() else None,
            "model_exists": model_path.is_file(),
            "model_size_bytes": collect_file_size(model_path),
            "external_data_path": str(data_path.resolve()) if data_path.exists() else None,
            "external_data_exists": data_path.is_file(),
            "external_data_size_bytes": collect_file_size(data_path),
        }
    )
    return result


def export_flow(args: argparse.Namespace) -> dict[str, Any]:
    raw_dir, _ = ensure_dirs(args.results_dir, args.paper_tables_dir, args.report_path)
    status_path = raw_dir / "onnx_export_status.json"
    csv_path = args.paper_tables_dir / "onnx_export_status.csv"

    status: dict[str, Any] = {
        "model_dir": str(args.model_dir.resolve()),
        "onnx_dir": str(args.onnx_dir.resolve()),
        "requested_primary_task": PRIMARY_TASK,
        "requested_fallback_task": FALLBACK_TASK,
        "opset": args.opset,
        "device": args.device,
        "preexisting_onnx_dir": args.onnx_dir.exists(),
        "attempts": [],
        "export_success": False,
        "used_fallback": False,
        "final_task": None,
        "final_model_path": None,
        "failure_reason": None,
    }

    primary = export_attempt(
        model_dir=args.model_dir,
        onnx_dir=args.onnx_dir,
        results_dir=args.results_dir,
        task=PRIMARY_TASK,
        opset=args.opset,
        device=args.device,
        log_name="onnx_export_with_past.log",
    )
    status["attempts"].append(primary)

    primary_success = primary["returncode"] == 0 and primary["model_exists"]
    if primary_success:
        status["export_success"] = True
        status["final_task"] = PRIMARY_TASK
        status["final_model_path"] = primary["model_path"]
    else:
        fallback = export_attempt(
            model_dir=args.model_dir,
            onnx_dir=args.onnx_dir,
            results_dir=args.results_dir,
            task=FALLBACK_TASK,
            opset=args.opset,
            device=args.device,
            log_name="onnx_export_fallback.log",
        )
        status["attempts"].append(fallback)
        status["used_fallback"] = True
        fallback_success = fallback["returncode"] == 0 and fallback["model_exists"]
        if fallback_success:
            status["export_success"] = True
            status["final_task"] = FALLBACK_TASK
            status["final_model_path"] = fallback["model_path"]
        else:
            status["failure_reason"] = "Both primary and fallback export attempts failed or did not leave model.onnx."

    write_json(status_path, status)
    csv_row = {
        "model_dir": status["model_dir"],
        "onnx_dir": status["onnx_dir"],
        "primary_task": PRIMARY_TASK,
        "fallback_task": FALLBACK_TASK,
        "opset": args.opset,
        "device": args.device,
        "export_success": status["export_success"],
        "used_fallback": status["used_fallback"],
        "final_task": status["final_task"],
        "final_model_path": status["final_model_path"],
        "failure_reason": status["failure_reason"],
        "primary_returncode": primary["returncode"],
        "primary_log": primary["stdout_log"],
        "fallback_returncode": status["attempts"][1]["returncode"] if len(status["attempts"]) > 1 else None,
        "fallback_log": status["attempts"][1]["stdout_log"] if len(status["attempts"]) > 1 else None,
    }
    write_csv(csv_path, list(csv_row.keys()), [csv_row])
    return status


def tensor_shape(value_info: Any) -> list[Any]:
    shape: list[Any] = []
    tensor_type = value_info.type.tensor_type
    for dim in tensor_type.shape.dim:
        if dim.HasField("dim_value"):
            shape.append(dim.dim_value)
        elif dim.HasField("dim_param"):
            shape.append(dim.dim_param)
        else:
            shape.append("?")
    return shape


def elem_type_name(value_info: Any) -> str:
    return onnx.TensorProto.DataType.Name(value_info.type.tensor_type.elem_type)


def file_summary_for_export(model_path: Path) -> list[dict[str, Any]]:
    model_dir = model_path.parent
    rows: list[dict[str, Any]] = []
    for path in sorted(model_dir.iterdir()):
        if not path.is_file():
            continue
        rows.append(
            {
                "file_name": path.name,
                "path": str(path.resolve()),
                "size_bytes": path.stat().st_size,
                "size_mib": round(path.stat().st_size / (1024 * 1024), 3),
                "kind": "onnx_model" if path.suffix == ".onnx" else ("external_data" if "onnx_data" in path.name else "support"),
            }
        )
    return rows


def inspect_flow(args: argparse.Namespace) -> dict[str, Any]:
    raw_dir, _ = ensure_dirs(args.results_dir, args.paper_tables_dir, args.report_path)
    model_path = default_model_path(args.model, args.onnx_dir)
    status = read_json(raw_dir / "onnx_export_status.json")
    if status and status.get("final_model_path"):
        model_path = Path(status["final_model_path"])
    if not model_path.is_file():
        raise FileNotFoundError(f"ONNX model file not found for inspection: {model_path}")

    model = onnx.load(str(model_path), load_external_data=False)
    op_counter: Counter[str] = Counter(node.op_type for node in model.graph.node)
    inputs = [
        {
            "name": value.name,
            "shape": tensor_shape(value),
            "elem_type": elem_type_name(value),
        }
        for value in model.graph.input
    ]
    outputs = [
        {
            "name": value.name,
            "shape": tensor_shape(value),
            "elem_type": elem_type_name(value),
        }
        for value in model.graph.output
    ]
    cache_inputs = [item for item in inputs if any(keyword in item["name"].lower() for keyword in CACHE_KEYWORDS)]
    cache_outputs = [item for item in outputs if any(keyword in item["name"].lower() for keyword in CACHE_KEYWORDS)]
    symbolic_dims = sorted(
        {
            str(dim)
            for item in inputs + outputs
            for dim in item["shape"]
            if isinstance(dim, str)
        }
    )
    file_rows = file_summary_for_export(model_path)
    total_model_bytes = sum(int(row["size_bytes"]) for row in file_rows)

    report = {
        "model_path": str(model_path.resolve()),
        "graph_name": model.graph.name,
        "ir_version": model.ir_version,
        "opset_imports": [{"domain": item.domain or "ai.onnx", "version": item.version} for item in model.opset_import],
        "input_count": len(inputs),
        "output_count": len(outputs),
        "inputs": inputs,
        "outputs": outputs,
        "cache_input_names": [item["name"] for item in cache_inputs],
        "cache_output_names": [item["name"] for item in cache_outputs],
        "decode_cache_reuse_ready": bool(cache_inputs and cache_outputs),
        "has_external_data": any(row["kind"] == "external_data" for row in file_rows),
        "external_data_files": [row["path"] for row in file_rows if row["kind"] == "external_data"],
        "total_node_count": len(model.graph.node),
        "total_initializer_count": len(model.graph.initializer),
        "operator_histogram": dict(sorted(op_counter.items(), key=lambda item: (-item[1], item[0]))),
        "key_operator_counts": {name: op_counter.get(name, 0) for name in KEY_OPS},
        "has_symbolic_shapes": bool(symbolic_dims),
        "symbolic_dims": symbolic_dims,
        "model_files": file_rows,
        "total_model_bytes": total_model_bytes,
    }

    json_path = raw_dir / "onnx_graph_inspection.json"
    write_json(json_path, report)

    io_rows: list[dict[str, Any]] = []
    for io_type, items in (("input", inputs), ("output", outputs)):
        for item in items:
            io_rows.append(
                {
                    "io_type": io_type,
                    "name": item["name"],
                    "elem_type": item["elem_type"],
                    "shape": json.dumps(item["shape"], ensure_ascii=True),
                    "is_cache_io": any(keyword in item["name"].lower() for keyword in CACHE_KEYWORDS),
                }
            )
    write_csv(
        args.paper_tables_dir / "onnx_graph_io_summary.csv",
        ["io_type", "name", "elem_type", "shape", "is_cache_io"],
        io_rows,
    )

    histogram_rows = [
        {"op_type": op_type, "count": count, "is_key_op": op_type in KEY_OPS}
        for op_type, count in sorted(op_counter.items(), key=lambda item: (-item[1], item[0]))
    ]
    write_csv(
        args.paper_tables_dir / "onnx_operator_histogram.csv",
        ["op_type", "count", "is_key_op"],
        histogram_rows,
    )

    write_csv(
        args.paper_tables_dir / "onnx_model_file_summary.csv",
        ["file_name", "path", "size_bytes", "size_mib", "kind"],
        file_rows,
    )

    return report


def summarize_ort_trace(profile_json_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not profile_json_path.is_file():
        return [], []
    raw = json.loads(profile_json_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return [], []

    op_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "total_dur_us": 0.0, "provider_counts": Counter()})
    provider_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"node_count": 0, "total_dur_us": 0.0})

    for event in raw:
        if not isinstance(event, dict):
            continue
        if event.get("cat") != "Node":
            continue
        args = event.get("args", {})
        op_name = args.get("op_name") or event.get("name") or "UNKNOWN"
        provider = args.get("provider") or "UNKNOWN"
        dur = float(event.get("dur", 0.0))

        entry = op_stats[op_name]
        entry["count"] += 1
        entry["total_dur_us"] += dur
        entry["provider_counts"][provider] += 1

        provider_entry = provider_stats[provider]
        provider_entry["node_count"] += 1
        provider_entry["total_dur_us"] += dur

    op_rows = []
    for op_name, stats in sorted(op_stats.items(), key=lambda item: (-item[1]["total_dur_us"], item[0])):
        op_rows.append(
            {
                "op_type": op_name,
                "count": stats["count"],
                "total_dur_us": round(stats["total_dur_us"], 3),
                "avg_dur_us": round(stats["total_dur_us"] / stats["count"], 3) if stats["count"] else None,
                "providers": "; ".join(f"{name}:{count}" for name, count in sorted(stats["provider_counts"].items())),
            }
        )

    provider_rows = []
    for provider, stats in sorted(provider_stats.items(), key=lambda item: (-item[1]["total_dur_us"], item[0])):
        provider_rows.append(
            {
                "provider": provider,
                "node_count": stats["node_count"],
                "total_dur_us": round(stats["total_dur_us"], 3),
                "avg_dur_us": round(stats["total_dur_us"] / stats["node_count"], 3) if stats["node_count"] else None,
            }
        )

    return op_rows, provider_rows


def profile_provider(model_path: Path, provider: str, prompt_len: int, decode_tokens: int, raw_dir: Path) -> dict[str, Any]:
    try:
        summary = profile_model(
            model_path=model_path,
            provider=provider,
            prompt_len=prompt_len,
            decode_tokens=decode_tokens,
            out_dir=raw_dir,
            enable_profile=(provider == "CPUExecutionProvider"),
        )
        return {
            "status": "ok",
            "provider": provider,
            "prompt_len": prompt_len,
            "decode_tokens": decode_tokens,
            "summary": summary,
            "error": None,
        }
    except Exception as exc:  # pragma: no cover - runtime artifact path
        return {
            "status": "failed",
            "provider": provider,
            "prompt_len": prompt_len,
            "decode_tokens": decode_tokens,
            "summary": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def profile_flow(args: argparse.Namespace) -> dict[str, Any]:
    raw_dir, _ = ensure_dirs(args.results_dir, args.paper_tables_dir, args.report_path)
    model_path = default_model_path(args.model, args.onnx_dir)
    export_status = read_json(raw_dir / "onnx_export_status.json")
    if export_status and export_status.get("final_model_path"):
        model_path = Path(export_status["final_model_path"])
    if not model_path.is_file():
        raise FileNotFoundError(f"ONNX model file not found for profiling: {model_path}")

    available_providers = ort.get_available_providers()
    status: dict[str, Any] = {
        "model_path": str(model_path.resolve()),
        "available_providers": available_providers,
        "cpu_attempt": None,
        "cuda_attempt": None,
        "profiling_blocked": False,
        "profiling_blocked_reason": None,
    }

    cpu_attempt = profile_provider(model_path, "CPUExecutionProvider", args.prompt_len, args.decode_tokens, raw_dir)
    status["cpu_attempt"] = cpu_attempt

    cpu_summary = cpu_attempt.get("summary") or {}
    profiling_json_path = None
    if cpu_attempt["status"] == "ok":
        profiling_json_value = cpu_summary.get("profiling_json")
        if profiling_json_value:
            profiling_json_path = Path(profiling_json_value)
            fixed_copy = raw_dir / "ort_profile_cpu.json"
            if profiling_json_path.is_file():
                shutil.copyfile(profiling_json_path, fixed_copy)
                status["cpu_attempt"]["profiling_json_original"] = str(profiling_json_path.resolve())
                status["cpu_attempt"]["profiling_json_copy"] = str(fixed_copy.resolve())
                profiling_json_path = fixed_copy
        if cpu_summary.get("note"):
            status["profiling_blocked"] = True
            status["profiling_blocked_reason"] = cpu_summary["note"]
    else:
        status["profiling_blocked"] = True
        status["profiling_blocked_reason"] = cpu_attempt["error"]

    if "CUDAExecutionProvider" in available_providers:
        status["cuda_attempt"] = profile_provider(
            model_path,
            "CUDAExecutionProvider",
            args.cuda_prompt_len,
            args.cuda_decode_tokens,
            raw_dir,
        )
    else:
        status["cuda_attempt"] = {
            "status": "skipped",
            "provider": "CUDAExecutionProvider",
            "reason": "CUDAExecutionProvider not available in this onnxruntime build.",
        }

    write_json(raw_dir / "ort_profile_status.json", status)

    session_rows = []
    for label, attempt in (("cpu", status["cpu_attempt"]), ("cuda", status["cuda_attempt"])):
        if not isinstance(attempt, dict):
            continue
        summary = attempt.get("summary") or {}
        session_rows.append(
            {
                "attempt": label,
                "provider": attempt.get("provider"),
                "status": attempt.get("status"),
                "prompt_len": attempt.get("prompt_len"),
                "decode_tokens": attempt.get("decode_tokens"),
                "session_init_s": summary.get("session_init_s"),
                "prefill_s": summary.get("prefill_s"),
                "decode_avg_s": summary.get("decode_avg_s"),
                "decode_mode": summary.get("decode_mode"),
                "cache_input_count": len(summary.get("cache_io", {}).get("cache_input_names", [])),
                "cache_output_count": len(summary.get("cache_io", {}).get("cache_output_names", [])),
                "note_or_error": summary.get("note") or attempt.get("error") or attempt.get("reason"),
            }
        )
    write_csv(
        args.paper_tables_dir / "ort_session_summary.csv",
        list(session_rows[0].keys()) if session_rows else ["attempt"],
        session_rows or [{"attempt": "none"}],
    )

    op_rows, provider_rows = summarize_ort_trace(profiling_json_path) if profiling_json_path else ([], [])
    write_csv(
        args.paper_tables_dir / "ort_operator_latency_summary.csv",
        ["op_type", "count", "total_dur_us", "avg_dur_us", "providers"],
        op_rows,
    )
    write_csv(
        args.paper_tables_dir / "ort_provider_summary.csv",
        ["provider", "node_count", "total_dur_us", "avg_dur_us"],
        provider_rows,
    )

    return status


def candidate_bottlenecks(
    inspection: dict[str, Any] | None,
    ort_status: dict[str, Any] | None,
    export_status: dict[str, Any] | None,
    ort_op_rows: list[dict[str, str]] | None = None,
) -> list[str]:
    findings: list[str] = []
    if export_status and not export_status.get("export_success"):
        findings.append("Export path itself is a blocking bottleneck candidate because ONNX generation did not complete cleanly.")
    if inspection:
        if inspection.get("has_external_data"):
            findings.append("The model uses external ONNX data, so model packaging and model-loading I/O are practical bottleneck candidates.")
        if inspection.get("cache_input_names") and inspection.get("cache_output_names"):
            findings.append("Cache-related graph I/O exists, so decode-stage cache handling is measurable and remains a candidate rather than an assumption.")
        top_ops = list(inspection.get("operator_histogram", {}).items())[:5]
        if top_ops:
            findings.append(
                "High-frequency graph operators include "
                + ", ".join(f"{name} ({count})" for name, count in top_ops)
                + "."
            )
    if ort_status:
        cpu_attempt = ort_status.get("cpu_attempt") or {}
        summary = cpu_attempt.get("summary") or {}
        if cpu_attempt.get("status") == "ok":
            if summary.get("session_init_s") is not None:
                findings.append(f"Session initialization on CPU is measurable ({summary['session_init_s']:.3f}s) and is one host-side overhead candidate.")
            if summary.get("prefill_s") is not None:
                findings.append(f"Prefill latency on CPU is measurable ({summary['prefill_s']:.3f}s) and is a direct runtime bottleneck candidate.")
            if summary.get("decode_avg_s") is not None:
                findings.append(f"Per-step decode latency on CPU is measurable ({summary['decode_avg_s']:.3f}s average for this short run).")
        if ort_op_rows:
            top_row = ort_op_rows[0]
            findings.append(
                "In the ORT node trace, "
                f"{top_row['op_type']} has the largest accumulated duration "
                f"({top_row['total_dur_us']} us across {top_row['count']} node executions), "
                "so dense linear algebra is an immediate runtime hotspot candidate."
            )
        if ort_status.get("profiling_blocked"):
            findings.append(f"Detailed profiling is partially blocked: {ort_status.get('profiling_blocked_reason')}")
    return findings


def report_flow(args: argparse.Namespace) -> Path:
    raw_dir, _ = ensure_dirs(args.results_dir, args.paper_tables_dir, args.report_path)
    export_status = read_json(raw_dir / "onnx_export_status.json")
    inspection = read_json(raw_dir / "onnx_graph_inspection.json")
    ort_status = read_json(raw_dir / "ort_profile_status.json")
    ort_op_rows = read_csv_rows(args.paper_tables_dir / "ort_operator_latency_summary.csv")

    lines: list[str] = []
    lines.append("# ONNX Bottleneck Report")
    lines.append("")
    lines.append("## Export Status")
    lines.append("")
    if export_status:
        lines.append(f"- Export success: `{export_status.get('export_success')}`")
        lines.append(f"- Fallback used: `{export_status.get('used_fallback')}`")
        lines.append(f"- Final task: `{export_status.get('final_task')}`")
        lines.append(f"- Final model path: `{export_status.get('final_model_path')}`")
        if export_status.get("failure_reason"):
            lines.append(f"- Failure reason: {export_status['failure_reason']}")
    else:
        lines.append("- Export status JSON is missing.")

    lines.append("")
    lines.append("## Graph Inspection")
    lines.append("")
    if inspection:
        lines.append(f"- Model path: `{inspection.get('model_path')}`")
        lines.append(f"- External data: `{inspection.get('has_external_data')}`")
        lines.append(f"- Total model bytes: `{inspection.get('total_model_bytes')}`")
        lines.append(f"- Inputs / outputs: `{inspection.get('input_count')}` / `{inspection.get('output_count')}`")
        lines.append(f"- Cache I/O present: `{inspection.get('decode_cache_reuse_ready')}`")
        lines.append(f"- Cache input count: `{len(inspection.get('cache_input_names', []))}`")
        lines.append(f"- Cache output count: `{len(inspection.get('cache_output_names', []))}`")
        lines.append(f"- Symbolic shapes present: `{inspection.get('has_symbolic_shapes')}`")
        top_ops = list(inspection.get("operator_histogram", {}).items())[:10]
        if top_ops:
            lines.append("- Top operators: " + ", ".join(f"`{name}`={count}" for name, count in top_ops))
    else:
        lines.append("- Graph inspection JSON is missing.")

    lines.append("")
    lines.append("## ORT Profiling")
    lines.append("")
    if ort_status:
        cpu_attempt = ort_status.get("cpu_attempt") or {}
        cpu_summary = cpu_attempt.get("summary") or {}
        lines.append(f"- CPU attempt status: `{cpu_attempt.get('status')}`")
        lines.append(f"- CPU session init time: `{cpu_summary.get('session_init_s')}`")
        lines.append(f"- CPU prefill latency: `{cpu_summary.get('prefill_s')}`")
        lines.append(f"- CPU decode average latency: `{cpu_summary.get('decode_avg_s')}`")
        lines.append(f"- CPU decode mode: `{cpu_summary.get('decode_mode')}`")
        if ort_op_rows:
            top_runtime_ops = ort_op_rows[:5]
            lines.append(
                "- Top traced runtime ops: "
                + ", ".join(
                    f"`{row['op_type']}`={row['total_dur_us']}us/{row['count']} calls"
                    for row in top_runtime_ops
                )
            )
        lines.append(f"- Profiling blocked: `{ort_status.get('profiling_blocked')}`")
        if ort_status.get("profiling_blocked_reason"):
            lines.append(f"- Blocked reason: {ort_status['profiling_blocked_reason']}")
        cuda_attempt = ort_status.get("cuda_attempt") or {}
        lines.append(f"- CUDA attempt status: `{cuda_attempt.get('status')}`")
        if cuda_attempt.get("error") or cuda_attempt.get("reason"):
            lines.append(f"- CUDA note: {cuda_attempt.get('error') or cuda_attempt.get('reason')}")
    else:
        lines.append("- ORT profile status JSON is missing.")

    lines.append("")
    lines.append("## Current Bottleneck Candidates")
    lines.append("")
    findings = candidate_bottlenecks(inspection, ort_status, export_status, ort_op_rows)
    if findings:
        for item in findings:
            lines.append(f"- {item}")
    else:
        lines.append("- No evidence-backed candidate could be extracted from the current artifacts.")

    lines.append("")
    lines.append("## Still Unconfirmed")
    lines.append("")
    lines.append("- Whole-model bottleneck ranking across export, graph structure, runtime, memory pressure, prefill, and decode is not yet fully resolved from this minimal run.")
    lines.append("- Cache-related memory pressure remains a candidate factor, but not a confirmed sole bottleneck.")
    lines.append("- CUDA-side ONNX Runtime behavior should not be inferred if the CUDA provider was unavailable or failed to initialize.")

    lines.append("")
    lines.append("## Evidence Positioning")
    lines.append("")
    lines.append("- PyTorch CPU/CUDA context sweep data remains a host-side reference baseline and is not reported here as ONNX Runtime profiling.")
    lines.append("- FPGA results remain primitive-level validation for the INT8 QK dot-product block and are not used here as end-to-end ONNX Runtime acceleration evidence.")

    args.report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return args.report_path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> None:
    args = parse_args()

    if args.command == "export":
        result = export_flow(args)
        print(json.dumps(result, indent=2))
        return

    if args.command == "inspect":
        result = inspect_flow(args)
        print(json.dumps(result, indent=2))
        return

    if args.command == "profile":
        result = profile_flow(args)
        print(json.dumps(result, indent=2))
        return

    if args.command == "report":
        path = report_flow(args)
        print(path)
        return

    if args.command == "all":
        export_status = export_flow(args)
        if export_status.get("export_success"):
            inspect_flow(args)
            profile_flow(args)
        report_path = report_flow(args)
        print(json.dumps({"export_success": export_status.get("export_success"), "report_path": str(report_path.resolve())}, indent=2))
        return


if __name__ == "__main__":
    main()
