#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from kv_cache_size import kv_cache_bytes
from run_profile import model_exists, profile_model


DEFAULT_PROMPT_LENS = [128, 512, 1024, 2048, 4096]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep prompt lengths for ONNX Runtime profiling, compare theoretical KV-cache "
            "size against measured process RSS growth, and connect the trend to FPGA validation artifacts."
        )
    )
    parser.add_argument("--model", type=Path, required=True, help="Path to an exported ONNX model.")
    parser.add_argument("--provider", default="CPUExecutionProvider", help="ONNX Runtime execution provider.")
    parser.add_argument(
        "--prompt-lens",
        type=int,
        nargs="+",
        default=DEFAULT_PROMPT_LENS,
        help="Prompt lengths to sweep.",
    )
    parser.add_argument("--decode-tokens", type=int, default=8, help="Decode iterations per prompt length.")
    parser.add_argument("--profile", action="store_true", help="Enable ONNX Runtime profiling JSON for each sweep point.")
    parser.add_argument("--layers", type=int, default=18, help="Transformer layer count used for theoretical KV-cache sizing.")
    parser.add_argument("--kv-heads", type=int, default=1, help="KV head count used for theoretical KV-cache sizing.")
    parser.add_argument("--head-dim", type=int, default=256, help="Head dimension used for theoretical KV-cache sizing.")
    parser.add_argument("--bytes-per-element", type=int, default=2, help="Bytes per KV-cache element, for example 2 for FP16.")
    parser.add_argument("--out-dir", type=Path, required=True, help="Output directory for sweep artifacts.")
    parser.add_argument(
        "--paper-tables-dir",
        type=Path,
        default=Path("paper_assets/tables"),
        help="Optional directory where paper-facing CSV copies are written.",
    )
    parser.add_argument(
        "--fpga-summary",
        type=Path,
        default=Path("fpga_test/captured/fpga_validation_summary.md"),
        help="FPGA validation summary markdown to reference in the host/FPGA bridge note.",
    )
    return parser.parse_args()


def mib_from_bytes(value: int | None) -> float | None:
    if value is None:
        return None
    return value / (1024 ** 2)


def delta_bytes(after: int | None, before: int | None) -> int | None:
    if after is None or before is None:
        return None
    return after - before


