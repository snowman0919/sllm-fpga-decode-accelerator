#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import ScalarFormatter


DEFAULT_MODEL_SHAPE = {
    "layers": 26,
    "kv_heads": 1,
    "head_dim": 256,
    "bytes_per_element": 2,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze the PyTorch CPU baseline context sweep and generate "
            "paper-ready tables, figures, and a Markdown summary."
        )
    )
    parser.add_argument(
        "--latency-csv",
        type=Path,
        default=Path("assets/torch_decode_latency_by_context.csv"),
        help="Input CSV with per-context latency measurements.",
    )
    parser.add_argument(
        "--memory-csv",
        type=Path,
        default=Path("assets/torch_memory_by_context.csv"),
        help="Input CSV with per-context memory measurements.",
    )
    parser.add_argument(
        "--tables-dir",
        type=Path,
        default=Path("assets"),
        help="Output directory for paper-ready CSV tables.",
    )
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=Path("assets"),
        help="Output directory for paper-ready figures.",
    )
    parser.add_argument(
        "--summary-md",
        type=Path,
        default=Path("assets/torch.md"),
        help="Output Markdown summary path.",
    )
    parser.add_argument(
        "--config-json",
        type=Path,
        default=None,
        help="Optional Gemma config JSON. When present, model-shape values are read from it.",
    )
    parser.add_argument(
        "--layers",
        type=int,
        default=None,
        help="Override transformer layer count.",
    )
    parser.add_argument(
        "--kv-heads",
        type=int,
        default=None,
        help="Override KV head count.",
    )
    parser.add_argument(
        "--head-dim",
        type=int,
        default=None,
        help="Override per-head dimension.",
    )
    parser.add_argument(
        "--bytes-per-element",
        type=int,
        default=None,
        help="Override bytes per cache element.",
    )
    return parser.parse_args()


def load_model_shape(args: argparse.Namespace) -> dict[str, int]:
    model_shape = dict(DEFAULT_MODEL_SHAPE)

    if args.config_json is not None:
        config = json.loads(args.config_json.read_text(encoding="utf-8"))
        if "num_hidden_layers" in config:
            model_shape["layers"] = int(config["num_hidden_layers"])
        if "num_key_value_heads" in config:
            model_shape["kv_heads"] = int(config["num_key_value_heads"])
        if "head_dim" in config:
            model_shape["head_dim"] = int(config["head_dim"])
        elif "hidden_size" in config and "num_attention_heads" in config:
            model_shape["head_dim"] = int(config["hidden_size"]) // int(
                config["num_attention_heads"]
            )

    for field in ("layers", "kv_heads", "head_dim", "bytes_per_element"):
        override = getattr(args, field)
        if override is not None:
            model_shape[field] = int(override)

    for field, value in model_shape.items():
        if value <= 0:
            raise ValueError(f"{field} must be positive, got {value}.")

    return model_shape


def require_columns(frame: pd.DataFrame, required: list[str], label: str) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns in {label}: {missing}")


def load_preferred_csv(csv_path: Path, repo_root: Path) -> tuple[pd.DataFrame, Path]:
    frame = pd.read_csv(csv_path)
    if len(frame.index) >= 2:
        return frame, csv_path

    fallback_path = repo_root / "onnx_profile" / "results" / "tables" / csv_path.name
    if fallback_path.exists():
        fallback_frame = pd.read_csv(fallback_path)
        if len(fallback_frame.index) > len(frame.index):
            print(
                f"Input {csv_path} has only {len(frame.index)} row(s); "
                f"using fuller sweep from {fallback_path} with "
                f"{len(fallback_frame.index)} rows."
            )
            return fallback_frame, fallback_path

    raise ValueError(
        f"{csv_path} contains only {len(frame.index)} row(s). "
        "At least two context points are required for a sweep analysis."
    )


def validate_baseline(latency_frame: pd.DataFrame, memory_frame: pd.DataFrame) -> None:
    for frame, label in (
        (latency_frame, "latency CSV"),
        (memory_frame, "memory CSV"),
    ):
        if "device" not in frame.columns:
            raise ValueError(f"{label} must include a device column.")
        devices = sorted({str(value).strip().lower() for value in frame["device"].dropna()})
        if devices != ["cpu"]:
            raise ValueError(
                f"{label} must describe a CPU baseline, found devices={devices}."
            )
        if "baseline" in frame.columns:
            baseline_values = [
                str(value).strip() for value in frame["baseline"].dropna().unique()
            ]
            if not baseline_values or not all("pytorch" in value.lower() for value in baseline_values):
                raise ValueError(
                    f"{label} baseline column does not look like a PyTorch baseline: "
                    f"{baseline_values}"
                )


