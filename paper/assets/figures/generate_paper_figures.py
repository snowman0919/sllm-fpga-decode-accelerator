#!/usr/bin/env python3

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[2]
FIGURES_DIR = ROOT / "paper_assets" / "figures"
MATMUL_CATEGORY_CSV = ROOT / "paper_assets" / "tables" / "ort_matmul_category_by_context.csv"


def save_research_flow() -> None:
    fig, ax = plt.subplots(figsize=(11.5, 6.0))
    ax.set_axis_off()

    steps = [
        ("1", "ONNX export", "local HF model\n-> exported graph"),
        ("2", "Graph inspection", "inputs, outputs,\ncache I/O"),
        ("3", "ORT profiling", "prefill/decode\ntraced node time"),
        ("4", "MatMul category\nanalysis", "projection-heavy\nhotspot split"),
        ("5", "FPGA primitive\nvalidation", "INT8 Decode MatVec\nfeasibility"),
        ("6", "Future architecture", "tiled MatVec/MatMul\naccelerator sketch"),
    ]
    colors = ["#4C78A8", "#59A14F", "#F28E2B", "#B07AA1", "#E15759", "#76B7B2"]
    positions = [(0.08, 0.63), (0.39, 0.63), (0.70, 0.63), (0.70, 0.25), (0.39, 0.25), (0.08, 0.25)]
    centers = [(x_pos + 0.11, y_pos + 0.105) for x_pos, y_pos in positions]

    for (number, title, subtitle), color, (x_pos, y_pos) in zip(steps, colors, positions):
        box = FancyBboxPatch(
            (x_pos, y_pos),
            0.22,
            0.21,
            boxstyle="round,pad=0.018,rounding_size=0.02",
            linewidth=1.4,
            edgecolor=color,
            facecolor="#F8FAFC",
            transform=ax.transAxes,
        )
        ax.add_patch(box)
        ax.text(x_pos + 0.11, y_pos + 0.165, number, ha="center", va="center", fontsize=13, weight="bold", color=color, transform=ax.transAxes)
        ax.text(x_pos + 0.11, y_pos + 0.115, title, ha="center", va="center", fontsize=10.5, weight="bold", transform=ax.transAxes)
        ax.text(x_pos + 0.11, y_pos + 0.055, subtitle, ha="center", va="center", fontsize=8.8, color="#444444", transform=ax.transAxes)

    arrow_pairs = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]
    for start_idx, end_idx in arrow_pairs:
        start = centers[start_idx]
        end = centers[end_idx]
        shrink_x = 0.13 if abs(start[1] - end[1]) < 0.02 else 0.0
        shrink_y = 0.13 if abs(start[0] - end[0]) < 0.02 else 0.0
        start_point = (start[0] + (shrink_x if end[0] > start[0] else -shrink_x), start[1] + (shrink_y if end[1] > start[1] else -shrink_y))
        end_point = (end[0] - (shrink_x if end[0] > start[0] else -shrink_x), end[1] - (shrink_y if end[1] > start[1] else -shrink_y))
        arrow = FancyArrowPatch(
            start_point,
            end_point,
            arrowstyle="-|>",
            mutation_scale=13,
            linewidth=1.3,
            color="#6B7280",
            transform=ax.transAxes,
        )
        ax.add_patch(arrow)

    ax.text(
        0.5,
        0.08,
        "Evidence layers remain separate: ONNX graph, ORT runtime profiling, host-side PyTorch reference, FPGA primitive validation.",
        ha="center",
        va="center",
        fontsize=10,
        color="#333333",
        transform=ax.transAxes,
    )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "research_flow.png", dpi=220)
    plt.close(fig)


def save_matmul_phase_share() -> None:
    labels = ["prefill + decode", "prefill", "decode"]
    values = [67.5, 53.4, 81.1]
    colors = ["#4C78A8", "#59A14F", "#F28E2B"]

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    bars = ax.bar(labels, values, color=colors, width=0.62)
    ax.set_ylim(0, 100)
    ax.set_ylabel("MatMul share of traced phase time (%)")
    ax.set_title("ONNX Runtime MatMul share by traced phase")
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 2.0, f"{value:.1f}%", ha="center", va="bottom", fontsize=10.5)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "ort_matmul_phase_share.png", dpi=220)
    plt.close(fig)


def load_global_matmul_category_share() -> list[tuple[str, float]]:
    totals: dict[str, float] = defaultdict(float)
    with MATMUL_CATEGORY_CSV.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            category = row["category"]
            totals[category] += float(row["total_us"])

    order = [
        "mlp_projection",
        "lm_head",
        "attention_qkv_projection",
        "attention_output_projection",
        "attention_v_weighted_sum",
        "unknown",
    ]
    grand_total = sum(totals.values())
    return [(category, totals[category] * 100.0 / grand_total) for category in order]


