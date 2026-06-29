#!/usr/bin/env python3
"""Build measured/projected ONNX Runtime vs FPGA primitive comparison artifacts."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = PROJECT_ROOT / "paper_assets/tables"
FIGURE_DIR = PROJECT_ROOT / "paper_assets/figures"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-csv", default=str(TABLE_DIR / "ort_vs_fpga_measured_and_projected_comparison.csv"))
    parser.add_argument("--out-md", default=str(PROJECT_ROOT / "docs/ort_vs_fpga_comparison_interpretation.md"))
    parser.add_argument("--out-fig", default=str(FIGURE_DIR / "ort_vs_fpga_latency_decomposition.png"))
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def first_row(path: Path, **filters: str) -> dict[str, str] | None:
    for row in read_rows(path):
        if all(str(row.get(key, "")) == value for key, value in filters.items()):
            return row
    rows = read_rows(path)
    return rows[0] if rows else None


def fnum(value: object) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(str(value))
    except ValueError:
        return None


def latency_fields(ms: float | None) -> tuple[str, str]:
    if ms is None:
        return "", ""
    return f"{ms:.9f}", f"{ms * 1000.0:.6f}"


def comparison_rows() -> list[dict[str, object]]:
    aligned = TABLE_DIR / "onnx_runtime_aligned_micrograph_baseline.csv"
    integer = TABLE_DIR / "onnx_runtime_integer_micrograph_baseline.csv"
    jtag = TABLE_DIR / "fpga_jtag_primitive_benchmark.csv"
    cycles = TABLE_DIR / "fpga_jtag_cycle_counter_summary.csv"
    projected = TABLE_DIR / "fpga_optimized_interface_estimate.csv"

    rows: list[dict[str, object]] = []
    cpu = first_row(aligned, backend="cpu_numpy_primitive_baseline")
    if cpu:
        latency_ms = fnum(cpu.get("latency_ms_mean"))
        ms, us = latency_fields(latency_ms)
        rows.append(
            {
                "backend": "CPU NumPy primitive baseline",
                "evidence_type": "measured",
                "interface": cpu.get("interface", "host_numpy"),
                "dtype": cpu.get("dtype", "int8_inputs_int32_accum"),
                "input_dim": cpu.get("input_dim", "16"),
                "output_dim": cpu.get("output_dim", "4"),
                "macs": cpu.get("macs", "64"),
                "correctness_pass": cpu.get("correctness_pass", ""),
                "latency_ms": ms,
                "latency_us": us,
                "latency_source": cpu.get("latency_source", "host wall time"),
                "measured_or_projected": "measured",
                "claim_boundary": "host-side primitive baseline; not ONNX Runtime profiling",
                "note": cpu.get("note", ""),
            }
        )

    ort = first_row(aligned, backend="onnxruntime_matvec_micrograph")
    if ort:
        latency_ms = fnum(ort.get("latency_ms_mean"))
        ms, us = latency_fields(latency_ms)
        rows.append(
            {
                "backend": "ONNX Runtime MatVec micrograph",
                "evidence_type": "measured",
                "interface": ort.get("interface", "CPUExecutionProvider"),
                "dtype": ort.get("dtype", "float32"),
                "input_dim": ort.get("input_dim", "16"),
                "output_dim": ort.get("output_dim", "4"),
                "macs": ort.get("macs", "64"),
                "correctness_pass": ort.get("correctness_pass", ""),
                "latency_ms": ms,
                "latency_us": us,
                "latency_source": ort.get("latency_source", "ORT CPUExecutionProvider"),
                "measured_or_projected": "measured",
                "claim_boundary": "aligned micrograph baseline only; not full Gemma ONNX Runtime profiling",
                "note": ort.get("dtype_boundary", ""),
            }
        )

    ort_int = first_row(integer, backend="onnxruntime_matmulinteger_micrograph")
    if ort_int:
        latency_ms = fnum(ort_int.get("latency_ms_mean"))
        ms, us = latency_fields(latency_ms)
        rows.append(
            {
                "backend": "ONNX Runtime MatMulInteger micrograph",
                "evidence_type": "measured",
                "interface": ort_int.get("interface", "CPUExecutionProvider"),
                "dtype": ort_int.get("dtype", "int8_inputs_int32_output"),
                "input_dim": ort_int.get("input_dim", "16"),
                "output_dim": ort_int.get("output_dim", "4"),
                "macs": ort_int.get("macs", "64"),
                "correctness_pass": ort_int.get("correctness_pass", ""),
                "latency_ms": ms,
                "latency_us": us,
                "latency_source": ort_int.get("latency_source", "ORT CPUExecutionProvider MatMulInteger"),
                "measured_or_projected": "measured",
                "claim_boundary": "integer micrograph baseline only; not full Gemma ONNX Runtime profiling",
                "note": ort_int.get("note", ""),
            }
        )

    jtag_row = first_row(jtag, backend="fpga_jtag_register_offload")
    if jtag_row:
        latency_ms = fnum(jtag_row.get("total_wall_latency_ms_mean") or jtag_row.get("total_latency_ms_mean"))
        ms, us = latency_fields(latency_ms)
        measured_kind = "measured" if latency_ms is not None else "measured_correctness_only"
        rows.append(
            {
                "backend": "FPGA JTAG total invocation",
                "evidence_type": "measured",
                "interface": jtag_row.get("interface", "jtag_to_avalon"),
                "dtype": "int8_inputs_int32_accum",
                "input_dim": jtag_row.get("input_dim", "16"),
                "output_dim": jtag_row.get("output_dim", "4"),
                "macs": jtag_row.get("macs", "64"),
                "correctness_pass": jtag_row.get("correctness_pass", ""),
                "latency_ms": ms,
                "latency_us": us,
                "latency_source": "System Console/JTAG total wall time" if latency_ms is not None else "not archived in current success record",
                "measured_or_projected": measured_kind,
                "claim_boundary": "JTAG invocation overhead; not compute speed",
                "note": jtag_row.get("tool_overhead_note", ""),
            }
        )

    cycle_row = first_row(cycles, backend="fpga_internal_cycle_counter")
    if cycle_row:
        latency_us = fnum(cycle_row.get("compute_time_us_50mhz_mean"))
        latency_ms = latency_us / 1000.0 if latency_us is not None else None
        ms, us = latency_fields(latency_ms)
        rows.append(
            {
                "backend": "FPGA internal compute cycles",
                "evidence_type": "measured",
                "interface": cycle_row.get("interface", "jtag_to_avalon_register_bank"),
                "dtype": "int8_inputs_int32_accum",
                "input_dim": cycle_row.get("input_dim", "16"),
                "output_dim": cycle_row.get("output_dim", "4"),
                "macs": cycle_row.get("macs", "64"),
                "correctness_pass": cycle_row.get("correctness_pass", ""),
                "latency_ms": ms,
                "latency_us": us,
                "latency_source": "FPGA COMPUTE_CYCLES register at 50 MHz",
                "measured_or_projected": "measured",
                "claim_boundary": cycle_row.get("claim_boundary", "primitive internal cycle measurement only"),
                "note": f"compute_cycles_mean={cycle_row.get('compute_cycles_mean', '')}",
            }
        )
    else:
        rows.append(
            {
                "backend": "FPGA internal compute cycles",
                "evidence_type": "pending_hardware_measurement",
                "interface": "jtag_to_avalon_register_bank",
                "dtype": "int8_inputs_int32_accum",
                "input_dim": "16",
                "output_dim": "4",
                "macs": "64",
                "correctness_pass": "",
                "latency_ms": "",
                "latency_us": "",
                "latency_source": "FPGA COMPUTE_CYCLES register",
                "measured_or_projected": "pending",
                "claim_boundary": "do not report as measured until a real board log reads COMPUTE_CYCLES",
                "note": "No cycle-counter board log is present in this repository state.",
            }
        )

    projected_rows = [
        row
        for row in read_rows(projected)
        if row.get("model_component") == "optimized_interface_estimate"
        and row.get("interface") == "ideal_register_batch"
        and row.get("assumption_case") == "nominal"
    ]
    if projected_rows:
        proj = projected_rows[0]
        latency_us = fnum(proj.get("optimized_interface_latency_us_fmax"))
        latency_ms = latency_us / 1000.0 if latency_us is not None else fnum(proj.get("optimized_interface_latency_ms"))
        ms, us = latency_fields(latency_ms)
        rows.append(
            {
                "backend": "FPGA optimized interface estimate",
                "evidence_type": "projected",
                "interface": proj.get("interface", "ideal_register_batch"),
                "dtype": "int8_inputs_int32_accum",
                "input_dim": proj.get("input_dim", "16"),
                "output_dim": proj.get("output_dim", "4"),
                "macs": proj.get("macs", "64"),
                "correctness_pass": "",
                "latency_ms": ms,
                "latency_us": us,
                "latency_source": "weight-preloaded low-overhead host interface model",
                "measured_or_projected": "projected",
                "claim_boundary": "design estimate only; not measured board latency",
                "note": (
                    f"{proj.get('estimate_boundary', '')}; "
                    f"compute_time_us_50mhz={proj.get('compute_time_us_50mhz', '')}; "
                    f"compute_time_us_fmax={proj.get('compute_time_us_fmax', '')}; "
                    f"clock_hz_fmax={proj.get('clock_hz_fmax', '')}"
                ),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# ORT vs FPGA Comparison Interpretation",
        "",
        "This comparison separates measured host baselines, measured JTAG correctness/invocation evidence, pending FPGA cycle-counter evidence, and projected optimized-interface estimates.",
        "",
        "| backend | evidence | latency source | latency us | boundary |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['backend']} | {row['evidence_type']} | {row['latency_source']} | {row['latency_us']} | {row['claim_boundary']} |"
        )
    lines.extend(
        [
            "",
            "JTAG-to-Avalon total latency is not FPGA compute latency. It includes System Console execution, JTAG service access, register writes/reads, and polling.",
            "",
            "Any future FPGA cycle-counter value should be described as fixed primitive compute latency only. It must not be used to claim full-model, full Gemma, custom-op, or end-to-end ONNX Runtime speedup.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_figure(path: Path, rows: list[dict[str, object]]) -> None:
    plotted = [
        row
        for row in rows
        if row.get("latency_us") not in ("", None)
        and row.get("measured_or_projected") in {"measured", "projected"}
    ]
    if not plotted:
        return
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return
    labels = [str(row["backend"]).replace(" ", "\n") for row in plotted]
    values = [float(str(row["latency_us"])) for row in plotted]
    colors = ["#4c78a8" if row["measured_or_projected"] == "measured" else "#f58518" for row in plotted]
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(labels, values, color=colors)
    ax.set_ylabel("Latency (us, log scale)")
    ax.set_yscale("log")
    ax.set_title("Primitive Latency: Measured Baselines vs Projected FPGA Interface")
    ax.grid(axis="y", which="both", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    rows = comparison_rows()
    write_csv(Path(args.out_csv), rows)
    write_md(Path(args.out_md), rows)
    write_figure(Path(args.out_fig), rows)
    print(f"wrote {args.out_csv}")
    print(f"wrote {args.out_md}")
    if Path(args.out_fig).exists():
        print(f"wrote {args.out_fig}")


if __name__ == "__main__":
    main()
