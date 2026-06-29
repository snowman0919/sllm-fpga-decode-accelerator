#!/usr/bin/env python3
"""Benchmark a Gemma-derived partial tile ONNX micrograph on CPUExecutionProvider."""

from __future__ import annotations

import argparse
import csv
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
    parser.add_argument("--model", default=str(PROJECT_ROOT / "onnx_micrographs/gemma_mlp_projection_tile_cpu.onnx"))
    parser.add_argument("--source-model", default="Gemma 3 1B ONNX profile artifacts")
    parser.add_argument("--source-node")
    parser.add_argument("--category", default="mlp_projection")
    parser.add_argument("--input-dim", type=int, default=DEFAULT_INPUT_DIM)
    parser.add_argument("--output-dim", type=int, default=DEFAULT_OUTPUT_DIM)
    return parser.parse_args()


def first_candidate(category: str) -> str:
    path = PROJECT_ROOT / "paper_assets/tables/gemma_partial_offload_candidates.csv"
    if not path.exists():
        return ""
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("category") == category:
                return row.get("node_name", "")
    return ""


def ensure_model(path: Path, input_dim: int, output_dim: int) -> bool:
    if path.exists():
        return True
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "onnx_micrographs"))
        from generate_matvec_micrographs import make_graph

        make_graph(path, input_dim, output_dim, path.name)
        return True
    except Exception as exc:
        print(f"could not generate tile ONNX graph: {exc}")
        return False


def skipped(log_dir: Path, reason: str, args: argparse.Namespace) -> None:
    summary = {
        "backend": "onnxruntime_cpu",
        "skipped": True,
        "reason": reason,
        "model": args.model,
    }
    write_json(log_dir / "gemma_partial_tile_summary.json", summary)
    write_summary_md(log_dir / "gemma_partial_tile_summary.md", "Gemma Partial Tile CPU Summary", summary)
    print(f"Gemma partial tile benchmark skipped: {reason}")


def main() -> None:
    args = parse_args()
    log_dir = resolve_log_dir(args.log_dir)
    model_path = Path(args.model)
    if not ensure_model(model_path, args.input_dim, args.output_dim):
        skipped(log_dir, "onnx package is unavailable or graph generation failed", args)
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
        result = session.run(None, {"activation": activation, "weight": weight})[0]
        t1 = timer()
        pass_run = bool((result == reference).all())
        all_pass = all_pass and pass_run
        rows.append(
            {
                "run": run,
                "source_model": args.source_model,
                "source_node": args.source_node or first_candidate(args.category),
                "category": args.category,
                "tile_shape": f"[1,{args.input_dim}]x[{args.input_dim},{args.output_dim}]",
                "input_dim": args.input_dim,
                "output_dim": args.output_dim,
                "macs": args.input_dim * args.output_dim,
                "weight_source": "deterministic_synthetic_tile",
                "activation_source": "deterministic_synthetic_activation",
                "synthetic_weight": True,
                "dtype": "float32",
                "backend": "onnxruntime_cpu",
                "latency_ms": elapsed_ms(t0, t1),
                "correctness_pass": pass_run,
            }
        )

    latency = latency_summary(rows, "latency_ms")
    summary = {
        "source_model": args.source_model,
        "source_node": args.source_node or first_candidate(args.category),
        "category": args.category,
        "tile_shape": f"[1,{args.input_dim}]x[{args.input_dim},{args.output_dim}]",
        "input_dim": args.input_dim,
        "output_dim": args.output_dim,
        "macs": args.input_dim * args.output_dim,
        "weight_source": "deterministic_synthetic_tile",
        "activation_source": "deterministic_synthetic_activation",
        "synthetic_weight": True,
        "dtype": "float32",
        "backend": "onnxruntime_cpu",
        "runs": args.runs,
        "correctness_pass": all_pass,
        "latency_ms_mean": round(latency["mean"], 6),
        "latency_ms_p50": round(latency["p50"], 6),
        "latency_ms_p95": round(latency["p95"], 6),
        "note": "Gemma-derived tile shape/category with synthetic tile values; not full Gemma ONNX execution.",
    }
    write_csv(log_dir / "gemma_partial_tile_cpu.csv", rows)
    write_json(log_dir / "gemma_partial_tile_summary.json", summary)
    write_summary_md(log_dir / "gemma_partial_tile_summary.md", "Gemma Partial Tile CPU Summary", summary)
    update_table(
        PROJECT_ROOT / "paper_assets/tables/gemma_partial_tile_baseline.csv",
        ["source_model", "source_node", "category", "tile_shape", "backend", "dtype"],
        {
            "source_model": summary["source_model"],
            "source_node": summary["source_node"],
            "category": summary["category"],
            "tile_shape": summary["tile_shape"],
            "input_dim": summary["input_dim"],
            "output_dim": summary["output_dim"],
            "macs": summary["macs"],
            "weight_source": summary["weight_source"],
            "activation_source": summary["activation_source"],
            "synthetic_weight": summary["synthetic_weight"],
            "backend": summary["backend"],
            "dtype": summary["dtype"],
            "evidence_type": "measured",
            "correctness_pass": summary["correctness_pass"],
            "latency_ms_mean": summary["latency_ms_mean"],
            "latency_ms_p50": summary["latency_ms_p50"],
            "latency_ms_p95": summary["latency_ms_p95"],
            "latency_source": "ONNX Runtime CPUExecutionProvider session.run wall time",
            "claim_boundary": "Gemma-derived category/tile-shape baseline with synthetic values; not full Gemma ONNX execution",
            "note": summary["note"],
        },
    )
    update_table(
        PROJECT_ROOT / "paper_assets/tables/gemma_partial_tile_benchmark.csv",
        ["source_model", "source_node", "category", "tile_shape", "backend"],
        {
            "source_model": summary["source_model"],
            "source_node": summary["source_node"],
            "category": summary["category"],
            "tile_shape": summary["tile_shape"],
            "weight_source": summary["weight_source"],
            "activation_source": summary["activation_source"],
            "backend": summary["backend"],
            "correctness_pass": summary["correctness_pass"],
            "latency_ms_mean": summary["latency_ms_mean"],
            "uart_overhead_ms_mean": "",
            "note": summary["note"],
        },
    )
    print(f"wrote {log_dir / 'gemma_partial_tile_summary.md'}")


if __name__ == "__main__":
    main()
