#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from collect_quartus_reports import (
    OPTIONAL_PATTERNS,
    REQUIRED_PATTERNS,
    extract_entity_rows,
    extract_resource_rows_from_fit,
    extract_timing_rows,
    find_first,
    format_path,
    get_search_dirs,
    read_text,
    write_csv,
)


SUPPORTED_DIMS = [16, 32, 64, 128]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect Quartus dim-sweep reports and emit paper-ready resource/timing/latency CSV tables."
    )
    parser.add_argument("--quartus-root", required=True, help="Quartus dim-sweep project root")
    parser.add_argument("--out-dir", required=True, help="Repository root for generated CSVs")
    parser.add_argument("--sim-csv", default="", help="Optional simulation sweep CSV path")
    parser.add_argument("--dims", nargs="+", type=int, default=SUPPORTED_DIMS, help="Dims to collect")
    return parser.parse_args()


def read_sim_rows(path: Path | None) -> dict[int, dict[str, str]]:
    if path is None or not path.is_file():
        return {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return {int(row["dim"]): row for row in reader}


def preferred_fmax_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    fmax_rows = [row for row in rows if row["analysis"] == "Fmax" and row["fmax_mhz"]]
    if not fmax_rows:
        return None
    for row in fmax_rows:
        if "Slow 85C" in row["corner"]:
            return row
    return fmax_rows[0]


def load_project_reports(project_dir: Path) -> tuple[dict[str, Path], dict[str, Path | None]]:
    search_dirs = get_search_dirs(project_dir)
    required_reports: dict[str, Path] = {}
    missing_required: list[str] = []

    for key, pattern in REQUIRED_PATTERNS.items():
        path = find_first(search_dirs, pattern)
        if path:
            required_reports[key] = path
        else:
            missing_required.append(pattern)

    if missing_required:
        raise FileNotFoundError(
            "required Quartus dim-sweep report files were not found.\n"
            f"searched under: {', '.join(str(path) for path in search_dirs)}\n"
            f"missing patterns: {', '.join(missing_required)}\n"
            "hint: run 'nix develop -c just quartus-dim-sweep' first."
        )

    optional_reports = {key: find_first(search_dirs, pattern) for key, pattern in OPTIONAL_PATTERNS.items()}
    return required_reports, optional_reports


def collect_rows_for_dim(project_dir: Path, dim: int) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, str] | None]:
    required_reports, optional_reports = load_project_reports(project_dir)
    fit_summary_text = read_text(required_reports["fit_summary"])
    map_rpt_text = read_text(optional_reports["map_rpt"]) if optional_reports["map_rpt"] else ""
    sta_summary_text = read_text(required_reports["sta_summary"])
    sta_rpt_text = read_text(optional_reports["sta_rpt"]) if optional_reports["sta_rpt"] else None

    resource_rows = [
        {
            "dim": str(dim),
            **row,
        }
        for row in extract_resource_rows_from_fit(fit_summary_text, required_reports["fit_summary"])
    ]

    entity_rows = []
    if optional_reports["map_rpt"]:
        entity_rows = extract_entity_rows(
            map_rpt_text,
            optional_reports["map_rpt"],
            wanted_entities={f"DotProductInt8_dim{dim}", f"DotProductInt8SweepTop_dim{dim}"},
            entity_labels={
                f"DotProductInt8_dim{dim}": "int8_qk_dot_product_core",
                f"DotProductInt8SweepTop_dim{dim}": "sweep_top_wrapper",
            },
        )
    resource_rows.extend({"dim": str(dim), **row} for row in entity_rows)

    timing_rows = [
        {
            "dim": str(dim),
            **row,
        }
        for row in extract_timing_rows(
            sta_summary_text,
            sta_rpt_text,
            required_reports["sta_summary"],
            optional_reports["sta_rpt"],
        )
    ]

    return resource_rows, timing_rows, preferred_fmax_row(timing_rows)


