#!/usr/bin/env python3
"""Run the small MatVec ONNX micrograph with ONNX Runtime CPUExecutionProvider."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from matvec_common import (
    DEFAULT_INPUT_DIM,
    DEFAULT_OUTPUT_DIM,
    PROJECT_ROOT,
    deterministic_activation,
    deterministic_weights,
    elapsed_ms,
    latency_summary,
    resolve_log_dir,
    timer,
    update_table,
    write_csv,
    write_json,
    write_summary_md,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--log-dir")
    parser.add_argument("--model", default=str(PROJECT_ROOT / "onnx_micrographs/matvec_cpu_baseline.onnx"))
    parser.add_argument("--input-dim", type=int, default=DEFAULT_INPUT_DIM)
    parser.add_argument("--output-dim", type=int, default=DEFAULT_OUTPUT_DIM)
    return parser.parse_args()


def ensure_model(path: Path, input_dim: int, output_dim: int) -> bool:
    if path.exists():
        return True
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "onnx_micrographs"))
        from generate_matvec_micrographs import make_graph

        make_graph(path, input_dim, output_dim, path.name)
        return True
    except Exception as exc:
        print(f"could not generate ONNX micrograph: {exc}")
        return False


def skipped(log_dir: Path, reason: str, args: argparse.Namespace) -> None:
    summary = {
        "backend": "onnxruntime_cpu",
        "skipped": True,
        "reason": reason,
        "model": args.model,
        "runs": args.runs,
    }
    write_json(log_dir / "ort_micrograph_cpu_summary.json", summary)
    write_summary_md(log_dir / "ort_micrograph_cpu_summary.md", "ORT MatVec CPU Micrograph Summary", summary)
    print(f"ORT micrograph CPU test skipped: {reason}")


def main() -> None:
    args = parse_args()
    log_dir = resolve_log_dir(args.log_dir)
    model_path = Path(args.model)

    if not ensure_model(model_path, args.input_dim, args.output_dim):
        skipped(log_dir, "onnx package is unavailable or model generation failed", args)
        return

    try:
        import onnxruntime as ort
    except ImportError:
        skipped(log_dir, "onnxruntime is not installed", args)
        return

    activation_i8 = deterministic_activation(args.input_dim)
    weights_i8 = deterministic_weights(args.input_dim, args.output_dim)
    activation = activation_i8.astype("float32").reshape(1, args.input_dim)
    weight = weights_i8.astype("float32").T
    reference = activation @ weight
    session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])

    rows: list[dict[str, object]] = []
    all_pass = True
    for run in range(args.runs):
        t0 = timer()
        outputs = session.run(None, {"activation": activation, "weight": weight})
        t1 = timer()
        result = outputs[0]
        pass_run = bool((result == reference).all())
        all_pass = all_pass and pass_run
        rows.append(
            {
                "run": run,
                "graph": model_path.name,
                "provider": "CPUExecutionProvider",
                "input_dim": args.input_dim,
                "output_dim": args.output_dim,
                "dtype": "float32",
                "latency_ms": elapsed_ms(t0, t1),
                "correctness_pass": pass_run,
                "result": " ".join(str(float(v)) for v in result.reshape(-1)),
            }
        )

    latency = latency_summary(rows, "latency_ms")
    summary = {
        "backend": "onnxruntime_cpu",
        "graph": model_path.name,
        "provider": "CPUExecutionProvider",
        "custom_op": False,
        "input_dim": args.input_dim,
        "output_dim": args.output_dim,
        "dtype": "float32",
        "runs": args.runs,
        "correctness_pass": all_pass,
        "latency_ms_mean": round(latency["mean"], 6),
        "latency_ms_p50": round(latency["p50"], 6),
        "latency_ms_p95": round(latency["p95"], 6),
        "log_dir": str(log_dir),
    }
    write_csv(log_dir / "ort_micrograph_cpu.csv", rows)
    write_json(log_dir / "ort_micrograph_cpu_summary.json", summary)
    write_summary_md(log_dir / "ort_micrograph_cpu_summary.md", "ORT MatVec CPU Micrograph Summary", summary)
    update_table(
        PROJECT_ROOT / "paper_assets/tables/ort_micrograph_vs_fpga_uart.csv",
        ["backend", "graph", "provider", "custom_op", "input_dim", "output_dim"],
        {
            "backend": "onnxruntime_cpu",
            "graph": model_path.name,
            "provider": "CPUExecutionProvider",
            "custom_op": False,
            "input_dim": args.input_dim,
            "output_dim": args.output_dim,
            "dtype": "float32",
            "correctness_pass": all_pass,
            "latency_ms_mean": round(latency["mean"], 6),
            "latency_ms_p50": round(latency["p50"], 6),
            "latency_ms_p95": round(latency["p95"], 6),
            "uart_txrx_ms_mean": "",
            "note": "Real ONNX Runtime CPUExecutionProvider MatMul micrograph baseline.",
        },
    )
    print(f"wrote {log_dir / 'ort_micrograph_cpu_summary.md'}")


if __name__ == "__main__":
    main()
