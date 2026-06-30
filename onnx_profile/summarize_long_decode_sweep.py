#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


DEFAULT_RESULTS_DIR = Path("onnx_profile/results_onnx_long_decode")
DEFAULT_TABLES_DIR = Path("assets")
DEFAULT_FIGURES_DIR = Path("assets")
DEFAULT_REPORT = Path("onnx_profile/results/reports/ort_long_decode_sweep_report.md")
SHAPE_OPS = ("Expand", "Concat", "Unsqueeze")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize long-decode ONNX Runtime CPU sweep artifacts for the paper.")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--tables-dir", type=Path, default=DEFAULT_TABLES_DIR)
    parser.add_argument("--figures-dir", type=Path, default=DEFAULT_FIGURES_DIR)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def as_int(value: str) -> int:
    return int(float(value))


def as_float(value: str) -> float:
    return float(value)


def latency_rows(raw_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in raw_rows:
        if row["phase"] != "decode" or row["status"] != "ok":
            continue
        rows.append(
            {
                "provider": "CPUExecutionProvider",
                "context_length": as_int(row["context_length"]),
                "decode_steps": as_int(row["decode_steps"]),
                "runs": as_int(row["runs"]),
                "warmup_runs": as_int(row["warmup_runs"]),
                "decode_total_mean_ms": as_float(row["latency_mean_ms"]),
                "decode_per_token_mean_ms": as_float(row["per_token_mean_ms"]),
                "latency_std_ms": as_float(row["latency_std_ms"]),
                "status": row["status"],
                "source_profile_jsons": row["profile_jsons"],
            }
        )
    return sorted(rows, key=lambda item: (item["context_length"], item["decode_steps"]))


def operator_share_rows(operator_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    totals: dict[tuple[int, int], float] = defaultdict(float)
    selected: dict[tuple[int, int, str], dict[str, Any]] = {}
    for row in operator_rows:
        if row["phase"] != "decode":
            continue
        context = as_int(row["context_length"])
        steps = as_int(row["decode_steps"])
        op_type = row["op_type"]
        total_us = as_float(row["total_us"])
        call_count = as_int(row["call_count"])
        totals[(context, steps)] += total_us
        if op_type == "MatMul" or op_type in SHAPE_OPS:
            selected[(context, steps, op_type)] = {
                "provider": "CPUExecutionProvider",
                "context_length": context,
                "decode_steps": steps,
                "operator_group": op_type,
                "call_count": call_count,
                "total_us": total_us,
            }

    for context, steps in sorted(totals):
        shape_total_us = 0.0
        shape_call_count = 0
        for op_type in SHAPE_OPS:
            item = selected.get((context, steps, op_type))
            if item:
                shape_total_us += float(item["total_us"])
                shape_call_count += int(item["call_count"])
        selected[(context, steps, "shape_related_total")] = {
            "provider": "CPUExecutionProvider",
            "context_length": context,
            "decode_steps": steps,
            "operator_group": "shape_related_total",
            "call_count": shape_call_count,
            "total_us": shape_total_us,
        }

    output = []
    for key, item in selected.items():
        phase_total_us = totals[key[:2]]
        item["phase_total_us"] = phase_total_us
        item["share_pct"] = item["total_us"] / phase_total_us * 100.0 if phase_total_us else 0.0
        output.append(item)
    return sorted(output, key=lambda item: (item["context_length"], item["decode_steps"], item["operator_group"]))


def lookup(rows: list[dict[str, Any]], group: str) -> dict[tuple[int, int], dict[str, Any]]:
    return {(row["context_length"], row["decode_steps"]): row for row in rows if row["operator_group"] == group}


def render_figures(latency: list[dict[str, Any]], shares: list[dict[str, Any]], figures_dir: Path) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    matmul = lookup(shares, "MatMul")
    shape = lookup(shares, "shape_related_total")
    contexts = sorted({row["context_length"] for row in latency})

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    for context in contexts:
        points = [(steps, matmul[(context, steps)]["share_pct"]) for steps in sorted(row["decode_steps"] for row in latency if row["context_length"] == context)]
        ax.plot([step for step, _ in points], [value for _, value in points], marker="o", label=f"context {context}")
    ax.set_xscale("log", base=2)
    ax.set_xticks([8, 32, 64, 128, 256])
    ax.set_xticklabels(["8", "32", "64", "128", "256"])
    ax.set_xlabel("Decode steps")
    ax.set_ylabel("MatMul share of traced decode node time (%)")
    ax.set_title("Long-decode ORT CPU MatMul share")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "f03.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    for context in contexts:
        points = [(steps, shape[(context, steps)]["share_pct"]) for steps in sorted(row["decode_steps"] for row in latency if row["context_length"] == context)]
        ax.plot([step for step, _ in points], [value for _, value in points], marker="o", label=f"context {context}")
    ax.set_xscale("log", base=2)
    ax.set_xticks([8, 32, 64, 128, 256])
    ax.set_xticklabels(["8", "32", "64", "128", "256"])
    ax.set_xlabel("Decode steps")
    ax.set_ylabel("Expand + Concat + Unsqueeze share (%)")
    ax.set_title("Long-decode ORT CPU shape-related op share")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "f04.png", dpi=220)
    plt.close(fig)


def render_report(latency: list[dict[str, Any]], shares: list[dict[str, Any]], report_path: Path) -> None:
    matmul = lookup(shares, "MatMul")
    shape = lookup(shares, "shape_related_total")
    expand = lookup(shares, "Expand")
    concat = lookup(shares, "Concat")
    unsqueeze = lookup(shares, "Unsqueeze")

    lines = [
        "# ONNX Runtime Long-Decode Sweep Report",
        "",
        "## Scope",
        "",
        "- Runtime provider: ONNX Runtime `CPUExecutionProvider`.",
        "- Context lengths: `128`, `512`, `2048`.",
        "- Decode steps: `8`, `32`, `64`, `128`, `256`.",
        "- Runs / warmup: `1` / `0`.",
        "- This sweep extends the earlier decode-step <= 8 artifact and is still a CPUExecutionProvider host-side profile.",
        "- No FPGA recompilation, custom operator integration, or end-to-end acceleration measurement is included.",
        "",
        "## Summary Table",
        "",
        "| context | decode steps | decode/token ms | MatMul share | shape-op share | Expand share | Concat share | Unsqueeze share |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in latency:
        key = (row["context_length"], row["decode_steps"])
        lines.append(
            "| "
            f"{row['context_length']} | {row['decode_steps']} | {row['decode_per_token_mean_ms']:.3f} | "
            f"{matmul[key]['share_pct']:.2f}% | {shape[key]['share_pct']:.2f}% | "
            f"{expand[key]['share_pct']:.2f}% | {concat[key]['share_pct']:.2f}% | {unsqueeze[key]['share_pct']:.2f}% |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- MatMul remains the largest traced decode operator group across all long-decode points.",
            "- At context 2048, MatMul share decreases from `78.33%` at 8 decode steps to `72.91%` at 256 decode steps.",
            "- At context 2048 and 256 decode steps, `Expand + Concat + Unsqueeze` accounts for `17.71%` of traced decode node time.",
            "- This supports treating KV-cache and shape-related graph work as a growing long-decode pressure source, while not reducing the bottleneck to KV-cache alone.",
            "- Per-token latency is noisy with one run, so trends are reported as host-side evidence rather than a statistically final latency model.",
            "",
            "## Artifacts",
            "",
            "- `assets/c06.csv`",
            "- `assets/c07.csv`",
            "- `assets/f03.png`",
            "- `assets/f04.png`",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    latency = latency_rows(read_csv(args.results_dir / "tables" / "c04.csv"))
    shares = operator_share_rows(read_csv(args.results_dir / "tables" / "ort_operator_latency_by_context.csv"))

    write_csv(
        args.tables_dir / "c06.csv",
        [
            "provider",
            "context_length",
            "decode_steps",
            "runs",
            "warmup_runs",
            "decode_total_mean_ms",
            "decode_per_token_mean_ms",
            "latency_std_ms",
            "status",
            "source_profile_jsons",
        ],
        latency,
    )
    write_csv(
        args.tables_dir / "c07.csv",
        [
            "provider",
            "context_length",
            "decode_steps",
            "operator_group",
            "call_count",
            "total_us",
            "phase_total_us",
            "share_pct",
        ],
        shares,
    )
    render_figures(latency, shares, args.figures_dir)
    render_report(latency, shares, args.report_path)


if __name__ == "__main__":
    main()