def build_analysis_frame(
    latency_frame: pd.DataFrame,
    memory_frame: pd.DataFrame,
    model_shape: dict[str, int],
) -> tuple[pd.DataFrame, dict[str, object]]:
    latency_required = [
        "baseline",
        "context_length",
        "decode_tokens",
        "runs",
        "warmup_runs",
        "device",
        "dtype",
        "prefill_ms_mean",
        "decode_ms_per_token_mean",
    ]
    memory_required = [
        "baseline",
        "context_length",
        "decode_tokens",
        "runs",
        "device",
        "dtype",
        "prefill_rss_delta_mib_mean",
        "peak_rss_mib_max",
    ]
    require_columns(latency_frame, latency_required, "latency CSV")
    require_columns(memory_frame, memory_required, "memory CSV")
    validate_baseline(latency_frame, memory_frame)

    latency_subset = latency_frame[latency_required].copy()
    memory_subset = memory_frame[memory_required].copy()

    merged = latency_subset.merge(
        memory_subset,
        on=["baseline", "context_length", "decode_tokens", "runs", "device", "dtype"],
        how="inner",
    )
    if merged.empty:
        raise ValueError("No matching rows were found after merging latency and memory CSVs.")

    merged = merged.sort_values("context_length").reset_index(drop=True)
    if 128 not in merged["context_length"].tolist():
        raise ValueError("A 128-token context row is required for relative latency columns.")

    kv_cache_mib = (
        2
        * model_shape["layers"]
        * model_shape["kv_heads"]
        * model_shape["head_dim"]
        * merged["context_length"]
        * model_shape["bytes_per_element"]
        / (1024 ** 2)
    )

    analysis_frame = pd.DataFrame(
        {
            "context_length": merged["context_length"].astype(int),
            "theoretical_kv_cache_mib": kv_cache_mib.astype(float),
            "observed_prefill_rss_delta_mib": merged[
                "prefill_rss_delta_mib_mean"
            ].astype(float),
            "observed_peak_rss_mib": merged["peak_rss_mib_max"].astype(float),
            "decode_ms_per_token_mean": merged["decode_ms_per_token_mean"].astype(float),
            "prefill_ms_mean": merged["prefill_ms_mean"].astype(float),
        }
    )
    analysis_frame["rss_delta_to_kv_cache_ratio"] = (
        analysis_frame["observed_prefill_rss_delta_mib"]
        / analysis_frame["theoretical_kv_cache_mib"]
    )

    base_row = analysis_frame.loc[analysis_frame["context_length"] == 128].iloc[0]
    analysis_frame["decode_latency_relative_to_128"] = (
        analysis_frame["decode_ms_per_token_mean"] / float(base_row["decode_ms_per_token_mean"])
    )
    analysis_frame["prefill_latency_relative_to_128"] = (
        analysis_frame["prefill_ms_mean"] / float(base_row["prefill_ms_mean"])
    )

    output_columns = [
        "context_length",
        "theoretical_kv_cache_mib",
        "observed_prefill_rss_delta_mib",
        "observed_peak_rss_mib",
        "rss_delta_to_kv_cache_ratio",
        "decode_ms_per_token_mean",
        "decode_latency_relative_to_128",
        "prefill_ms_mean",
        "prefill_latency_relative_to_128",
    ]
    analysis_frame = analysis_frame[output_columns]

    metadata = {
        "baseline_label": str(merged["baseline"].iloc[0]),
        "device": str(merged["device"].iloc[0]),
        "dtype": str(merged["dtype"].iloc[0]),
        "decode_tokens": int(merged["decode_tokens"].iloc[0]),
        "runs": int(merged["runs"].iloc[0]),
        "warmup_runs": int(merged["warmup_runs"].iloc[0]),
        "context_lengths": analysis_frame["context_length"].tolist(),
    }
    return analysis_frame, metadata