def build_latency_row(dim: int, fmax_row: dict[str, str] | None, sim_row: dict[str, str] | None) -> dict[str, str]:
    estimated_cycles = dim + 1
    board_clock_mhz = 50.0
    row = {
        "dim": str(dim),
        "mac_cycles": str(dim),
        "estimated_cycles_sequential_mac": str(estimated_cycles),
        "board_clock_mhz": f"{board_clock_mhz:.1f}",
        "estimated_latency_us_50mhz": f"{estimated_cycles / board_clock_mhz:.3f}",
        "observed_cycles_from_sim": sim_row.get("observed_cycles", "") if sim_row else "",
        "observed_latency_us_50mhz": (
            f"{float(sim_row['observed_cycles']) / board_clock_mhz:.3f}" if sim_row and sim_row.get("observed_cycles") else ""
        ),
        "fmax_corner": "",
        "fmax_mhz": "",
        "theoretical_latency_us_at_fmax": "",
        "notes": "Sequential single-MAC INT8 QK dot-product estimate. This is a primitive-level latency estimate only.",
    }

    if fmax_row and fmax_row.get("fmax_mhz"):
        fmax_mhz = float(fmax_row["fmax_mhz"])
        row["fmax_corner"] = fmax_row["corner"]
        row["fmax_mhz"] = f"{fmax_mhz:.3f}"
        row["theoretical_latency_us_at_fmax"] = f"{estimated_cycles / fmax_mhz:.3f}"

    return row


def main() -> int:
    args = parse_args()
    quartus_root = Path(args.quartus_root).resolve()
    out_dir = Path(args.out_dir).resolve()
    sim_path = Path(args.sim_csv).resolve() if args.sim_csv else None

    if not quartus_root.is_dir():
        print(
            f"error: Quartus dim-sweep root does not exist: {quartus_root}\n"
            "hint: run 'nix develop -c just quartus-dim-sweep' first.",
            file=sys.stderr,
        )
        return 1

    sim_rows = read_sim_rows(sim_path)
    resource_rows: list[dict[str, str]] = []
    timing_rows: list[dict[str, str]] = []
    latency_rows: list[dict[str, str]] = []

    for dim in args.dims:
        project_dir = quartus_root / "projects" / f"dim{dim}"
        if not project_dir.is_dir():
            print(
                f"error: missing Quartus project directory for dim={dim}: {project_dir}\n"
                "hint: run 'nix develop -c just quartus-dim-sweep' first.",
                file=sys.stderr,
            )
            return 1

        try:
            dim_resource_rows, dim_timing_rows, fmax_row = collect_rows_for_dim(project_dir, dim)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        resource_rows.extend(dim_resource_rows)
        timing_rows.extend(dim_timing_rows)
        latency_rows.append(build_latency_row(dim, fmax_row, sim_rows.get(dim)))

    resource_csv = out_dir / "paper_assets" / "tables" / "fpga_dim_sweep_resource.csv"
    timing_csv = out_dir / "paper_assets" / "tables" / "fpga_dim_sweep_timing.csv"
    latency_csv = out_dir / "paper_assets" / "tables" / "fpga_dim_sweep_latency.csv"

    write_csv(
        resource_csv,
        ["dim", "scope", "entity", "metric", "used", "total", "percent", "source_report", "notes"],
        resource_rows,
    )
    write_csv(
        timing_csv,
        ["dim", "corner", "analysis", "clock", "slack_ns", "tns_ns", "fmax_mhz", "restricted_fmax_mhz", "source_report"],
        timing_rows,
    )
    write_csv(
        latency_csv,
        [
            "dim",
            "mac_cycles",
            "estimated_cycles_sequential_mac",
            "board_clock_mhz",
            "estimated_latency_us_50mhz",
            "observed_cycles_from_sim",
            "observed_latency_us_50mhz",
            "fmax_corner",
            "fmax_mhz",
            "theoretical_latency_us_at_fmax",
            "notes",
        ],
        latency_rows,
    )

    print(f"Wrote {resource_csv}")
    print(f"Wrote {timing_csv}")
    print(f"Wrote {latency_csv}")
    if sim_path and sim_path.is_file():
        print(f"Used simulation CSV: {format_path(sim_path)}")
    else:
        print("Simulation CSV not found; latency CSV contains only estimated cycles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
