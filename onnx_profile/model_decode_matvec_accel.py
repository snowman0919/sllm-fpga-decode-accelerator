#!/usr/bin/env python3
"""Estimate FPGA Decode MatVec accelerator candidates from ORT MatMul profiling.

The model is intentionally conservative: it ranks dense projection categories
from measured ONNX Runtime CPU profile time and emits design-estimate tables.
It does not claim an FPGA speedup.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import math
from collections import defaultdict
from pathlib import Path


CANDIDATE_ORDER = [
    "mlp_projection",
    "lm_head",
    "attention_qkv_projection",
    "attention_output_projection",
    "attention_v_weighted_sum",
]

DEFAULT_SHAPES = {
    "mlp_projection": (1152, 6912),
    "lm_head": (1152, 262144),
    "attention_qkv_projection": (1152, 1152),
    "attention_output_projection": (1152, 1152),
    "attention_v_weighted_sum": (2048, 256),
}

ARCH_NOTES = {
    "mlp_projection": "Highest cumulative MatMul time; repeated gate/up/down projection maps naturally to tiled INT8 MatVec/MatMul.",
    "lm_head": "Large vocabulary projection makes full weight streaming unavoidable; tiled streaming and partial top-k/reduction should be studied.",
    "attention_qkv_projection": "Dense linear projection candidate, but measured share is far below MLP and lm_head in the current ORT profile.",
    "attention_output_projection": "Dense projection candidate with moderate reuse of the same MatVec datapath.",
    "attention_v_weighted_sum": "Attention data movement candidate; shape depends on context and KV-cache stream layout.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category-csv", default="paper_assets/tables/ort_matmul_category_by_context.csv")
    parser.add_argument("--top-nodes-csv", default="paper_assets/tables/ort_matmul_top_nodes.csv")
    parser.add_argument("--graph-inspection", default="onnx_profile/results_onnx/raw/onnx_graph_inspection.json")
    parser.add_argument("--tables-dir", default="paper_assets/tables")
    parser.add_argument("--summary-md", default="onnx_profile/results/reports/fpga_decode_accel_model_summary.md")
    parser.add_argument("--clock-mhz", type=float, default=50.0)
    parser.add_argument("--mac-lanes", type=int, default=16)
    parser.add_argument("--bandwidth-mbps", type=float, default=400.0)
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def f(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    return float(value) if value not in ("", None) else 0.0


def i(row: dict[str, str], key: str) -> int:
    value = row.get(key, "")
    return int(float(value)) if value not in ("", None) else 0


def parse_shape_cell(cell: str) -> tuple[int | None, int | None]:
    if not cell:
        return (None, None)
    try:
        parsed = ast.literal_eval(cell)
    except (ValueError, SyntaxError):
        return (None, None)
    if not parsed or not isinstance(parsed, list):
        return (None, None)
    shape = next(iter(parsed[0].values()), None) if isinstance(parsed[0], dict) else None
    if not isinstance(shape, list) or len(shape) < 2:
        return (None, None)
    in_dim = shape[-1] if isinstance(shape[-1], int) else None
    out_dim = shape[-1] if isinstance(shape[-1], int) else None
    return (in_dim, out_dim)


def representative_shapes(top_rows: list[dict[str, str]]) -> dict[str, tuple[int, int]]:
    shapes: dict[str, tuple[int, int]] = {}
    for category in CANDIDATE_ORDER:
        for row in top_rows:
            if row.get("category") != category:
                continue
            in_dim, _ = parse_shape_cell(row.get("example_input_type_shape", ""))
            _, out_dim = parse_shape_cell(row.get("example_output_type_shape", ""))
            if in_dim and out_dim:
                shapes[category] = (in_dim, out_dim)
                break
    for category, shape in DEFAULT_SHAPES.items():
        shapes.setdefault(category, shape)
    return shapes


def graph_summary(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    with path.open() as f:
        data = json.load(f)
    return {
        "node_count": data.get("total_node_count"),
        "matmul_count": data.get("key_operator_counts", {}).get("MatMul"),
        "cache_inputs": len(data.get("cache_input_names", [])),
        "cache_outputs": len(data.get("cache_output_names", [])),
        "decode_cache_reuse_ready": data.get("decode_cache_reuse_ready"),
    }


def aggregate(category_rows: list[dict[str, str]]) -> tuple[dict[str, dict[str, float]], dict[str, float]]:
    by_category: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    unique_phase_totals: dict[tuple[str, str, str], float] = {}
    phase_matmul: dict[str, float] = defaultdict(float)

    for row in category_rows:
        category = row["category"]
        total_us = f(row, "total_us")
        by_category[category]["total_us"] += total_us
        by_category[category]["call_count"] += i(row, "call_count")
        by_category[category]["profile_count"] += i(row, "profile_count")
        by_category[category][f"{row['phase']}_us"] += total_us
        phase_matmul[row["phase"]] += total_us
        key = (row["phase"], row["context_length"], row["decode_steps"])
        unique_phase_totals[key] = f(row, "phase_node_total_us")

    total_matmul_us = sum(v["total_us"] for v in by_category.values())
    total_phase_us = sum(unique_phase_totals.values())
    stats = {
        "total_matmul_us": total_matmul_us,
        "total_phase_us": total_phase_us,
        "total_matmul_share_pct": 100.0 * total_matmul_us / total_phase_us if total_phase_us else 0.0,
        "prefill_matmul_us": phase_matmul["prefill"],
        "decode_matmul_us": phase_matmul["decode"],
    }
    phase_totals = defaultdict(float)
    for (phase, _, _), total_us in unique_phase_totals.items():
        phase_totals[phase] += total_us
    stats["prefill_matmul_share_pct"] = 100.0 * phase_matmul["prefill"] / phase_totals["prefill"]
    stats["decode_matmul_share_pct"] = 100.0 * phase_matmul["decode"] / phase_totals["decode"]
    return by_category, stats


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    category_path = Path(args.category_csv)
    top_nodes_path = Path(args.top_nodes_csv)
    tables_dir = Path(args.tables_dir)
    summary_path = Path(args.summary_md)

    category_rows = read_rows(category_path)
    top_rows = read_rows(top_nodes_path) if top_nodes_path.exists() else []
    by_category, stats = aggregate(category_rows)
    shapes = representative_shapes(top_rows)
    graph = graph_summary(Path(args.graph_inspection))

    total_matmul_us = stats["total_matmul_us"]
    mlp_lm_us = by_category["mlp_projection"]["total_us"] + by_category["lm_head"]["total_us"]
    mlp_lm_share = 100.0 * mlp_lm_us / total_matmul_us if total_matmul_us else 0.0

    candidate_rows: list[dict[str, object]] = []
    roofline_rows: list[dict[str, object]] = []
    priority_rows: list[dict[str, object]] = []

    for rank_base, category in enumerate(CANDIDATE_ORDER, start=1):
        data = by_category.get(category, {})
        total_us = data.get("total_us", 0.0)
        decode_us = data.get("decode_us", 0.0)
        prefill_us = data.get("prefill_us", 0.0)
        matmul_share = 100.0 * total_us / total_matmul_us if total_matmul_us else 0.0
        decode_share = 100.0 * decode_us / stats["decode_matmul_us"] if stats["decode_matmul_us"] else 0.0
        prefill_share = 100.0 * prefill_us / stats["prefill_matmul_us"] if stats["prefill_matmul_us"] else 0.0
        input_dim, output_dim = shapes[category]
        macs = input_dim * output_dim
        weight_bytes = macs
        activation_bytes = input_dim
        output_bytes = output_dim * 4
        total_bytes = weight_bytes + activation_bytes + output_bytes
        compute_cycles = math.ceil(macs / max(args.mac_lanes, 1))
        compute_us = compute_cycles / (args.clock_mhz * 1_000_000.0) * 1_000_000.0
        bandwidth_us = total_bytes / (args.bandwidth_mbps * 1_000_000.0) * 1_000_000.0
        bound = "bandwidth-bound" if bandwidth_us > compute_us else "compute-bound"
        bandwidth_risk = "high" if category == "lm_head" or bandwidth_us > compute_us * 2 else "medium" if bandwidth_us > compute_us else "low"
        priority_score = (matmul_share * 0.55) + (decode_share * 0.35) - (5.0 if bandwidth_risk == "high" else 0.0) - rank_base * 0.05

        candidate_rows.append({
            "category": category,
            "total_ms": round(total_us / 1000.0, 3),
            "decode_ms": round(decode_us / 1000.0, 3),
            "prefill_ms": round(prefill_us / 1000.0, 3),
            "matmul_share_pct": round(matmul_share, 2),
            "decode_matmul_share_pct": round(decode_share, 2),
            "prefill_matmul_share_pct": round(prefill_share, 2),
            "call_count": int(data.get("call_count", 0)),
            "representative_input_dim": input_dim,
            "representative_output_dim": output_dim,
            "design_note": ARCH_NOTES[category],
        })
        roofline_rows.append({
            "category": category,
            "representative_input_dim": input_dim,
            "representative_output_dim": output_dim,
            "int8_macs_per_token_est": macs,
            "weight_bytes_int8_stream_est": weight_bytes,
            "activation_bytes_int8_est": activation_bytes,
            "accumulator_output_bytes_int32_est": output_bytes,
            "assumed_mac_lanes": args.mac_lanes,
            "assumed_clock_mhz": args.clock_mhz,
            "assumed_stream_bandwidth_mbps": args.bandwidth_mbps,
            "compute_time_us_est": round(compute_us, 3),
            "stream_time_us_est": round(bandwidth_us, 3),
            "likely_bound": bound,
            "bandwidth_risk": bandwidth_risk,
        })
        priority_rows.append({
            "priority_rank": 0,
            "category": category,
            "priority_score": round(priority_score, 3),
            "rationale": ARCH_NOTES[category],
            "claim_limit": "Design estimate only; do not interpret as measured FPGA speedup.",
        })

    priority_rows.sort(key=lambda row: row["priority_score"], reverse=True)
    for idx, row in enumerate(priority_rows, start=1):
        row["priority_rank"] = idx

    write_csv(tables_dir / "fpga_decode_accel_candidate_ops.csv", candidate_rows)
    write_csv(tables_dir / "fpga_decode_accel_roofline_estimate.csv", roofline_rows)
    write_csv(tables_dir / "fpga_decode_accel_priority.csv", priority_rows)

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    graph_line = "not available"
    if graph:
        graph_line = (
            f"{graph.get('node_count')} nodes, {graph.get('matmul_count')} MatMul nodes, "
            f"cache I/O {graph.get('cache_inputs')}/{graph.get('cache_outputs')}, "
            f"decode cache reuse ready={graph.get('decode_cache_reuse_ready')}"
        )
    top_priority = ", ".join(row["category"] for row in priority_rows[:3])
    summary_path.write_text(
        "\n".join([
            "# FPGA Decode MatVec Accelerator Model Summary",
            "",
            "## Scope",
            "",
            "This summary uses the existing ONNX Runtime MatMul category table as profiling evidence. "
            "The roofline-style values are architecture estimates for a candidate INT8 tiled MatVec/MatMul datapath, not measured speedup.",
            "",
            "## Inputs",
            "",
            f"- MatMul category CSV: `{category_path}`",
            f"- Top-node shape CSV: `{top_nodes_path}`",
            f"- ONNX graph inspection: {graph_line}",
            "",
            "## Profiling Implication",
            "",
            f"- MatMul share of traced phase time: {stats['total_matmul_share_pct']:.1f}%",
            f"- Decode MatMul share: {stats['decode_matmul_share_pct']:.1f}%",
            f"- Prefill MatMul share: {stats['prefill_matmul_share_pct']:.1f}%",
            f"- `mlp_projection + lm_head` share of MatMul time: {mlp_lm_share:.2f}%",
            "",
            "The current evidence therefore does not support a MatMul-free direction or a QK-only accelerator story. "
            "The first FPGA optimization target should be a decode-stage dense tiled MatVec/MatMul datapath, with QK remaining one primitive among several.",
            "",
            "## Candidate Priority",
            "",
            f"- Highest estimated priorities: {top_priority}",
            "- `lm_head` requires tiled/streaming treatment because the representative vocabulary projection output dimension is very large.",
            "- KV-cache remains a structural memory-pressure factor and should inform stream/cache interfaces, but it is not treated as the single proven bottleneck.",
            "",
            "## Generated Tables",
            "",
            "- `paper_assets/tables/fpga_decode_accel_candidate_ops.csv`",
            "- `paper_assets/tables/fpga_decode_accel_roofline_estimate.csv`",
            "- `paper_assets/tables/fpga_decode_accel_priority.csv`",
            "",
        ])
    )


if __name__ == "__main__":
    main()
