#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import shutil
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import onnxruntime as ort

from run_profile import (
    build_decode_inputs,
    build_prefill_inputs,
    classify_session_io,
    describe_session,
    map_cache_outputs,
    model_exists,
)


DEFAULT_MODEL = Path("/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx")
DEFAULT_OUT_DIR = Path("onnx_profile/results_onnx_sweep")
DEFAULT_TABLES_DIR = Path("paper_assets/tables")
DEFAULT_FIGURES_DIR = Path("paper_assets/figures")
DEFAULT_REPORT = Path("onnx_profile/results/reports/onnx_runtime_sweep_report.md")
DEFAULT_CONTEXTS = [128, 512, 1024, 2048]
DEFAULT_DECODE_STEPS = [1, 2, 4, 8]
FOCUS_OPS = {
    "MatMul": "MatMul",
    "SimplifiedLayerNormalization": "SimplifiedLayerNormalization",
    "Mul": "Mul",
    "Gather": "Gather",
    "Cast": "Cast",
    "Reshape": "Reshape/Transpose",
    "Transpose": "Reshape/Transpose",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CPUExecutionProvider ONNX Runtime context/decode sweep with phase-level operator profiling.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    common.add_argument("--provider", default="CPUExecutionProvider")
    common.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    common.add_argument("--paper-tables-dir", type=Path, default=DEFAULT_TABLES_DIR)
    common.add_argument("--paper-figures-dir", type=Path, default=DEFAULT_FIGURES_DIR)
    common.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)

    sweep = subparsers.add_parser("sweep", parents=[common])
    sweep.add_argument("--context-lengths", type=int, nargs="+", default=DEFAULT_CONTEXTS)
    sweep.add_argument("--decode-steps", type=int, nargs="+", default=DEFAULT_DECODE_STEPS)
    sweep.add_argument("--runs", type=int, default=3)
    sweep.add_argument("--warmup-runs", type=int, default=1)

    report = subparsers.add_parser("report", parents=[common])
    report.add_argument("--context-lengths", type=int, nargs="+", default=DEFAULT_CONTEXTS)
    report.add_argument("--decode-steps", type=int, nargs="+", default=DEFAULT_DECODE_STEPS)
    return parser.parse_args()


def ensure_dirs(args: argparse.Namespace) -> Path:
    raw_dir = args.out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    args.paper_tables_dir.mkdir(parents=True, exist_ok=True)
    args.paper_figures_dir.mkdir(parents=True, exist_ok=True)
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    return raw_dir


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def make_session(model_path: Path, provider: str, profile_prefix: Path | None = None) -> ort.InferenceSession:
    options = ort.SessionOptions()
    if profile_prefix is not None:
        options.enable_profiling = True
        options.profile_file_prefix = str(profile_prefix)
    return ort.InferenceSession(str(model_path), sess_options=options, providers=[provider])


def mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def p50(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def stdev(values: list[float]) -> float | None:
    if not values:
        return None
    return statistics.stdev(values) if len(values) > 1 else 0.0


def copy_profile(raw_path: str, stable_path: Path) -> str:
    source = Path(raw_path)
    if source.resolve() != stable_path.resolve():
        shutil.copyfile(source, stable_path)
        source.unlink(missing_ok=True)
    return str(stable_path.resolve())


def io_summary(session: ort.InferenceSession) -> dict[str, Any]:
    info = classify_session_io(session)
    return {
        "decode_input_generation_possible": not info["unsupported_inputs"] and bool(info["cache_inputs"] and info["cache_outputs"]),
        "unsupported_inputs": [{"name": meta.name, "type": meta.type, "shape": list(meta.shape)} for meta in info["unsupported_inputs"]],
        "cache_input_count": len(info["cache_inputs"]),
        "cache_output_count": len(info["cache_outputs"]),
        "cache_inputs": [{"name": meta.name, "type": meta.type, "shape": list(meta.shape)} for meta in info["cache_inputs"]],
        "cache_outputs": [{"name": meta.name, "type": meta.type, "shape": list(meta.shape)} for meta in info["cache_outputs"]],
    }


def summarize_profile(profile_path: Path) -> list[dict[str, Any]]:
    events = json.loads(profile_path.read_text(encoding="utf-8"))
    stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "total_us": 0.0, "providers": Counter()})
    for event in events:
        if not isinstance(event, dict) or event.get("cat") != "Node":
            continue
        args = event.get("args", {})
        op_type = args.get("op_name") or event.get("name") or "UNKNOWN"
        provider = args.get("provider") or "UNKNOWN"
        duration_us = float(event.get("dur", 0.0))
        stats[op_type]["count"] += 1
        stats[op_type]["total_us"] += duration_us
        stats[op_type]["providers"][provider] += 1
    return [
        {
            "op_type": op_type,
            "call_count": item["count"],
            "total_us": item["total_us"],
            "mean_us": item["total_us"] / item["count"] if item["count"] else None,
            "provider": "; ".join(sorted(item["providers"])),
        }
        for op_type, item in sorted(stats.items(), key=lambda pair: (-pair[1]["total_us"], pair[0]))
    ]


def run_prefill(model_path: Path, provider: str, context_length: int, profile_prefix: Path | None) -> dict[str, Any]:
    session = make_session(model_path, provider, profile_prefix)
    info = classify_session_io(session)
    inputs = build_prefill_inputs(session, context_length, info)
    start = time.perf_counter()
    outputs = session.run(None, inputs)
    elapsed_s = time.perf_counter() - start
    profile_json = None
    if profile_prefix is not None:
        profile_json = copy_profile(session.end_profiling(), profile_prefix.with_suffix(".json"))
    return {
        "elapsed_s": elapsed_s,
        "profile_json": profile_json,
        "cache_tensors": map_cache_outputs(info, outputs),
        "io_summary": io_summary(session),
    }


def run_decode(
    model_path: Path,
    provider: str,
    context_length: int,
    decode_steps: int,
    cache_tensors: dict[str, np.ndarray],
    profile_prefix: Path | None,
) -> dict[str, Any]:
    session = make_session(model_path, provider, profile_prefix)
    info = classify_session_io(session)
    cache_enabled = bool(info["cache_inputs"] and info["cache_outputs"])
    current_cache = dict(cache_tensors)
    step_latencies: list[float] = []
    for step in range(decode_steps):
        inputs = build_decode_inputs(
            session=session,
            prefill_inputs={},
            io_info=info,
            prompt_len=context_length,
            step=step,
            cache_tensors=current_cache,
            cache_enabled=cache_enabled,
        )
        start = time.perf_counter()
        outputs = session.run(None, inputs)
        step_latencies.append(time.perf_counter() - start)
        if cache_enabled:
            current_cache = map_cache_outputs(info, outputs)
    profile_json = None
    if profile_prefix is not None:
        profile_json = copy_profile(session.end_profiling(), profile_prefix.with_suffix(".json"))
    return {
        "elapsed_s": sum(step_latencies),
        "step_latencies_s": step_latencies,
        "profile_json": profile_json,
        "decode_mode": "with_past_kv_cache" if cache_enabled else "single_token_without_cache_feedback",
        "io_summary": io_summary(session),
    }