def build_key_findings(analysis_frame: pd.DataFrame) -> pd.DataFrame:
    min_row = analysis_frame.iloc[0]
    max_row = analysis_frame.iloc[-1]
    findings = pd.DataFrame(
        [
            {
                "min_context": int(min_row["context_length"]),
                "max_context": int(max_row["context_length"]),
                "decode_latency_at_min_context": float(min_row["decode_ms_per_token_mean"]),
                "decode_latency_at_max_context": float(max_row["decode_ms_per_token_mean"]),
                "decode_latency_growth_ratio": float(
                    max_row["decode_ms_per_token_mean"]
                    / min_row["decode_ms_per_token_mean"]
                ),
                "prefill_latency_growth_ratio": float(
                    max_row["prefill_ms_mean"] / min_row["prefill_ms_mean"]
                ),
                "rss_delta_growth_ratio": float(
                    max_row["observed_prefill_rss_delta_mib"]
                    / min_row["observed_prefill_rss_delta_mib"]
                ),
                "theoretical_kv_cache_growth_ratio": float(
                    max_row["theoretical_kv_cache_mib"]
                    / min_row["theoretical_kv_cache_mib"]
                ),
            }
        ]
    )
    return findings


def format_log2_x_axis(ax: plt.Axes, context_lengths: list[int]) -> None:
    ax.set_xscale("log", base=2)
    ax.set_xticks(context_lengths)
    ax.get_xaxis().set_major_formatter(ScalarFormatter())
    if len(context_lengths) > 1:
        ax.set_xlim(min(context_lengths), max(context_lengths))
    ax.grid(True, which="both", linestyle=":", linewidth=0.8, alpha=0.6)


def save_decode_latency_figure(
    analysis_frame: pd.DataFrame, figure_path: Path, baseline_title: str
) -> None:
    context_lengths = analysis_frame["context_length"].tolist()
    plt.figure(figsize=(8.2, 4.8))
    plt.plot(
        context_lengths,
        analysis_frame["decode_ms_per_token_mean"],
        marker="o",
        linewidth=2.2,
        color="#1f77b4",
    )
    ax = plt.gca()
    format_log2_x_axis(ax, context_lengths)
    plt.xlabel("Context length (tokens, log2 scale)")
    plt.ylabel("Decode latency (ms/token)")
    plt.title(f"{baseline_title}: Decode Latency by Context")
    plt.tight_layout()
    plt.savefig(figure_path, dpi=220)
    plt.close()


def save_memory_comparison_figure(
    analysis_frame: pd.DataFrame, figure_path: Path, baseline_title: str
) -> None:
    context_lengths = analysis_frame["context_length"].tolist()
    plt.figure(figsize=(8.4, 5.0))
    plt.plot(
        context_lengths,
        analysis_frame["theoretical_kv_cache_mib"],
        marker="o",
        linewidth=2.2,
        color="#2ca02c",
        label="Theoretical KV-cache",
    )
    plt.plot(
        context_lengths,
        analysis_frame["observed_prefill_rss_delta_mib"],
        marker="s",
        linewidth=2.2,
        color="#d62728",
        label="Observed prefill RSS delta",
    )
    plt.plot(
        context_lengths,
        analysis_frame["observed_peak_rss_mib"],
        marker="^",
        linewidth=1.8,
        linestyle="--",
        color="#7f7f7f",
        label="Observed peak RSS",
    )
    ax = plt.gca()
    format_log2_x_axis(ax, context_lengths)
    plt.xlabel("Context length (tokens, log2 scale)")
    plt.ylabel("Memory footprint (MiB)")
    plt.title(f"{baseline_title}: Theoretical KV-cache vs RSS")
    plt.legend()
    plt.tight_layout()
    plt.savefig(figure_path, dpi=220)
    plt.close()


