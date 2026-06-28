#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export deterministic INT8 Q/K vectors for FPGA testing.")
    parser.add_argument("--dim", type=int, default=16, help="Vector dimension.")
    parser.add_argument("--num-keys", type=int, default=8, help="Number of key vectors to generate.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed.")
    parser.add_argument("--out-dir", type=Path, required=True, help="Output directory.")
    return parser.parse_args()


def int8_to_hex(value: int) -> str:
    return f"{(int(value) & 0xFF):02x}"


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    q_vector = rng.integers(-128, 128, size=args.dim, dtype=np.int16).astype(np.int8)
    k_cache = rng.integers(-128, 128, size=(args.num_keys, args.dim), dtype=np.int16).astype(np.int8)

    scores = (k_cache.astype(np.int32) * q_vector.astype(np.int32)).sum(axis=1, dtype=np.int32)

    q_path = args.out_dir / "q_vector.hex"
    k_path = args.out_dir / "k_cache.hex"
    scores_path = args.out_dir / "expected_scores.csv"

    with q_path.open("w", encoding="utf-8") as handle:
      handle.write("# Two's complement INT8, one byte per line, q[0]..q[dim-1]\n")
      for value in q_vector:
          handle.write(f"{int8_to_hex(int(value))}\n")

    with k_path.open("w", encoding="utf-8") as handle:
      handle.write("# Two's complement INT8, one key vector per line, bytes separated by spaces\n")
      for row in k_cache:
          handle.write(" ".join(int8_to_hex(int(value)) for value in row) + "\n")

    frame = pd.DataFrame(
        {
            "key_index": np.arange(args.num_keys, dtype=np.int32),
            "expected_score_int32": scores.astype(np.int32),
        }
    )
    frame.to_csv(scores_path, index=False)

    print(f"Saved query vector: {q_path}")
    print(f"Saved key cache: {k_path}")
    print(f"Saved expected scores: {scores_path}")


if __name__ == "__main__":
    main()
