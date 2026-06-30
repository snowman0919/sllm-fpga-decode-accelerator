#!/usr/bin/env python3
"""Run the fixed INT8 MatMulInteger ONNX micrograph with ONNX Runtime."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from matvec_common import (
    DEFAULT_INPUT_DIM,
    DEFAULT_OUTPUT_DIM,
    PROJECT_ROOT,
    cpu_reference,
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
    parser.add_argument("--model", default=str(PROJECT_ROOT / "onnx_micrographs/matvec_int8_matmulinteger.onnx"))
    parser.add_argument("--input-dim", type=int, default=DEFAULT_INPUT_DIM)
    parser.add_argument("--output-dim", type=int, default=DEFAULT_OUTPUT_DIM)
    return parser.parse_args()


def ensure_model(path: Path, input_dim: int, output_dim: int) -> bool:
    if path.exists():
        return True
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "onnx_micrographs"))
        from generate_matvec_micrographs import make_matmulinteger_graph

        make_matmulinteger_graph(path, input_dim, output_dim, path.name)
        return True
    except Exception as exc:
        print(f"could not generate MatMulInteger ONNX micrograph: {exc}")
        return False


def skipped(log_dir: Path, reason: str, args: argparse.Namespace) -> None:
    summary = {
        "backend": "onnxruntime_matmulinteger_cpu",
        "skipped": True,
        "reason": reason,
        "model": args.model,
        "input_dim": args.input_dim,
        "output_dim": args.output_dim,
        "dtype": "int8_inputs_int32_output",
        "runs": args.runs,
        "paper_table_updated": False,
        "claim_boundary": "No measured integer ORT baseline is reported when MatMulInteger generation or execution fails.",
    }
    write_json(log_dir / "ort_matmulinteger_summary.json", summary)
    write_summary_md(log_dir / "ort_matmulinteger_summary.md", "ORT MatMulInteger Micrograph Summary", summary)
    print(f"ORT MatMulInteger micrograph skipped: {reason}")


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

    activation = deterministic_activation(args.input_dim).reshape(1, args.input_dim)
    weights = deterministic_weights(args.input_dim, args.output_dim)
    weight = weights.T.copy()
    reference = cpu_reference(activation.reshape(args.input_dim), weights).reshape(1, args.output_dim)

    try:
        session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    except Exception as exc:
        skipped(log_dir, f"ONNX Runtime could not load MatMulInteger graph: {exc}", args)
        return

    rows: list[dict[str, object]] = []
    all_pass = True
    for run in range(args.runs):
        try:
            t0 = timer()
            result = session.run(None, {"activation": activation, "weight": weight})[0]
            t1 = timer()
            pass_run = bool((result == reference).all())
            error = ""
        except Exception as exc:
            t1 = timer()
            result = None
            pass_run = False
            error = str(exc)
        all_pass = all_pass and pass_run
        rows.append(
            {
                "run": run,
                "graph": model_path.name,
                "provider": "CPUExecutionProvider",
                "input_dim": args.input_dim,
                "output_dim": args.output_dim,
                "macs": args.input_dim * args.output_dim,
                "dtype": "int8_inputs_int32_output",
                "latency_ms": elapsed_ms(t0, t1),
                "correctness_pass": pass_run,
                "reference": " ".join(str(int(v)) for v in reference.reshape(-1)),
                "result": "" if result is None else " ".join(str(int(v)) for v in result.reshape(-1)),
                "error": error,
            }
        )

    write_csv(log_dir / "ort_matmulinteger_micrograph.csv", rows)
    if not all_pass:
        skipped(log_dir, "MatMulInteger graph executed but did not produce passing runs", args)
        return

    latency = latency_summary(rows, "latency_ms")
    macs_per_run = args.input_dim * args.output_dim
    summary = {
        "backend": "onnxruntime_matmulinteger_cpu",
        "graph": model_path.name,
        "provider": "CPUExecutionProvider",
        "input_dim": args.input_dim,
        "output_dim": args.output_dim,
        "macs": macs_per_run,
        "dtype": "int8_inputs_int32_output",
        "runs": args.runs,
        "correctness_pass": all_pass,
        "latency_ms_mean": round(latency["mean"], 6),
        "latency_ms_p50": round(latency["p50"], 6),
        "latency_ms_p95": round(latency["p95"], 6),
        "log_dir": str(log_dir),
        "paper_table_updated": True,
        "claim_boundary": "Measured ORT MatMulInteger micrograph baseline only; not full Gemma ONNX Runtime profiling.",
    }
    write_json(log_dir / "ort_matmulinteger_summary.json", summary)
    write_summary_md(log_dir / "ort_matmulinteger_summary.md", "ORT MatMulInteger Micrograph Summary", summary)
    update_table(
        PROJECT_ROOT / "assets/c18.csv",
        ["backend", "interface", "dtype", "input_dim", "output_dim"],
        {
            "backend": "onnxruntime_matmulinteger_micrograph",
            "interface": "CPUExecutionProvider",
            "evidence_type": "measured",
            "dtype": "int8_inputs_int32_output",
            "input_dim": args.input_dim,
            "output_dim": args.output_dim,
            "macs": macs_per_run,
            "runs": args.runs,
            "correctness_pass": all_pass,
            "latency_ms_mean": summary["latency_ms_mean"],
            "latency_ms_p50": summary["latency_ms_p50"],
            "latency_ms_p95": summary["latency_ms_p95"],
            "latency_source": "ONNX Runtime CPUExecutionProvider MatMulInteger session.run wall time",
            "synthetic_weight": True,
            "claim_boundary": summary["claim_boundary"],
            "note": "Same deterministic activation and weight values as FPGA primitive, using ONNX MatMulInteger.",
        },
    )
    print(f"wrote {log_dir / 'ort_matmulinteger_summary.md'}")


if __name__ == "__main__":
    main()