def save_summary_figure(
    analysis_frame: pd.DataFrame, figure_path: Path, baseline_title: str
) -> None:
    context_lengths = analysis_frame["context_length"].tolist()
    fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(8.6, 8.0), sharex=True)

    ax_top.plot(
        context_lengths,
        analysis_frame["decode_latency_relative_to_128"],
        marker="o",
        linewidth=2.2,
        color="#1f77b4",
        label="Decode latency / 128-token decode latency",
    )
    ax_top.plot(
        context_lengths,
        analysis_frame["prefill_latency_relative_to_128"],
        marker="s",
        linewidth=2.2,
        color="#ff7f0e",
        label="Prefill latency / 128-token prefill latency",
    )
    format_log2_x_axis(ax_top, context_lengths)
    ax_top.set_ylabel("Latency growth vs 128-token context")
    ax_top.set_title(f"{baseline_title}: Latency and Memory Summary")
    ax_top.legend(loc="upper left")

    ax_bottom.plot(
        context_lengths,
        analysis_frame["theoretical_kv_cache_mib"],
        marker="o",
        linewidth=2.2,
        color="#2ca02c",
        label="Theoretical KV-cache",
    )
    ax_bottom.plot(
        context_lengths,
        analysis_frame["observed_prefill_rss_delta_mib"],
        marker="s",
        linewidth=2.2,
        color="#d62728",
        label="Observed prefill RSS delta",
    )
    ax_bottom.plot(
        context_lengths,
        analysis_frame["observed_peak_rss_mib"],
        marker="^",
        linewidth=1.8,
        linestyle="--",
        color="#7f7f7f",
        label="Observed peak RSS",
    )
    format_log2_x_axis(ax_bottom, context_lengths)
    ax_bottom.set_xlabel("Context length (tokens, log2 scale)")
    ax_bottom.set_ylabel("Memory footprint (MiB)")
    ax_bottom.legend(loc="upper left")

    fig.tight_layout()
    fig.savefig(figure_path, dpi=220)
    plt.close(fig)