def safe_ratio(numerator: int | None, denominator: int | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def read_fpga_timing_summary(paper_tables_dir: Path) -> dict[str, str]:
    timing_path = paper_tables_dir / "fpga_timing_summary.csv"
    if not timing_path.exists():
        return {}

    with timing_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("analysis") == "Fmax" and row.get("corner") == "Slow 1200mV 85C":
                return row
    return {}


def read_fpga_resource_summary(paper_tables_dir: Path) -> dict[str, str]:
    resource_path = paper_tables_dir / "fpga_resource_summary.csv"
    if not resource_path.exists():
        return {}

    summary: dict[str, str] = {}
    with resource_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("entity") == "int8_qk_dot_product_core":
                metric = row.get("metric", "")
                summary[metric] = row.get("used", "")
    return summary


def to_ms(seconds: float | None) -> float | None:
    if seconds is None:
        return None
    return seconds * 1000.0


def add_ratio_columns(frame: pd.DataFrame) -> pd.DataFrame:
    for column in [
        "prefill_rss_delta_bytes",
        "decode_rss_delta_bytes",
        "total_rss_delta_bytes",
        "theoretical_kv_prompt_bytes",
        "theoretical_kv_decode_growth_bytes",
        "theoretical_kv_final_bytes",
    ]:
        if column in frame:
            mib_column = column.replace("_bytes", "_mib")
            frame[mib_column] = frame[column].apply(lambda value: value / (1024 ** 2) if pd.notna(value) else value)
    return frame


def render_markdown_summary(
    latency_frame: pd.DataFrame,
    kv_frame: pd.DataFrame,
    fpga_summary_path: Path,
    fpga_timing: dict[str, str],
    fpga_resources: dict[str, str],
    output_dir: Path,
) -> str:
    decode_mode = latency_frame["decode_mode"].iloc[0] if not latency_frame.empty else "unknown"
    note_lines = [
        "# Decode Profiling to FPGA Bridge Summary",
        "",
        "## Scope",
        "",
        "- Host-side artifact: ONNX Runtime measurements across prompt lengths",
        "- FPGA-side artifact: DE10-Lite INT8 QK dot-product validation summary",
        "- This summary does not claim full Gemma 3 1B execution on FPGA.",
        "- This summary does not claim FPGA speedup over ONNX Runtime.",
        f"- Decode execution mode discovered by the host script: `{decode_mode}`",
        "",
        "## Host-Side Outputs",
        "",
        f"- Latency table: `{(output_dir / 'tables' / 'decode_latency_by_context.csv').resolve()}`",
        f"- KV comparison table: `{(output_dir / 'tables' / 'kv_memory_comparison.csv').resolve()}`",
        f"- Decode latency plot: `{(output_dir / 'figures' / 'decode_latency_by_context.png').resolve()}`",
        f"- KV/RSS comparison plot: `{(output_dir / 'figures' / 'kv_theoretical_vs_actual_rss.png').resolve()}`",
        "",
        "## Interpretation",
        "",
        "- Prefill and decode are measured separately so the paper can discuss token-by-token latency growth without mixing it into session creation time.",
        "- The context-length sweep is useful for showing whether decode cost and process RSS tend to rise with longer active sequences.",
        "- Theoretical KV-cache size is linear in sequence length; measured RSS deltas are only a coarse upper bound because ONNX Runtime allocators, graph state, and temporary buffers are included.",
    ]

    if fpga_summary_path.exists():
        note_lines.extend(
            [
                "",
                "## FPGA Connection",
                "",
                f"- FPGA validation summary: `{fpga_summary_path.resolve()}`",
                "- The host-side decode trend motivates isolating compact decode-stage primitives for RTL validation.",
                "- The currently validated primitive remains the INT8 QK dot-product core, not the full attention stack and not the full language model.",
            ]
        )
        if fpga_timing:
            note_lines.append(
                f"- Quartus slow-corner Fmax recorded for the validation design: `{fpga_timing.get('fmax_mhz', '')} MHz`."
            )
        if fpga_resources:
            note_lines.append(
                "- Core resource snapshot from Quartus map report: "
                f"`{fpga_resources.get('Combinational ALUTs', '?')}` ALUTs, "
                f"`{fpga_resources.get('Dedicated Logic Registers', '?')}` registers, "
                f"`{fpga_resources.get('DSP 9x9', '?')}` DSP 9x9."
            )
        note_lines.extend(
            [
                "- In the paper narrative, use the ONNX Runtime sweep to explain why decode-stage work matters, then use the FPGA result to show that one deterministic score-computation block can be synthesized and observed on hardware.",
            ]
        )

    note_lines.extend(
        [
            "",
            "## Cautions",
            "",
            "- If the ONNX export does not expose reusable past-KV tensors, the script falls back to single-token runs without cache feedback and marks that mode explicitly.",
            "- RSS growth should not be reported as pure KV-cache allocation without that caveat.",
            "- Keep all conclusions limited to profiling evidence plus narrow block-level FPGA validation.",
        ]
    )
    return "\n".join(note_lines) + "\n"


def main() -> None:
    args = parse_args()
    model_path = model_exists(args.model)

    raw_dir = args.out_dir / "raw"
    tables_dir = args.out_dir / "tables"
    figures_dir = args.out_dir / "figures"
    raw_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    latency_rows: list[dict[str, Any]] = []
    kv_rows: list[dict[str, Any]] = []

    for prompt_len in args.prompt_lens:
        run_dir = raw_dir / f"context_{prompt_len}"
        summary = profile_model(
            model_path=model_path,
            provider=args.provider,
            prompt_len=prompt_len,
            decode_tokens=args.decode_tokens,
            out_dir=run_dir,
            enable_profile=args.profile,
        )

        rss_before_prefill = summary["rss_bytes"].get("before_prefill")
        rss_after_prefill = summary["rss_bytes"].get("after_prefill")
        rss_after_decode = summary["rss_bytes"].get("after_decode")
        prefill_rss_delta = delta_bytes(rss_after_prefill, rss_before_prefill)
        decode_rss_delta = delta_bytes(rss_after_decode, rss_after_prefill)
        total_rss_delta = delta_bytes(rss_after_decode, rss_before_prefill)

        theoretical_kv_prompt_bytes = kv_cache_bytes(
            layers=args.layers,
            kv_heads=args.kv_heads,
            head_dim=args.head_dim,
            seq_len=prompt_len,
            bytes_per_element=args.bytes_per_element,
        )
        theoretical_kv_final_bytes = kv_cache_bytes(
            layers=args.layers,
            kv_heads=args.kv_heads,
            head_dim=args.head_dim,
            seq_len=prompt_len + args.decode_tokens,
            bytes_per_element=args.bytes_per_element,
        )
        theoretical_kv_decode_growth_bytes = theoretical_kv_final_bytes - theoretical_kv_prompt_bytes

        latency_rows.append(
            {
                "prompt_len": prompt_len,
                "decode_tokens": args.decode_tokens,
                "decode_mode": summary.get("decode_mode"),
                "session_init_ms": to_ms(summary.get("session_init_s")),
                "prefill_ms": to_ms(summary.get("prefill_s")),
                "decode_avg_ms": to_ms(summary.get("decode_avg_s")),
                "decode_p50_ms": to_ms(summary.get("decode_p50_s")),
                "decode_p95_ms": to_ms(summary.get("decode_p95_s")),
                "decode_last_ms": to_ms(summary["decode_step_s"][-1]) if summary.get("decode_step_s") else None,
                "profile_summary_json": str((run_dir / "profile_summary.json").resolve()),
            }
        )

        kv_rows.append(
            {
                "prompt_len": prompt_len,
                "decode_tokens": args.decode_tokens,
                "decode_mode": summary.get("decode_mode"),
                "rss_before_prefill_bytes": rss_before_prefill,
                "rss_after_prefill_bytes": rss_after_prefill,
                "rss_after_decode_bytes": rss_after_decode,
                "prefill_rss_delta_bytes": prefill_rss_delta,
                "decode_rss_delta_bytes": decode_rss_delta,
                "total_rss_delta_bytes": total_rss_delta,
                "theoretical_kv_prompt_bytes": theoretical_kv_prompt_bytes,
                "theoretical_kv_decode_growth_bytes": theoretical_kv_decode_growth_bytes,
                "theoretical_kv_final_bytes": theoretical_kv_final_bytes,
                "prefill_rss_vs_theoretical_prompt_ratio": safe_ratio(prefill_rss_delta, theoretical_kv_prompt_bytes),
                "decode_rss_vs_theoretical_growth_ratio": safe_ratio(decode_rss_delta, theoretical_kv_decode_growth_bytes),
                "total_rss_vs_theoretical_final_ratio": safe_ratio(total_rss_delta, theoretical_kv_final_bytes),
                "profile_summary_json": str((run_dir / "profile_summary.json").resolve()),
            }
        )

    latency_frame = pd.DataFrame(latency_rows)
    kv_frame = add_ratio_columns(pd.DataFrame(kv_rows))

    latency_csv = tables_dir / "decode_latency_by_context.csv"
    kv_csv = tables_dir / "kv_memory_comparison.csv"
    latency_frame.to_csv(latency_csv, index=False)
    kv_frame.to_csv(kv_csv, index=False)

    plt.figure(figsize=(8, 4.5))
    plt.plot(latency_frame["prompt_len"], latency_frame["decode_avg_ms"], marker="o", label="Decode avg (ms)")
    plt.xlabel("Prompt Length")
    plt.ylabel("Decode Latency (ms)")
    plt.title("Decode Latency by Context Length")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(figures_dir / "decode_latency_by_context.png", dpi=160)
    plt.close()

    plt.figure(figsize=(8, 4.5))
    plt.plot(kv_frame["prompt_len"], kv_frame["theoretical_kv_prompt_mib"], marker="o", label="Theoretical KV-cache (MiB)")
    plt.plot(kv_frame["prompt_len"], kv_frame["prefill_rss_delta_mib"], marker="s", label="Measured RSS delta after prefill (MiB)")
    plt.xlabel("Prompt Length")
    plt.ylabel("Memory (MiB)")
    plt.title("Theoretical KV-cache vs Measured RSS Growth")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / "kv_theoretical_vs_actual_rss.png", dpi=160)
    plt.close()

    args.paper_tables_dir.mkdir(parents=True, exist_ok=True)
    latency_frame.to_csv(args.paper_tables_dir / "decode_latency_by_context.csv", index=False)
    kv_frame.to_csv(args.paper_tables_dir / "kv_memory_comparison.csv", index=False)

    fpga_timing = read_fpga_timing_summary(args.paper_tables_dir)
    fpga_resources = read_fpga_resource_summary(args.paper_tables_dir)
    summary_md = args.out_dir / "decode_fpga_bridge_summary.md"
    summary_md.write_text(
        render_markdown_summary(
            latency_frame=latency_frame,
            kv_frame=kv_frame,
            fpga_summary_path=args.fpga_summary,
            fpga_timing=fpga_timing,
            fpga_resources=fpga_resources,
            output_dir=args.out_dir,
        ),
        encoding="utf-8",
    )

    print(latency_frame.to_string(index=False))
    print()
    print(kv_frame.to_string(index=False))
    print(f"\nSaved latency CSV: {latency_csv}")
    print(f"Saved KV comparison CSV: {kv_csv}")
    print(f"Saved summary: {summary_md}")


if __name__ == "__main__":
    main()