def save_matmul_category_breakdown() -> None:
    category_shares = load_global_matmul_category_share()
    labels = [category for category, _share in category_shares]
    values = [share for _category, share in category_shares]
    colors = ["#66CCEE", "#AA3377", "#4477AA", "#CCBB44", "#228833", "#BBBBBB"]

    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    y_positions = list(range(len(labels)))
    bars = ax.barh(y_positions, values, color=colors)
    ax.set_yticks(y_positions, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 70)
    ax.set_xlabel("Share of total MatMul time (%)")
    ax.set_title("ORT MatMul category breakdown")
    ax.grid(axis="x", color="#DDDDDD", linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values):
        ax.text(value + 1.0, bar.get_y() + bar.get_height() / 2, f"{value:.2f}%", va="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "ort_matmul_category_breakdown.png", dpi=220)
    plt.close(fig)


def add_box(ax, xy: tuple[float, float], text: str, color: str, width: float = 0.18, height: float = 0.12) -> None:
    x_pos, y_pos = xy
    box = FancyBboxPatch(
        (x_pos, y_pos),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=1.4,
        edgecolor=color,
        facecolor="#F8FAFC",
        transform=ax.transAxes,
    )
    ax.add_patch(box)
    ax.text(x_pos + width / 2, y_pos + height / 2, text, ha="center", va="center", fontsize=10, weight="bold", transform=ax.transAxes)


def add_arrow(ax, start: tuple[float, float], end: tuple[float, float], color: str = "#6B7280") -> None:
    arrow = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=13, linewidth=1.3, color=color, transform=ax.transAxes)
    ax.add_patch(arrow)


def save_architecture_diagram() -> None:
    fig, ax = plt.subplots(figsize=(12.5, 7.2))
    ax.set_axis_off()

    add_box(ax, (0.04, 0.76), "ONNX Runtime\n/ Host", "#4C78A8", 0.18, 0.13)
    add_box(ax, (0.30, 0.76), "Host/ORT\noffload boundary", "#E15759", 0.19, 0.13)
    add_box(ax, (0.75, 0.76), "Cache-aware\ninterface", "#59A14F", 0.19, 0.13)

    add_box(ax, (0.34, 0.52), "Activation\nbuffer", "#4C78A8", 0.17, 0.12)
    add_box(ax, (0.57, 0.52), "INT8 tiled\nMatVec engine", "#F28E2B", 0.20, 0.12)
    add_box(ax, (0.80, 0.52), "Output tile\nbuffer", "#76B7B2", 0.17, 0.12)

    add_box(ax, (0.34, 0.27), "Weight tile\nstreamer", "#B07AA1", 0.17, 0.12)
    add_box(ax, (0.585, 0.27), "INT32\naccumulator", "#F28E2B", 0.17, 0.12)
    add_box(ax, (0.80, 0.27), "Scale /\nrequant unit", "#76B7B2", 0.17, 0.12)

    add_arrow(ax, (0.22, 0.825), (0.30, 0.825))
    add_arrow(ax, (0.49, 0.825), (0.75, 0.825))
    add_arrow(ax, (0.395, 0.76), (0.405, 0.64))
    add_arrow(ax, (0.35, 0.76), (0.38, 0.39))
    add_arrow(ax, (0.51, 0.58), (0.57, 0.58))
    add_arrow(ax, (0.51, 0.33), (0.57, 0.54))
    add_arrow(ax, (0.67, 0.52), (0.67, 0.39))
    add_arrow(ax, (0.755, 0.33), (0.80, 0.33))
    add_arrow(ax, (0.885, 0.39), (0.885, 0.52))
    add_arrow(ax, (0.885, 0.64), (0.845, 0.76))

    ax.plot([0.27, 0.27], [0.18, 0.93], color="#E15759", linewidth=1.2, linestyle="--", transform=ax.transAxes)
    ax.text(0.275, 0.925, "offload boundary", ha="left", va="center", fontsize=9, color="#E15759", transform=ax.transAxes)
    ax.text(
        0.5,
        0.09,
        "Projection-general tiled data path for MLP projection, attention projection, and lm_head output tiling; current evidence remains primitive-level.",
        ha="center",
        va="center",
        fontsize=10,
        color="#333333",
        transform=ax.transAxes,
    )

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fpga_decode_accelerator_architecture.png", dpi=220)
    plt.close(fig)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    save_research_flow()
    save_matmul_phase_share()
    save_matmul_category_breakdown()
    save_architecture_diagram()


if __name__ == "__main__":
    main()