def aggregate_operator_rows(run_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in run_rows:
        key = (row["phase"], row["context_length"], row["decode_steps"], row["op_type"], row["provider"])
        item = grouped.setdefault(
            key,
            {
                "phase": row["phase"],
                "context_length": row["context_length"],
                "decode_steps": row["decode_steps"],
                "op_type": row["op_type"],
                "provider": row["provider"],
                "profile_count": 0,
                "call_count": 0,
                "total_us": 0.0,
            },
        )
        item["profile_count"] += 1
        item["call_count"] += int(row["call_count"])
        item["total_us"] += float(row["total_us"])
    output = []
    for item in grouped.values():
        item["mean_us"] = item["total_us"] / item["call_count"] if item["call_count"] else None
        output.append(item)
    return sorted(output, key=lambda item: (item["context_length"], item["decode_steps"], item["phase"], -item["total_us"], item["op_type"]))


def share_rows(operator_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    totals: dict[tuple[Any, ...], float] = defaultdict(float)
    focused: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in operator_rows:
        base = (row["phase"], row["context_length"], row["decode_steps"])
        totals[base] += float(row["total_us"])
        group = FOCUS_OPS.get(str(row["op_type"]))
        if not group:
            continue
        key = base + (group,)
        item = focused.setdefault(
            key,
            {
                "phase": row["phase"],
                "context_length": row["context_length"],
                "decode_steps": row["decode_steps"],
                "operator_group": group,
                "call_count": 0,
                "total_us": 0.0,
            },
        )
        item["call_count"] += int(row["call_count"])
        item["total_us"] += float(row["total_us"])
    output = []
    for key, item in focused.items():
        phase_total = totals[key[:3]]
        item["phase_total_us"] = phase_total
        item["share_pct"] = item["total_us"] / phase_total * 100.0 if phase_total else None
        output.append(item)
    return sorted(output, key=lambda item: (item["context_length"], item["decode_steps"], item["phase"], -item["total_us"]))


def comparison_rows(latency_rows: list[dict[str, Any]], operator_rows: list[dict[str, Any]], shares: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prefill = {row["context_length"]: row for row in latency_rows if row["phase"] == "prefill" and row["status"] == "ok"}
    matmul_share = {
        (row["phase"], row["context_length"], row["decode_steps"]): row["share_pct"]
        for row in shares
        if row["operator_group"] == "MatMul"
    }
    top_ops: dict[tuple[str, int, int], str] = {}
    for row in operator_rows:
        top_ops.setdefault((row["phase"], row["context_length"], row["decode_steps"]), row["op_type"])
    output = []
    for row in latency_rows:
        if row["phase"] != "decode" or row["status"] != "ok":
            continue
        context = row["context_length"]
        steps = row["decode_steps"]
        output.append(
            {
                "context_length": context,
                "decode_steps": steps,
                "prefill_mean_ms": prefill.get(context, {}).get("latency_mean_ms"),
                "decode_total_mean_ms": row.get("latency_mean_ms"),
                "decode_per_token_mean_ms": row.get("per_token_mean_ms"),
                "matmul_prefill_share_pct": matmul_share.get(("prefill", context, 0)),
                "matmul_decode_share_pct": matmul_share.get(("decode", context, steps)),
                "top_prefill_op": top_ops.get(("prefill", context, 0)),
                "top_decode_op": top_ops.get(("decode", context, steps)),
            }
        )
    return output


def render_figures(args: argparse.Namespace, latency_rows: list[dict[str, Any]], shares: list[dict[str, Any]]) -> None:
    prefill = [row for row in latency_rows if row["phase"] == "prefill" and row["status"] == "ok"]
    decode = [row for row in latency_rows if row["phase"] == "decode" and row["status"] == "ok"]

    if prefill:
        plt.figure(figsize=(7, 4))
        plt.plot([row["context_length"] for row in prefill], [row["latency_mean_ms"] for row in prefill], marker="o")
        plt.xlabel("Context length")
        plt.ylabel("Prefill latency (ms)")
        plt.title("ONNX Runtime CPU prefill latency by context")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(args.paper_figures_dir / "ort_prefill_latency_by_context.png", dpi=160)
        plt.close()

    if decode:
        plt.figure(figsize=(7, 4))
        for steps in sorted({row["decode_steps"] for row in decode}):
            rows = [row for row in decode if row["decode_steps"] == steps]
            plt.plot([row["context_length"] for row in rows], [row["per_token_mean_ms"] for row in rows], marker="o", label=f"{steps} step")
        plt.xlabel("Context length")
        plt.ylabel("Decode latency per token (ms)")
        plt.title("ONNX Runtime CPU decode latency by context")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(args.paper_figures_dir / "ort_decode_latency_by_context.png", dpi=160)
        plt.close()

    matmul = [row for row in shares if row["operator_group"] == "MatMul"]
    if matmul:
        plt.figure(figsize=(7, 4))
        prefill_rows = [row for row in matmul if row["phase"] == "prefill"]
        if prefill_rows:
            plt.plot([row["context_length"] for row in prefill_rows], [row["share_pct"] for row in prefill_rows], marker="o", label="prefill")
        for steps in sorted({row["decode_steps"] for row in matmul if row["phase"] == "decode"}):
            rows = [row for row in matmul if row["phase"] == "decode" and row["decode_steps"] == steps]
            plt.plot([row["context_length"] for row in rows], [row["share_pct"] for row in rows], marker="o", label=f"decode {steps}")
        plt.xlabel("Context length")
        plt.ylabel("MatMul share of traced node time (%)")
        plt.title("ONNX Runtime CPU MatMul share by phase")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(args.paper_figures_dir / "ort_operator_share_by_context.png", dpi=160)
        plt.close()


def render_report(args: argparse.Namespace, latency_rows: list[dict[str, Any]], operator_rows: list[dict[str, Any]], comparisons: list[dict[str, Any]], status: dict[str, Any]) -> Path:
    lines = [
        "# ONNX Runtime Context Sweep Report",
        "",
        "## Scope",
        "",
        "- Runtime: ONNX Runtime `CPUExecutionProvider`.",
        f"- Model: `{status.get('model', args.model)}`.",
        f"- Context lengths: `{', '.join(str(x) for x in status.get('context_lengths', []))}`.",
        f"- Decode steps: `{', '.join(str(x) for x in status.get('decode_steps', []))}`.",
        f"- Runs / warmup: `{status.get('runs')}` / `{status.get('warmup_runs')}`.",
        "- PyTorch baselines are not used as ONNX Runtime measurements.",
        "- FPGA primitive results are not used as end-to-end ONNX Runtime acceleration evidence.",
        "",
        "## Cache I/O",
        "",
    ]
    io = status.get("io_summary", {})
    lines.extend(
        [
            f"- Decode input generation possible: `{io.get('decode_input_generation_possible')}`.",
            f"- Cache inputs / outputs: `{io.get('cache_input_count')}` / `{io.get('cache_output_count')}`.",
            "- Cache I/O is treated as a decode profiling enabler and memory-pressure candidate, not as proof of a single bottleneck.",
            "",
            "## Latency Summary",
            "",
        ]
    )
    for row in comparisons:
        lines.append(
            f"- Context `{row['context_length']}`, decode `{row['decode_steps']}`: "
            f"prefill `{float(row['prefill_mean_ms']):.3f} ms`, "
            f"decode/token `{float(row['decode_per_token_mean_ms']):.3f} ms`, "
            f"MatMul share prefill `{float(row['matmul_prefill_share_pct']):.1f}%`, "
            f"decode `{float(row['matmul_decode_share_pct']):.1f}%`."
        )
    lines.extend(["", "## Operator Findings", ""])
    max_decode = max(status.get("decode_steps", [0]))
    for context in status.get("context_lengths", []):
        for phase, steps in (("prefill", 0), ("decode", max_decode)):
            rows = [row for row in operator_rows if row["context_length"] == context and row["phase"] == phase and row["decode_steps"] == steps][:5]
            if rows:
                label = "prefill" if phase == "prefill" else f"decode {steps}"
                lines.append(f"- Context `{context}` {label} top ops: " + ", ".join(f"`{row['op_type']}` {float(row['total_us']):.0f}us" for row in rows) + ".")
    lines.extend(
        [
            "",
            "## Interpretation Limits",
            "",
            "- These are short synthetic CPU runs and should not be treated as final bottleneck proof.",
            "- MatMul is currently an evidence-backed runtime hotspot candidate because it dominates traced node time in these runs.",
            "- KV-cache is reported as cache I/O and memory-pressure candidate context only.",
            "- No claim is made that FPGA is faster than ONNX Runtime or that DE10-Lite runs Gemma 3 1B.",
            "",
            "## Artifacts",
            "",
            f"- Status JSON: `{(args.out_dir / 'raw' / 'ort_sweep_status.json').resolve()}`",
            f"- Latency CSV: `{(args.paper_tables_dir / 'ort_context_sweep_latency.csv').resolve()}`",
            f"- Operator latency CSV: `{(args.paper_tables_dir / 'ort_operator_latency_by_context.csv').resolve()}`",
            f"- Operator share CSV: `{(args.paper_tables_dir / 'ort_operator_share_by_context.csv').resolve()}`",
            f"- Prefill/decode comparison CSV: `{(args.paper_tables_dir / 'ort_prefill_decode_comparison.csv').resolve()}`",
        ]
    )
    args.report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return args.report_path


def run_sweep(args: argparse.Namespace) -> dict[str, Any]:
    raw_dir = ensure_dirs(args)
    model_path = model_exists(args.model)
    status_path = raw_dir / "ort_sweep_status.json"
    latency_rows: list[dict[str, Any]] = []
    raw_runs: list[dict[str, Any]] = []
    operator_run_rows: list[dict[str, Any]] = []
    attempted_points: list[dict[str, Any]] = []

    status: dict[str, Any] = {
        "model": str(model_path.resolve()),
        "provider": args.provider,
        "available_providers": ort.get_available_providers(),
        "context_lengths": args.context_lengths,
        "decode_steps": args.decode_steps,
        "runs": args.runs,
        "warmup_runs": args.warmup_runs,
        "status": "running",
        "attempted_points": attempted_points,
        "failure": None,
    }
    write_json(status_path, status)

    meta_session = make_session(model_path, args.provider)
    status["session_description"] = describe_session(meta_session)
    status["io_summary"] = io_summary(meta_session)
    del meta_session
    write_json(status_path, status)

    for context_length in args.context_lengths:
        point = {"context_length": context_length, "status": "running", "decode_steps": []}
        attempted_points.append(point)
        context_dir = raw_dir / f"context_{context_length}"
        context_dir.mkdir(parents=True, exist_ok=True)
        write_json(status_path, status)
        try:
            for _ in range(args.warmup_runs):
                warm = run_prefill(model_path, args.provider, context_length, None)
                for decode_steps in args.decode_steps:
                    run_decode(model_path, args.provider, context_length, decode_steps, warm["cache_tensors"], None)

            prefill_latencies: list[float] = []
            prefill_profiles: list[str] = []
            cache_for_decode: dict[str, np.ndarray] | None = None
            for run_idx in range(args.runs):
                result = run_prefill(model_path, args.provider, context_length, context_dir / f"prefill_ctx{context_length}_run{run_idx}")
                cache_for_decode = result["cache_tensors"]
                prefill_latencies.append(result["elapsed_s"])
                prefill_profiles.append(str(result["profile_json"]))
                raw_runs.append({"phase": "prefill", "context_length": context_length, "decode_steps": 0, "run_index": run_idx, "elapsed_s": result["elapsed_s"], "profile_json": result["profile_json"]})
                for row in summarize_profile(Path(result["profile_json"])):
                    row.update({"phase": "prefill", "context_length": context_length, "decode_steps": 0, "run_index": run_idx})
                    operator_run_rows.append(row)

            latency_rows.append(
                {
                    "phase": "prefill",
                    "context_length": context_length,
                    "decode_steps": 0,
                    "runs": args.runs,
                    "warmup_runs": args.warmup_runs,
                    "latency_mean_ms": mean(prefill_latencies) * 1000.0 if prefill_latencies else None,
                    "latency_p50_ms": p50(prefill_latencies) * 1000.0 if prefill_latencies else None,
                    "latency_std_ms": stdev(prefill_latencies) * 1000.0 if prefill_latencies else None,
                    "per_token_mean_ms": mean(prefill_latencies) * 1000.0 / context_length if prefill_latencies else None,
                    "profile_jsons": "; ".join(prefill_profiles),
                    "status": "ok",
                    "error": None,
                }
            )
            if cache_for_decode is None:
                raise RuntimeError("Prefill completed without cache tensors.")

            for decode_steps in args.decode_steps:
                step_point = {"decode_steps": decode_steps, "status": "running"}
                point["decode_steps"].append(step_point)
                decode_latencies: list[float] = []
                decode_step_latencies: list[float] = []
                decode_profiles: list[str] = []
                for run_idx in range(args.runs):
                    result = run_decode(model_path, args.provider, context_length, decode_steps, cache_for_decode, context_dir / f"decode_ctx{context_length}_steps{decode_steps}_run{run_idx}")
                    decode_latencies.append(result["elapsed_s"])
                    decode_step_latencies.extend(result["step_latencies_s"])
                    decode_profiles.append(str(result["profile_json"]))
                    raw_runs.append(
                        {
                            "phase": "decode",
                            "context_length": context_length,
                            "decode_steps": decode_steps,
                            "run_index": run_idx,
                            "elapsed_s": result["elapsed_s"],
                            "step_latencies_s": result["step_latencies_s"],
                            "profile_json": result["profile_json"],
                            "decode_mode": result["decode_mode"],
                        }
                    )
                    for row in summarize_profile(Path(result["profile_json"])):
                        row.update({"phase": "decode", "context_length": context_length, "decode_steps": decode_steps, "run_index": run_idx})
                        operator_run_rows.append(row)
                latency_rows.append(
                    {
                        "phase": "decode",
                        "context_length": context_length,
                        "decode_steps": decode_steps,
                        "runs": args.runs,
                        "warmup_runs": args.warmup_runs,
                        "latency_mean_ms": mean(decode_latencies) * 1000.0 if decode_latencies else None,
                        "latency_p50_ms": p50(decode_latencies) * 1000.0 if decode_latencies else None,
                        "latency_std_ms": stdev(decode_latencies) * 1000.0 if decode_latencies else None,
                        "per_token_mean_ms": mean(decode_step_latencies) * 1000.0 if decode_step_latencies else None,
                        "profile_jsons": "; ".join(decode_profiles),
                        "status": "ok",
                        "error": None,
                    }
                )
                step_point["status"] = "ok"
                write_json(status_path, status)
            point["status"] = "ok"
        except Exception as exc:
            point["status"] = "failed"
            point["error"] = f"{type(exc).__name__}: {exc}"
            latency_rows.append(
                {
                    "phase": "failed",
                    "context_length": context_length,
                    "decode_steps": None,
                    "runs": args.runs,
                    "warmup_runs": args.warmup_runs,
                    "latency_mean_ms": None,
                    "latency_p50_ms": None,
                    "latency_std_ms": None,
                    "per_token_mean_ms": None,
                    "profile_jsons": "",
                    "status": "failed",
                    "error": point["error"],
                }
            )
        write_json(status_path, status)

    operator_rows = aggregate_operator_rows(operator_run_rows)
    shares = share_rows(operator_rows)
    comparisons = comparison_rows(latency_rows, operator_rows, shares)

    write_json(raw_dir / "ort_sweep_raw_runs.json", {"runs": raw_runs})
    write_json(raw_dir / "ort_sweep_operator_runs.json", {"operator_runs": operator_run_rows})
    write_csv(args.paper_tables_dir / "ort_context_sweep_latency.csv", ["phase", "context_length", "decode_steps", "runs", "warmup_runs", "latency_mean_ms", "latency_p50_ms", "latency_std_ms", "per_token_mean_ms", "profile_jsons", "status", "error"], latency_rows)
    write_csv(args.paper_tables_dir / "ort_operator_latency_by_context.csv", ["phase", "context_length", "decode_steps", "op_type", "provider", "profile_count", "call_count", "total_us", "mean_us"], operator_rows)
    write_csv(args.paper_tables_dir / "ort_operator_share_by_context.csv", ["phase", "context_length", "decode_steps", "operator_group", "call_count", "total_us", "phase_total_us", "share_pct"], shares)
    write_csv(args.paper_tables_dir / "ort_prefill_decode_comparison.csv", ["context_length", "decode_steps", "prefill_mean_ms", "decode_total_mean_ms", "decode_per_token_mean_ms", "matmul_prefill_share_pct", "matmul_decode_share_pct", "top_prefill_op", "top_decode_op"], comparisons)
    render_figures(args, latency_rows, shares)
    report_path = render_report(args, latency_rows, operator_rows, comparisons, status)

    status["status"] = "ok" if all(point.get("status") == "ok" for point in attempted_points) else "partial"
    status["outputs"] = {
        "raw_runs": str((raw_dir / "ort_sweep_raw_runs.json").resolve()),
        "operator_runs": str((raw_dir / "ort_sweep_operator_runs.json").resolve()),
        "latency_csv": str((args.paper_tables_dir / "ort_context_sweep_latency.csv").resolve()),
        "operator_latency_csv": str((args.paper_tables_dir / "ort_operator_latency_by_context.csv").resolve()),
        "operator_share_csv": str((args.paper_tables_dir / "ort_operator_share_by_context.csv").resolve()),
        "comparison_csv": str((args.paper_tables_dir / "ort_prefill_decode_comparison.csv").resolve()),
        "report": str(report_path.resolve()),
    }
    write_json(status_path, status)
    return status


def report_only(args: argparse.Namespace) -> Path:
    latency_rows = [convert_row(row) for row in read_csv_rows(args.paper_tables_dir / "ort_context_sweep_latency.csv")]
    operator_rows = [convert_row(row) for row in read_csv_rows(args.paper_tables_dir / "ort_operator_latency_by_context.csv")]
    comparison = [convert_row(row) for row in read_csv_rows(args.paper_tables_dir / "ort_prefill_decode_comparison.csv")]
    status_path = args.out_dir / "raw" / "ort_sweep_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.is_file() else {
        "model": str(args.model),
        "context_lengths": args.context_lengths,
        "decode_steps": args.decode_steps,
        "runs": "?",
        "warmup_runs": "?",
        "io_summary": {},
    }
    return render_report(args, latency_rows, operator_rows, comparison, status)


def convert_row(row: dict[str, str]) -> dict[str, Any]:
    output: dict[str, Any] = dict(row)
    for key in ("context_length", "decode_steps", "runs", "warmup_runs", "profile_count", "call_count"):
        if key in output and output[key] not in ("", None):
            output[key] = int(float(output[key]))
    for key in ("latency_mean_ms", "latency_p50_ms", "latency_std_ms", "per_token_mean_ms", "total_us", "mean_us", "prefill_mean_ms", "decode_total_mean_ms", "decode_per_token_mean_ms", "matmul_prefill_share_pct", "matmul_decode_share_pct"):
        if key in output and output[key] not in ("", None):
            output[key] = float(output[key])
    return output


def main() -> None:
    args = parse_args()
    if args.command == "sweep":
        print(json.dumps(run_sweep(args), indent=2))
    elif args.command == "report":
        print(report_only(args))


if __name__ == "__main__":
    main()