def write_summary(
    summary_path: Path,
    analysis_frame: pd.DataFrame,
    findings_frame: pd.DataFrame,
    metadata: dict[str, object],
    model_shape: dict[str, int],
    latency_source_path: Path,
    memory_source_path: Path,
) -> None:
    min_row = analysis_frame.iloc[0]
    max_row = analysis_frame.iloc[-1]
    findings = findings_frame.iloc[0]
    ratio_min = analysis_frame["rss_delta_to_kv_cache_ratio"].min()
    ratio_max = analysis_frame["rss_delta_to_kv_cache_ratio"].max()

    summary = f"""# PyTorch CPU Baseline Context Sweep Analysis

## Experimental Conditions

- Baseline under analysis: PyTorch CPU baseline. This summary does not describe ONNX Runtime, CUDA/GPU execution, or end-to-end FPGA decode acceleration.
- Input latency table used for analysis: `{latency_source_path}`
- Input memory table used for analysis: `{memory_source_path}`
- Device and dtype recorded in the sweep: `{metadata["device"]}` / `{metadata["dtype"]}`
- Context lengths analyzed: {", ".join(str(value) for value in metadata["context_lengths"])}
- Decode tokens per run: {metadata["decode_tokens"]}
- Measured runs per context: {metadata["runs"]} with {metadata["warmup_runs"]} warmup run(s)
- Theoretical KV-cache parameters: layers={model_shape["layers"]}, kv_heads={model_shape["kv_heads"]}, head_dim={model_shape["head_dim"]}, bytes_per_element={model_shape["bytes_per_element"]}

## Key Numbers

- Decode latency increased from {min_row["decode_ms_per_token_mean"]:.2f} ms/token at context {int(min_row["context_length"])} to {max_row["decode_ms_per_token_mean"]:.2f} ms/token at context {int(max_row["context_length"])} ({findings["decode_latency_growth_ratio"]:.2f}x).
- Prefill latency increased by {findings["prefill_latency_growth_ratio"]:.2f}x across the same context range, from {min_row["prefill_ms_mean"]:.2f} ms to {max_row["prefill_ms_mean"]:.2f} ms.
- Theoretical KV-cache size increased from {min_row["theoretical_kv_cache_mib"]:.2f} MiB to {max_row["theoretical_kv_cache_mib"]:.2f} MiB ({findings["theoretical_kv_cache_growth_ratio"]:.2f}x).
- Observed prefill RSS delta increased from {min_row["observed_prefill_rss_delta_mib"]:.2f} MiB to {max_row["observed_prefill_rss_delta_mib"]:.2f} MiB ({findings["rss_delta_growth_ratio"]:.2f}x).
- The observed peak RSS reached {max_row["observed_peak_rss_mib"]:.2f} MiB at the maximum analyzed context length.
- The ratio between observed prefill RSS delta and theoretical KV-cache size stayed within {ratio_min:.2f}x to {ratio_max:.2f}x over the sweep.

## Interpretable Scope

Within this PyTorch CPU baseline, decode latency grows gradually with context length while prefill latency and process RSS growth rise much more sharply. The tables and figures support a host-side comparison between theoretical KV-cache scaling and observed memory movement at the process level, but they should be interpreted only as a baseline characterization for this software stack and this measurement setup.

## RSS Interpretation Limits

The observed RSS delta values in these outputs are process-level resident-set-size changes measured around prefill. They are not a direct measurement of KV-cache bytes, and they should not be treated as proof that all of the RSS change is caused only by KV-cache allocation. Other allocator effects, framework buffers, page residency changes, and host-side bookkeeping can contribute to the observed delta.

## Connection to FPGA Primitive Validation

These PyTorch CPU baseline trends help motivate why long-context decode workloads become increasingly sensitive to memory footprint and latency, but they do not demonstrate FPGA acceleration of real Gemma 3 1B decode. In this repository, the FPGA evidence remains at the primitive-validation level, such as operator-scale correctness checks plus resource, timing, and latency studies for the implemented building blocks.
"""
    summary_path.write_text(summary, encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]

    if not args.latency_csv.exists():
        raise FileNotFoundError(f"Missing latency CSV: {args.latency_csv}")
    if not args.memory_csv.exists():
        raise FileNotFoundError(f"Missing memory CSV: {args.memory_csv}")
    if args.config_json is not None and not args.config_json.exists():
        raise FileNotFoundError(f"Missing config JSON: {args.config_json}")

    args.tables_dir.mkdir(parents=True, exist_ok=True)
    args.figures_dir.mkdir(parents=True, exist_ok=True)
    args.summary_md.parent.mkdir(parents=True, exist_ok=True)

    model_shape = load_model_shape(args)
    latency_frame, latency_source_path = load_preferred_csv(args.latency_csv, repo_root)
    memory_frame, memory_source_path = load_preferred_csv(args.memory_csv, repo_root)
    analysis_frame, metadata = build_analysis_frame(
        latency_frame=latency_frame,
        memory_frame=memory_frame,
        model_shape=model_shape,
    )
    findings_frame = build_key_findings(analysis_frame)

    kv_vs_rss_path = args.tables_dir / "torch_kv_cache_vs_rss.csv"
    key_findings_path = args.tables_dir / "torch_sweep_key_findings.csv"
    decode_latency_figure_path = (
        args.figures_dir / "torch_decode_latency_by_context_logx.png"
    )
    kv_vs_rss_figure_path = args.figures_dir / "torch_kv_cache_vs_rss_logx.png"
    summary_figure_path = args.figures_dir / "torch_latency_and_memory_summary.png"

    analysis_frame.to_csv(kv_vs_rss_path, index=False, float_format="%.6f")
    findings_frame.to_csv(key_findings_path, index=False, float_format="%.6f")

    baseline_title = "PyTorch CPU baseline"
    save_decode_latency_figure(
        analysis_frame=analysis_frame,
        figure_path=decode_latency_figure_path,
        baseline_title=baseline_title,
    )
    save_memory_comparison_figure(
        analysis_frame=analysis_frame,
        figure_path=kv_vs_rss_figure_path,
        baseline_title=baseline_title,
    )
    save_summary_figure(
        analysis_frame=analysis_frame,
        figure_path=summary_figure_path,
        baseline_title=baseline_title,
    )
    write_summary(
        summary_path=args.summary_md,
        analysis_frame=analysis_frame,
        findings_frame=findings_frame,
        metadata=metadata,
        model_shape=model_shape,
        latency_source_path=latency_source_path,
        memory_source_path=memory_source_path,
    )

    print(f"Saved table: {kv_vs_rss_path}")
    print(f"Saved table: {key_findings_path}")
    print(f"Saved figure: {decode_latency_figure_path}")
    print(f"Saved figure: {kv_vs_rss_figure_path}")
    print(f"Saved figure: {summary_figure_path}")
    print(f"Saved summary: {args.summary_md}")
    print()
    print(findings_frame.to_string(index=False))


if __name__ == "__main__":
    main()
