#!/usr/bin/env python3
"""Generate final representative ONNX projection micrographs."""

from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "onnx_micrographs"


def main() -> None:
    sys.path.insert(0, str(PROJECT_ROOT / "onnx_micrographs"))
    from generate_matvec_micrographs import make_graph, make_matmulinteger_graph

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    specs = [
        ("gemma_mlp_projection_1152x6912_float.onnx", "float", 1152, 6912),
        ("gemma_mlp_projection_1152x6912_matmulinteger.onnx", "int", 1152, 6912),
        ("gemma_lm_head_tile_1152x4096_float.onnx", "float", 1152, 4096),
        ("gemma_lm_head_tile_1152x4096_matmulinteger.onnx", "int", 1152, 4096),
        ("gemma_attention_output_projection_1024x1152_float.onnx", "float", 1024, 1152),
        ("gemma_attention_output_projection_1024x1152_matmulinteger.onnx", "int", 1024, 1152),
    ]
    for name, kind, input_dim, output_dim in specs:
        path = OUT_DIR / name
        if kind == "float":
            make_graph(path, input_dim, output_dim, name)
        else:
            make_matmulinteger_graph(path, input_dim, output_dim, name)
        print(f"wrote {path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
