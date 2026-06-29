#!/usr/bin/env python3
"""Run the fixed INT8 Decode MatVec primitive on the CPU as a reference baseline."""

from __future__ import annotations

import argparse
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
    parser.add_argument("--input-dim", type=int, default=DEFAULT_INPUT_DIM)
    parser.add_argument("--output-dim", type=int, default=DEFAULT_OUTPUT_DIM)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    log_dir = resolve_log_dir(args.log_dir)

    rows: list[dict[str, object]] = []
    correctness = True
    reference = None
    for run in range(args.runs):
        t0 = timer()
        activation = deterministic_activation(args.input_dim)
        weights = deterministic_weights(args.input_dim, args.output_dim)
        t1 = timer()
        result = cpu_reference(activation, weights)
        t2 = timer()
        if reference is None:
            reference = result
        correctness = correctness and bool((result == reference).all())
        total_ms = elapsed_ms(t0, t2)
        rows.append(
            {
                "run": run,
                "input_dim": args.input_dim,
                "output_dim": args.output_dim,
                "generation_ms": elapsed_ms(t0, t1),
                "compute_ms": elapsed_ms(t1, t2),
                "total_latency_ms": total_ms,
                "result": " ".join(str(int(v)) for v in result),
                "correctness_pass": True,
            }
        )

    total = latency_summary(rows, "total_latency_ms")
    compute = latency_summary(rows, "compute_ms")
    macs_per_run = args.input_dim * args.output_dim
    summary = {
        "backend": "cpu_numpy_int32",
        "input_dim": args.input_dim,
        "output_dim": args.output_dim,
        "runs": args.runs,
        "correctness_pass": correctness,
        "total_latency_ms_mean": round(total["mean"], 6),
        "total_latency_ms_p50": round(total["p50"], 6),
        "total_latency_ms_p95": round(total["p95"], 6),
        "compute_latency_ms_mean": round(compute["mean"], 6),
        "effective_macs_per_s": round((macs_per_run / (total["mean"] / 1000.0)) if total["mean"] else 0.0, 3),
        "log_dir": str(log_dir),
    }

    write_csv(log_dir / "cpu_matvec_baseline.csv", rows)
    write_json(log_dir / "cpu_matvec_summary.json", summary)
    write_summary_md(log_dir / "cpu_matvec_summary.md", "CPU MatVec Baseline Summary", summary)

    update_table(
        PROJECT_ROOT / "paper_assets/tables/fpga_uart_primitive_benchmark.csv",
        ["backend", "input_dim", "output_dim", "baudrate"],
        {
            "backend": "cpu_numpy_int32",
            "input_dim": args.input_dim,
            "output_dim": args.output_dim,
            "runs": args.runs,
            "correctness_pass": correctness,
            "total_latency_ms_mean": round(total["mean"], 6),
            "total_latency_ms_p50": round(total["p50"], 6),
            "total_latency_ms_p95": round(total["p95"], 6),
            "tx_latency_ms_mean": "",
            "rx_wait_latency_ms_mean": "",
            "effective_macs_per_s": summary["effective_macs_per_s"],
            "baudrate": "",
            "note": "CPU NumPy int32 reference for the fixed deterministic INT8 MatVec primitive.",
        },
    )
    print(f"wrote {log_dir / 'cpu_matvec_summary.md'}")


if __name__ == "__main__":
    main()
