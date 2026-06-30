#!/usr/bin/env python3
"""Regenerate optimized FPGA interface estimate from the latest Quartus summary."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUARTUS_SUMMARY = PROJECT_ROOT / "assets/c11.csv"
DEFAULT_OUT = PROJECT_ROOT / "assets/c19.csv"
BOARD_CLOCK_HZ = 50_000_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quartus-summary", default=str(DEFAULT_QUARTUS_SUMMARY))
    parser.add_argument("--out-csv", default=str(DEFAULT_OUT))
    return parser.parse_args()


def read_fmax_hz(path: Path) -> tuple[int, str]:
    if not path.exists():
        return BOARD_CLOCK_HZ, "fallback board clock; Quartus summary missing"
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return BOARD_CLOCK_HZ, "fallback board clock; Quartus summary empty"
    row = rows[0]
    try:
        fmax_mhz = float(row.get("fmax_mhz", "") or 0.0)
    except ValueError:
        fmax_mhz = 0.0
    if fmax_mhz <= 0:
        return BOARD_CLOCK_HZ, "fallback board clock; Quartus Fmax unavailable"
    model = row.get("fmax_model", "Quartus Fmax")
    return int(round(fmax_mhz * 1_000_000.0)), f"Quartus {model} CLOCK_50 Fmax"


def compute_us(cycles: int, clock_hz: int) -> float:
    return cycles / clock_hz * 1_000_000.0


def transfer_us(bytes_count: int, bandwidth_mbps: float | None) -> float:
    if not bandwidth_mbps:
        return 0.0
    return bytes_count / (bandwidth_mbps * 1_000_000.0) * 1_000_000.0


def main() -> None:
    args = parse_args()
    fmax_hz, fmax_source = read_fmax_hz(Path(args.quartus_summary))
    input_dim = 16
    output_dim = 4
    macs = input_dim * output_dim
    control_overhead_cycles = 4
    activation_transfer_bytes = input_dim
    result_transfer_bytes = output_dim * 4
    transfer_bytes = activation_transfer_bytes + result_transfer_bytes
    estimate_boundary = "projected optimized-interface estimate; not measured board latency"

    rows: list[dict[str, object]] = []
    for lanes in [1, 4, 8, 16]:
        cycles = (macs + lanes - 1) // lanes + control_overhead_cycles
        rows.append(
            {
                "model_component": "compute_only_lower_bound",
                "evidence_type": "projected",
                "input_dim": input_dim,
                "output_dim": output_dim,
                "macs": macs,
                "lanes": lanes,
                "control_overhead_cycles": control_overhead_cycles,
                "cycles": cycles,
                "clock_hz_board": BOARD_CLOCK_HZ,
                "clock_hz_fmax": fmax_hz,
                "clock_source_fmax": fmax_source,
                "compute_time_us_50mhz": f"{compute_us(cycles, BOARD_CLOCK_HZ):.9f}",
                "compute_time_us_fmax": f"{compute_us(cycles, fmax_hz):.9f}",
                "weight_preloaded": True,
                "activation_transfer_bytes": activation_transfer_bytes,
                "result_transfer_bytes": result_transfer_bytes,
                "interface": "compute_only",
                "assumption_case": "lower_bound",
                "driver_overhead_us": 0,
                "assumed_transfer_bandwidth_MBps": "",
                "transfer_time_us": "0.000000",
                "optimized_interface_latency_us_50mhz": f"{compute_us(cycles, BOARD_CLOCK_HZ):.9f}",
                "optimized_interface_latency_us_fmax": f"{compute_us(cycles, fmax_hz):.9f}",
                "optimized_interface_latency_ms": f"{compute_us(cycles, fmax_hz) / 1000.0:.9f}",
                "estimate_boundary": "projected compute-only estimate; not measured board latency",
            }
        )

    interface_cases = [
        ("ideal_register_batch", "conservative", 10, 20_000),
        ("ideal_register_batch", "nominal", 5, 20_000),
        ("ideal_register_batch", "aggressive", 2, 20_000),
        ("low_overhead_driver", "conservative", 100, 100),
        ("low_overhead_driver", "nominal", 50, 100),
        ("low_overhead_driver", "aggressive", 20, 100),
        ("dma_shared_memory_style", "conservative", 25, 1_000),
        ("dma_shared_memory_style", "nominal", 10, 1_000),
        ("dma_shared_memory_style", "aggressive", 5, 1_000),
    ]
    lanes = 16
    cycles = (macs + lanes - 1) // lanes + control_overhead_cycles
    compute_50 = compute_us(cycles, BOARD_CLOCK_HZ)
    compute_fmax = compute_us(cycles, fmax_hz)
    for interface, assumption_case, driver_overhead, bandwidth in interface_cases:
        xfer = transfer_us(transfer_bytes, bandwidth)
        rows.append(
            {
                "model_component": "optimized_interface_estimate",
                "evidence_type": "projected",
                "input_dim": input_dim,
                "output_dim": output_dim,
                "macs": macs,
                "lanes": lanes,
                "control_overhead_cycles": control_overhead_cycles,
                "cycles": cycles,
                "clock_hz_board": BOARD_CLOCK_HZ,
                "clock_hz_fmax": fmax_hz,
                "clock_source_fmax": fmax_source,
                "compute_time_us_50mhz": f"{compute_50:.9f}",
                "compute_time_us_fmax": f"{compute_fmax:.9f}",
                "weight_preloaded": True,
                "activation_transfer_bytes": activation_transfer_bytes,
                "result_transfer_bytes": result_transfer_bytes,
                "interface": interface,
                "assumption_case": assumption_case,
                "driver_overhead_us": driver_overhead,
                "assumed_transfer_bandwidth_MBps": bandwidth,
                "transfer_time_us": f"{xfer:.6f}",
                "optimized_interface_latency_us_50mhz": f"{compute_50 + driver_overhead + xfer:.9f}",
                "optimized_interface_latency_us_fmax": f"{compute_fmax + driver_overhead + xfer:.9f}",
                "optimized_interface_latency_ms": f"{(compute_fmax + driver_overhead + xfer) / 1000.0:.9f}",
                "estimate_boundary": estimate_boundary,
            }
        )

    out = Path(args.out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
