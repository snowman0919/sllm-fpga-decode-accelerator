#!/usr/bin/env python3
"""Build final paper analysis tables with explicit evidence boundaries."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = Path("/home/monad/develop/ai_accel/gemma3-1B/config.json")
DEFAULT_OUT_DIR = PROJECT_ROOT / "paper_assets/tables"
DEFAULT_QUARTUS_SUMMARY = PROJECT_ROOT / "assets/c11.csv"
DEFAULT_FPGA_CYCLE_SUMMARY = PROJECT_ROOT / "assets/c13.csv"
DEFAULT_Y700_DEVICE_INFO = PROJECT_ROOT / "logs/y700_onnx_runtime/device_info.json"
DEFAULT_Y700_BENCHMARK_SUMMARY = PROJECT_ROOT / "logs/y700_onnx_runtime/benchmark_summary.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--quartus-summary", default=str(DEFAULT_QUARTUS_SUMMARY))
    parser.add_argument("--fpga-cycle-summary", default=str(DEFAULT_FPGA_CYCLE_SUMMARY))
    parser.add_argument("--y700-device-info", default=str(DEFAULT_Y700_DEVICE_INFO))
    parser.add_argument("--y700-benchmark-summary", default=str(DEFAULT_Y700_BENCHMARK_SUMMARY))
    return parser.parse_args()


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_first(path: Path) -> dict[str, str]:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}


def read_summary_first(path: Path) -> dict[str, object]:
    if path.suffix.lower() == ".json":
        return read_json(path)
    return read_csv_first(path)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def as_int(value: object, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def as_float(value: object, fallback: float = math.nan) -> float:
    try:
        return float(str(value).replace("%", "").strip())
    except (TypeError, ValueError):
        return fallback


def build_projection_roofline(config: dict[str, object]) -> list[dict[str, object]]:
    hidden = as_int(config.get("hidden_size"), 1152)
    intermediate = as_int(config.get("intermediate_size"), 6912)
    vocab = as_int(config.get("vocab_size"), 262144)
    head_dim = as_int(config.get("head_dim"), 256)
    heads = as_int(config.get("num_attention_heads"), 4)
    attn_out = head_dim * heads

    shapes = [
        ("mlp_gate_or_up_projection", hidden, intermediate, "Gemma MLP gate/up projection tile target"),
        ("mlp_down_projection", intermediate, hidden, "Gemma MLP down projection tile target"),
        ("lm_head_full_projection", hidden, vocab, "Full vocabulary projection; normally requires output tiling/top-k strategy"),
        ("lm_head_4096_vocab_tile", hidden, 4096, "Representative vocabulary output tile"),
        ("attention_qkv_projection", hidden, attn_out, "Attention q/k/v projection aggregate output width"),
        ("attention_output_projection", attn_out, hidden, "Attention output projection"),
    ]

    rows: list[dict[str, object]] = []
    memory_bandwidth_cases = [
        ("debug_jtag_not_applicable", None),
        ("usb2_like_40_MBps", 40.0),
        ("usb3_stream_320_MBps", 320.0),
        ("axi_dma_1000_MBps", 1000.0),
    ]
    lane_cases = [1, 16, 64]
    clock_mhz = 50.0
    for component, input_dim, output_dim, note in shapes:
        macs = input_dim * output_dim
        weight_bytes = macs
        activation_bytes = input_dim
        output_bytes = output_dim * 4
        total_stream_bytes = weight_bytes + activation_bytes + output_bytes
        ai_macs_per_byte = macs / total_stream_bytes if total_stream_bytes else math.nan
        for lanes in lane_cases:
            compute_us = macs / (lanes * clock_mhz)
            for bandwidth_label, bandwidth_MBps in memory_bandwidth_cases:
                if bandwidth_MBps is None:
                    stream_us = ""
                    likely_bound = "not_applicable"
                else:
                    stream_us_float = total_stream_bytes / bandwidth_MBps
                    stream_us = f"{stream_us_float:.3f}"
                    likely_bound = "bandwidth_bound" if stream_us_float > compute_us else "compute_bound"
                rows.append(
                    {
                        "component": component,
                        "evidence_type": "projected",
                        "input_dim": input_dim,
                        "output_dim": output_dim,
                        "macs_per_token": macs,
                        "weight_bytes_int8": weight_bytes,
                        "activation_bytes_int8": activation_bytes,
                        "output_bytes_int32": output_bytes,
                        "total_stream_bytes": total_stream_bytes,
                        "arithmetic_intensity_macs_per_byte": f"{ai_macs_per_byte:.6f}",
                        "assumed_lanes": lanes,
                        "assumed_clock_mhz": clock_mhz,
                        "compute_time_us_est": f"{compute_us:.3f}",
                        "bandwidth_case": bandwidth_label,
                        "assumed_bandwidth_MBps": "" if bandwidth_MBps is None else bandwidth_MBps,
                        "stream_time_us_est": stream_us,
                        "likely_bound": likely_bound,
                        "note": note,
                        "claim_boundary": "Projection-scale model only; not measured FPGA or ONNX Runtime latency.",
                    }
                )
    return rows


def build_interface_model() -> list[dict[str, object]]:
    return [
        {
            "interface": "USB-Blaster JTAG/System Console",
            "evidence_type": "measured_invocation_overhead",
            "usable_for": "correctness/debug register access",
            "performance_claim_allowed": "no",
            "typical_boundary": "Host tool invocation dominates; not a low-latency offload path.",
        },
        {
            "interface": "UART/USB serial",
            "evidence_type": "projected",
            "usable_for": "bring-up/correctness for small payloads",
            "performance_claim_allowed": "no",
            "typical_boundary": "Too little bandwidth for projection-scale weight streaming.",
        },
        {
            "interface": "USB3/FT600-class streaming",
            "evidence_type": "projected",
            "usable_for": "external FPGA streaming prototype",
            "performance_claim_allowed": "model_only_until_measured",
            "typical_boundary": "Could test activation/output streaming, but weight streaming remains a bandwidth driver.",
        },
        {
            "interface": "Ethernet/UDP streaming",
            "evidence_type": "projected",
            "usable_for": "external board prototype",
            "performance_claim_allowed": "model_only_until_measured",
            "typical_boundary": "Latency and packetization overhead must be measured before acceleration claims.",
        },
        {
            "interface": "AXI DMA/shared memory on KR260/Zynq-class SoC",
            "evidence_type": "future_path",
            "usable_for": "practical low-overhead accelerator integration",
            "performance_claim_allowed": "future_work",
            "typical_boundary": "Requires KR260 or similar platform; current KR260 is unavailable due to RMA.",
        },
        {
            "interface": "Snapdragon QNN/NNAPI EP",
            "evidence_type": "attempt_required",
            "usable_for": "on-device accelerator baseline",
            "performance_claim_allowed": "only_if_y700_log_succeeds",
            "typical_boundary": "Must be reported as attempted but not used or integration blocked if it fails on Y700.",
        },
    ]


def build_tiled_config_sweep() -> list[dict[str, object]]:
    return [
        {
            "config_name": "smoke_board_anchor",
            "evidence_type": "board_measured",
            "input_dim": 16,
            "output_dim": 4,
            "tile_dim_or_lanes": 1,
            "macs": 64,
            "rtl_simulation": "pass",
            "quartus_synthesis": "pass_existing_clean_rebuild",
            "board_run": "pass_existing_20_of_20",
            "current_role": "DE10-Lite correctness and cycle-counter anchor",
            "claim_boundary": "Measured only for fixed 16x4 sequential core.",
        },
        {
            "config_name": "small_tiled_sim",
            "evidence_type": "simulation",
            "input_dim": 64,
            "output_dim": 16,
            "tile_dim_or_lanes": 4,
            "macs": 1024,
            "rtl_simulation": "pass",
            "quartus_synthesis": "not_run",
            "board_run": "not_run",
            "current_role": "Input-lane parameterization check",
            "claim_boundary": "Simulation only; not a measured board or timing result.",
        },
        {
            "config_name": "medium_candidate",
            "evidence_type": "planned_or_projected",
            "input_dim": 128,
            "output_dim": 32,
            "tile_dim_or_lanes": 8,
            "macs": 4096,
            "rtl_simulation": "not_run",
            "quartus_synthesis": "not_run",
            "board_run": "not_run",
            "current_role": "Candidate for later synthesis sweep",
            "claim_boundary": "Design-space placeholder only.",
        },
        {
            "config_name": "projection_tile_candidate",
            "evidence_type": "planned_or_projected",
            "input_dim": 256,
            "output_dim": 64,
            "tile_dim_or_lanes": 16,
            "macs": 16384,
            "rtl_simulation": "not_run",
            "quartus_synthesis": "not_run",
            "board_run": "not_run",
            "current_role": "Representative projection tile candidate",
            "claim_boundary": "Design-space placeholder only; not measured.",
        },
    ]


def build_board_validation(quartus: dict[str, str], cycle: dict[str, str]) -> list[dict[str, object]]:
    input_dim = cycle.get("input_dim", "16")
    output_dim = cycle.get("output_dim", "4")
    macs = cycle.get("macs", "")
    if macs == "":
        try:
            macs = int(input_dim) * int(output_dim)
        except (TypeError, ValueError):
            macs = "64"
    return [
        {
            "artifact": "DE10-Lite INT8 MatVec core",
            "evidence_type": "board_measured",
            "input_dim": input_dim,
            "output_dim": output_dim,
            "macs": macs,
            "pass_count": cycle.get("pass_count", ""),
            "fail_count": cycle.get("fail_count", ""),
            "correctness_pass": cycle.get("correctness_pass", ""),
            "compute_cycles": cycle.get("compute_cycles_mean", ""),
            "compute_time_us_50mhz": cycle.get("compute_time_us_50mhz_mean", ""),
            "logic_elements_used": quartus.get("logic_elements_used", ""),
            "logic_elements_available": quartus.get("logic_elements_available", ""),
            "dsp_9bit_elements_used": quartus.get("dsp_9bit_elements_used", ""),
            "dsp_9bit_elements_available": quartus.get("dsp_9bit_elements_available", ""),
            "memory_bits_used": quartus.get("memory_bits_used", ""),
            "memory_bits_available": quartus.get("memory_bits_available", ""),
            "fmax_mhz": quartus.get("fmax_mhz", ""),
            "timing_met": quartus.get("timing_met", ""),
            "claim_boundary": "Core correctness and internal cycle anchor only; not whole-model or whole-offload acceleration evidence.",
        }
    ]


def build_environment_rows(y700: dict[str, object]) -> list[dict[str, object]]:
    device = y700.get("device") if isinstance(y700.get("device"), dict) else {}
    return [
        {
            "environment": "Lenovo Y700 Android",
            "evidence_type": "environment_check",
            "status": y700.get("status", "missing_log"),
            "model": device.get("ro.product.model", "") if isinstance(device, dict) else "",
            "board_platform": device.get("ro.board.platform", "") if isinstance(device, dict) else "",
            "hardware": device.get("ro.hardware", "") if isinstance(device, dict) else "",
            "android_release": device.get("ro.build.version.release", "") if isinstance(device, dict) else "",
            "claim_boundary": "Device info only. No ONNX Runtime latency is implied.",
        },
        {
            "environment": "DE10-Lite/Pocket4 board path",
            "evidence_type": "board_validation_environment",
            "status": "existing_board_manifest_available",
            "model": "DE10-Lite MAX 10",
            "board_platform": "10M50DAF484C7G",
            "hardware": "USB-Blaster JTAG",
            "android_release": "",
            "claim_boundary": "FPGA core validation environment, not connected to Lenovo Y700 as a low-latency offload path.",
        },
    ]


def inspect_onnx_artifacts() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    try:
        import onnx
    except Exception as exc:
        return [
            {
                "model_name": "onnx_inspection_unavailable",
                "path": "",
                "status": "skipped",
                "reason": f"onnx import failed: {exc}",
                "claim_boundary": "Manifest generation did not inspect ONNX graph contents.",
            }
        ]

    for path in sorted((PROJECT_ROOT / "onnx_micrographs").glob("*.onnx")):
        try:
            model = onnx.load(path)
            graph = model.graph
            inputs = []
            outputs = []
            node_types: dict[str, int] = {}
            for node in graph.node:
                node_types[node.op_type] = node_types.get(node.op_type, 0) + 1
            for value in graph.input:
                tensor = value.type.tensor_type
                shape = [
                    dim.dim_value if dim.dim_value else dim.dim_param or "?"
                    for dim in tensor.shape.dim
                ]
                inputs.append(f"{value.name}:{onnx.TensorProto.DataType.Name(tensor.elem_type)}{shape}")
            for value in graph.output:
                tensor = value.type.tensor_type
                shape = [
                    dim.dim_value if dim.dim_value else dim.dim_param or "?"
                    for dim in tensor.shape.dim
                ]
                outputs.append(f"{value.name}:{onnx.TensorProto.DataType.Name(tensor.elem_type)}{shape}")
            rows.append(
                {
                    "model_name": path.name,
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "status": "available",
                    "node_count": len(graph.node),
                    "op_types": ";".join(f"{key}:{value}" for key, value in sorted(node_types.items())),
                    "inputs": " | ".join(inputs),
                    "outputs": " | ".join(outputs),
                    "target_runtime": "ONNX Runtime micrograph",
                    "notes": "Synthetic micrograph; filename may indicate intended representative role, but graph shape is authoritative.",
                    "claim_boundary": "Micrograph artifact only; not a Gemma full model.",
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "model_name": path.name,
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "status": "inspect_failed",
                    "reason": str(exc),
                    "claim_boundary": "Manifest row does not support a model execution claim.",
                }
            )
    return rows


def build_y700_baseline_rows(benchmark: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    status = str(benchmark.get("status", "missing_log"))
    results = benchmark.get("results")
    if isinstance(results, list) and results:
        for result in results:
            if not isinstance(result, dict):
                continue
            rows.append(
                {
                    "model_name": result.get("model_name", ""),
                    "runtime": "ONNX Runtime Android APK",
                    "execution_provider": result.get("execution_provider", ""),
                    "kind": result.get("kind", ""),
                    "status": result.get("status", ""),
                    "input_dim": result.get("input_dim", ""),
                    "output_dim": result.get("output_dim", ""),
                    "warmup": result.get("warmup", benchmark.get("warmup", "")),
                    "runs": result.get("runs", benchmark.get("runs", "")),
                    "mean_ms": result.get("mean_ms", ""),
                    "p50_ms": result.get("p50_ms", ""),
                    "p95_ms": result.get("p95_ms", ""),
                    "min_ms": result.get("min_ms", ""),
                    "max_ms": result.get("max_ms", ""),
                    "available_providers": result.get("available_providers", ""),
                    "error": result.get("error", ""),
                    "claim_boundary": "Android ONNX Runtime APK micrograph session.run latency only; not whole-model inference.",
                }
            )
        return rows

    run_results = benchmark.get("run_results")
    if isinstance(run_results, list) and run_results:
        for result in run_results:
            if not isinstance(result, dict):
                continue
            rows.append(
                {
                    "model_name": result.get("kind", ""),
                    "runtime": "ONNX Runtime",
                    "execution_provider": result.get("provider", ""),
                    "status": "attempted",
                    "warmup": benchmark.get("warmup", ""),
                    "runs": benchmark.get("runs", ""),
                    "summary_stdout": result.get("stdout", ""),
                    "summary_stderr": result.get("stderr", ""),
                    "claim_boundary": "Raw Android micrograph attempt summary; use pulled JSON/CSV for measured latency only if status completed.",
                }
            )
    else:
        rows.append(
            {
                "model_name": "not_run",
                "runtime": "ONNX Runtime",
                "execution_provider": "",
                "status": status,
                "warmup": benchmark.get("warmup", ""),
                "runs": benchmark.get("runs", ""),
                "summary_stdout": "",
                "summary_stderr": benchmark.get("reason", ""),
                "claim_boundary": "No Y700 ONNX Runtime latency is available in this row.",
            }
        )
    return rows


def build_y700_micrograph_summary(benchmark: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for row in build_y700_baseline_rows(benchmark):
        if row.get("status") != "completed":
            continue
        model_name = str(row.get("model_name", ""))
        if model_name.startswith("matvec_"):
            role = "smoke_16x4"
        elif "attention_output" in model_name:
            role = "attention_output_projection"
        elif "lm_head" in model_name:
            role = "lm_head_tile"
        elif "mlp_projection" in model_name:
            role = "mlp_projection"
        else:
            role = "unknown"
        rows.append(
            {
                "role": role,
                "model_name": model_name,
                "execution_provider": row.get("execution_provider", ""),
                "kind": row.get("kind", ""),
                "input_dim": row.get("input_dim", ""),
                "output_dim": row.get("output_dim", ""),
                "mean_ms": row.get("mean_ms", ""),
                "p50_ms": row.get("p50_ms", ""),
                "p95_ms": row.get("p95_ms", ""),
                "claim_boundary": "Representative ONNX Runtime Android micrograph latency.",
            }
        )
    return rows


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    config = read_json(Path(args.model_config))
    quartus = read_csv_first(Path(args.quartus_summary))
    cycle = read_summary_first(Path(args.fpga_cycle_summary))
    y700 = read_json(Path(args.y700_device_info))
    y700_benchmark = read_json(Path(args.y700_benchmark_summary))

    write_csv(out_dir / "projection_tile_roofline.csv", build_projection_roofline(config))
    write_csv(out_dir / "offload_interface_model.csv", build_interface_model())
    write_csv(out_dir / "fpga_tiled_config_sweep.csv", build_tiled_config_sweep())
    write_csv(out_dir / "fpga_board_validation_summary.csv", build_board_validation(quartus, cycle))
    write_csv(out_dir / "experiment_environment.csv", build_environment_rows(y700))
    write_csv(out_dir / "model_artifact_manifest.csv", inspect_onnx_artifacts())
    write_csv(out_dir / "y700_onnx_runtime_baseline.csv", build_y700_baseline_rows(y700_benchmark))
    write_csv(out_dir / "y700_operator_or_micrograph_summary.csv", build_y700_micrograph_summary(y700_benchmark))
    print(f"wrote final analysis tables under {out_dir}")


if __name__ == "__main__":
    main()
