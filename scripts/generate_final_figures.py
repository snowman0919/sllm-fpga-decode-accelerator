#!/usr/bin/env python3
"""Generate final paper figures from paper_assets tables."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "paper_assets/tables"
FIG_DIR = ROOT / "paper_assets/figures"


def add_box(ax, xy: tuple[float, float], text: str, color: str, width: float = 0.2, height: float = 0.12) -> None:
    x, y = xy
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=1.3,
        edgecolor=color,
        facecolor="#F8FAFC",
        transform=ax.transAxes,
    )
    ax.add_patch(box)
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=9.6, weight="bold", transform=ax.transAxes)


def add_arrow(ax, start: tuple[float, float], end: tuple[float, float], color: str = "#6B7280") -> None:
    ax.add_patch(
        FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=13, linewidth=1.2, color=color, transform=ax.transAxes)
    )


def save_research_flow() -> None:
    fig, ax = plt.subplots(figsize=(11.5, 5.8))
    ax.set_axis_off()
    steps = [
        ("Y700/Android\nenvironment", "ADB, thermal,\nruntime path"),
        ("ORT micrographs", "CPU, NNAPI,\nQNN attempts"),
        ("Decode bottleneck\nanalysis", "operator and\nmicrograph evidence"),
        ("FPGA core\nvalidation", "INT8 MatVec\ncycle anchor"),
        ("Roofline/interface\nmodel", "bandwidth and\noffload boundary"),
        ("Architecture\nproposal", "tiled INT8\nMatVec structure"),
    ]
    positions = [(0.05, 0.62), (0.37, 0.62), (0.69, 0.62), (0.69, 0.28), (0.37, 0.28), (0.05, 0.28)]
    colors = ["#4C78A8", "#59A14F", "#F28E2B", "#B07AA1", "#E15759", "#76B7B2"]
    centers = []
    for (title, subtitle), pos, color in zip(steps, positions, colors):
        add_box(ax, pos, f"{title}\n{subtitle}", color, width=0.22, height=0.18)
        centers.append((pos[0] + 0.11, pos[1] + 0.09))
    for s, e in [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]:
        start = centers[s]
        end = centers[e]
        dx = 0.13 if abs(start[1] - end[1]) < 0.02 else 0
        dy = 0.11 if abs(start[0] - end[0]) < 0.02 else 0
        add_arrow(
            ax,
            (start[0] + (dx if end[0] > start[0] else -dx), start[1] + (dy if end[1] > start[1] else -dy)),
            (end[0] - (dx if end[0] > start[0] else -dx), end[1] - (dy if end[1] > start[1] else -dy)),
        )
    ax.text(
        0.5,
        0.11,
        "Evidence types are kept separate: measured Android results, board-measured FPGA cycles, simulation, and projected models.",
        ha="center",
        va="center",
        fontsize=10,
        color="#333333",
        transform=ax.transAxes,
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "research_flow.png", dpi=220)
    plt.close(fig)


def save_architecture() -> None:
    fig, ax = plt.subplots(figsize=(12.0, 6.6))
    ax.set_axis_off()
    add_box(ax, (0.04, 0.74), "ONNX Runtime\n/ Android host", "#4C78A8", 0.19, 0.13)
    add_box(ax, (0.30, 0.74), "Offload\nboundary", "#E15759", 0.16, 0.13)
    add_box(ax, (0.78, 0.74), "Cache-aware\nruntime state", "#59A14F", 0.18, 0.13)
    add_box(ax, (0.30, 0.49), "Activation\nbuffer", "#4C78A8", 0.17, 0.12)
    add_box(ax, (0.53, 0.49), "INT8 tiled\nMatVec lanes", "#F28E2B", 0.19, 0.12)
    add_box(ax, (0.78, 0.49), "Output tile\nbuffer", "#76B7B2", 0.18, 0.12)
    add_box(ax, (0.30, 0.25), "Weight tile\nstreamer", "#B07AA1", 0.17, 0.12)
    add_box(ax, (0.54, 0.25), "INT32\naccumulator", "#F28E2B", 0.17, 0.12)
    add_box(ax, (0.78, 0.25), "Scale/requant\nor host reduce", "#76B7B2", 0.18, 0.12)
    for start, end in [
        ((0.23, 0.805), (0.30, 0.805)),
        ((0.46, 0.805), (0.78, 0.805)),
        ((0.385, 0.74), (0.385, 0.61)),
        ((0.385, 0.49), (0.385, 0.37)),
        ((0.47, 0.55), (0.53, 0.55)),
        ((0.47, 0.31), (0.53, 0.51)),
        ((0.625, 0.49), (0.625, 0.37)),
        ((0.71, 0.31), (0.78, 0.31)),
        ((0.87, 0.37), (0.87, 0.49)),
        ((0.87, 0.61), (0.87, 0.74)),
    ]:
        add_arrow(ax, start, end)
    ax.plot([0.265, 0.265], [0.18, 0.91], color="#E15759", linewidth=1.1, linestyle="--", transform=ax.transAxes)
    ax.text(0.27, 0.91, "host/hardware boundary", ha="left", va="center", fontsize=9, color="#E15759", transform=ax.transAxes)
    ax.text(
        0.5,
        0.08,
        "Current board evidence validates the INT8 MatVec core only; streamers, quantization path, and low-overhead interface remain proposal components.",
        ha="center",
        va="center",
        fontsize=9.6,
        color="#333333",
        transform=ax.transAxes,
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fpga_tiled_matvec_architecture.png", dpi=220)
    plt.close(fig)


def save_roofline_bars() -> None:
    rows = []
    with (TABLE_DIR / "projection_tile_roofline.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["assumed_lanes"] == "16" and row["bandwidth_case"] in {"usb3_stream_320_MBps", "axi_dma_1000_MBps"}:
                if row["component"] in {"mlp_gate_or_up_projection", "lm_head_full_projection", "lm_head_4096_vocab_tile"}:
                    rows.append(row)
    labels = []
    compute = []
    stream = []
    for row in rows:
        labels.append(f"{row['component'].replace('_', ' ')}\n{row['bandwidth_case'].replace('_', ' ')}")
        compute.append(float(row["compute_time_us_est"]) / 1000.0)
        stream.append(float(row["stream_time_us_est"]) / 1000.0)
    fig, ax = plt.subplots(figsize=(12.0, 5.8))
    x = range(len(labels))
    width = 0.38
    ax.bar([i - width / 2 for i in x], compute, width, label="compute model", color="#4C78A8")
    ax.bar([i + width / 2 for i in x], stream, width, label="stream model", color="#F28E2B")
    ax.set_yscale("log")
    ax.set_ylabel("Projected time (ms, log scale)")
    ax.set_title("Projection-scale compute and stream model (projected, not measured)")
    ax.set_xticks(list(x), labels, rotation=20, ha="right")
    ax.grid(axis="y", which="both", color="#DDDDDD", linewidth=0.8)
    ax.legend()
    ax.text(
        0.5,
        -0.31,
        "Rows use 16 assumed lanes at 50 MHz. They are design-space estimates, separate from the 16x4 board-measured core.",
        ha="center",
        va="center",
        fontsize=9.3,
        transform=ax.transAxes,
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fpga_roofline_or_latency_decomposition.png", dpi=220)
    plt.close(fig)


def save_y700_status() -> None:
    rows = []
    table = TABLE_DIR / "y700_operator_or_micrograph_summary.csv"
    if table.exists():
        with table.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["role"] != "smoke_16x4" and row["kind"] == "matmulinteger":
                    rows.append(row)
    if not rows:
        fig, ax = plt.subplots(figsize=(8.5, 4.8))
        ax.set_axis_off()
        add_box(ax, (0.30, 0.53), "Y700 ADB status\nno result", "#E15759", 0.40, 0.20)
        ax.text(
            0.5,
            0.34,
            "No Y700 ONNX Runtime latency is available yet.",
            ha="center",
            va="center",
            fontsize=11,
            color="#333333",
            transform=ax.transAxes,
        )
        fig.tight_layout()
        fig.savefig(FIG_DIR / "y700_onnx_runtime_bottleneck.png", dpi=220)
        plt.close(fig)
        return

    label_map = {
        "attention_output_projection": "Attention output\n1024x1152",
        "lm_head_tile": "lm_head tile\n1152x4096",
        "mlp_projection": "MLP projection\n1152x6912",
    }
    roles = ["attention_output_projection", "lm_head_tile", "mlp_projection"]
    providers = ["CPU", "NNAPI"]
    values = {provider: [] for provider in providers}
    for role in roles:
        for provider in providers:
            match = next((row for row in rows if row["role"] == role and row["execution_provider"] == provider), None)
            values[provider].append(float(match["p50_ms"]) if match else 0.0)

    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    x = list(range(len(roles)))
    width = 0.34
    ax.bar([i - width / 2 for i in x], values["CPU"], width, label="CPU EP", color="#4C78A8")
    ax.bar([i + width / 2 for i in x], values["NNAPI"], width, label="NNAPI EP", color="#59A14F")
    ax.set_xticks(x, [label_map[role] for role in roles])
    ax.set_ylabel("p50 latency (ms)")
    ax.set_title("Lenovo Y700 ONNX Runtime MatMulInteger projection micrographs")
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.8)
    ax.legend()
    ax.text(
        0.5,
        -0.23,
        "Android APK, ONNX Runtime 1.27.0, warmup=3, runs=20. QNN EP was not available in this AAR build.",
        ha="center",
        va="center",
        fontsize=9.2,
        transform=ax.transAxes,
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "y700_onnx_runtime_bottleneck.png", dpi=220)
    plt.close(fig)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    save_research_flow()
    save_architecture()
    save_roofline_bars()
    save_y700_status()
    print(f"wrote final figures under {FIG_DIR}")


if __name__ == "__main__":
    main()
