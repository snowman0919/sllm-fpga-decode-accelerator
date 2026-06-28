#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


DEFAULT_SEQ_LENS = [128, 512, 1024, 2048, 4096]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute theoretical KV-cache sizes.")
    parser.add_argument("--layers", type=int, required=True, help="Number of transformer layers.")
    parser.add_argument("--kv-heads", type=int, required=True, help="Number of KV heads.")
    parser.add_argument("--head-dim", type=int, required=True, help="Per-head dimension.")
    parser.add_argument(
        "--bytes-per-element",
        type=int,
        required=True,
        help="Bytes per cache element, for example 2 for FP16.",
    )
    parser.add_argument(
        "--seq-lens",
        type=int,
        nargs="+",
        default=DEFAULT_SEQ_LENS,
        help="Sequence lengths to evaluate.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Output directory for CSV and PNG results.",
    )
    return parser.parse_args()


def kv_cache_bytes(layers: int, kv_heads: int, head_dim: int, seq_len: int, bytes_per_element: int) -> int:
    return 2 * layers * kv_heads * head_dim * seq_len * bytes_per_element


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for seq_len in args.seq_lens:
        total_bytes = kv_cache_bytes(
            layers=args.layers,
            kv_heads=args.kv_heads,
            head_dim=args.head_dim,
            seq_len=seq_len,
            bytes_per_element=args.bytes_per_element,
        )
        rows.append(
            {
                "sequence_length": seq_len,
                "kv_cache_bytes": total_bytes,
                "kv_cache_mib": total_bytes / (1024 ** 2),
            }
        )

    frame = pd.DataFrame(rows)

    tables_dir = args.out_dir / "tables"
    figures_dir = args.out_dir / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    csv_path = tables_dir / "kv_cache_sizes.csv"
    png_path = figures_dir / "kv_cache_sizes.png"

    frame.to_csv(csv_path, index=False)

    plt.figure(figsize=(8, 4.5))
    plt.plot(frame["sequence_length"], frame["kv_cache_mib"], marker="o")
    plt.xlabel("Sequence Length")
    plt.ylabel("KV-cache Size (MiB)")
    plt.title("Theoretical KV-cache Size")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(png_path, dpi=160)
    plt.close()

    print(frame.to_string(index=False))
    print(f"\nSaved CSV: {csv_path}")
    print(f"Saved plot: {png_path}")


if __name__ == "__main__":
    main()
