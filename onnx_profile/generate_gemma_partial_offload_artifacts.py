#!/usr/bin/env python3
"""Create Gemma-derived partial offload candidate tables and tiny tile graphs."""

from __future__ import annotations

import argparse
import ast
import csv
from pathlib import Path


PREFERRED_CATEGORIES = ["mlp_projection", "lm_head", "attention_qkv_projection", "attention_output_projection"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-nodes-csv", default="paper_assets/tables/ort_matmul_top_nodes.csv")
    parser.add_argument("--out-csv", default="paper_assets/tables/gemma_partial_offload_candidates.csv")
    parser.add_argument("--plan-md", default="docs/gemma_partial_offload_plan.md")
    parser.add_argument("--patch-notes-md", default="docs/gemma_onnx_patch_notes.md")
    parser.add_argument("--micrograph-dir", default="onnx_micrographs")
    parser.add_argument("--tile-input-dim", type=int, default=16)
    parser.add_argument("--tile-output-dim", type=int, default=4)
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_shape(cell: str) -> str:
    if not cell:
        return "unknown"
    try:
        parsed = ast.literal_eval(cell)
    except (ValueError, SyntaxError):
        return "unknown"
    if not parsed or not isinstance(parsed, list):
        return "unknown"
    first = parsed[0]
    if isinstance(first, dict) and first:
        return str(next(iter(first.values())))
    return str(first)


def select_candidates(rows: list[dict[str, str]], tile_input_dim: int, tile_output_dim: int) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    seen: set[str] = set()
    for category in PREFERRED_CATEGORIES:
        for row in rows:
            node_name = row.get("node_name", "")
            if row.get("category") != category or node_name in seen:
                continue
            input_shape = parse_shape(row.get("example_input_type_shape", ""))
            output_shape = parse_shape(row.get("example_output_type_shape", ""))
            if category == "lm_head":
                selected_tile = f"[1,{tile_input_dim}] x [{tile_input_dim},{tile_output_dim}] vocabulary tile"
                reason = "lm_head is a measured MatMul hotspot, but only a tiny output tile is feasible for UART validation."
                mode = "small output tile extraction only"
            elif category == "mlp_projection":
                selected_tile = f"[1,{tile_input_dim}] x [{tile_input_dim},{tile_output_dim}] projection tile"
                reason = "MLP projection has the highest cumulative MatMul share and maps to a tiled MatVec path."
                mode = "Gemma-derived projection tile micrograph"
            else:
                selected_tile = f"[1,{tile_input_dim}] x [{tile_input_dim},{tile_output_dim}] candidate tile"
                reason = "Recorded as a secondary candidate from the observed MatMul categories."
                mode = "candidate only unless a later tile benchmark is logged"
            selected.append(
                {
                    "node_name": node_name,
                    "category": category,
                    "input_shape": input_shape,
                    "weight_shape": "not resolved from external initializers in this lightweight artifact step",
                    "output_shape": output_shape,
                    "selected_tile_shape": selected_tile,
                    "reason": reason,
                    "replacement_mode": mode,
                    "claim_boundary": "partial node/tile offload feasibility only; no full Gemma ONNX execution or speedup claim",
                }
            )
            seen.add(node_name)
            break
    return selected


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_plan(path: Path, rows: list[dict[str, object]]) -> None:
    lines = [
        "# Gemma-Derived Partial Offload Plan",
        "",
        "This plan selects small MatMul tiles from measured Gemma ONNX MatMul categories. It does not patch or accelerate the full Gemma 3 1B graph.",
        "",
        "## Selection Rules",
        "",
        "- Prefer `mlp_projection` because it has the highest cumulative MatMul contribution in the current ORT profile artifacts.",
        "- Treat `lm_head` as a tile-only candidate; full vocabulary projection over UART is intentionally out of scope.",
        "- Use synthetic deterministic activation/weight values unless a later experiment resolves and records a real external initializer tile.",
        "- Record all results as partial node/tile feasibility evidence only.",
        "",
        "## Candidates",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"### {row['category']}: `{row['node_name']}`",
                "",
                f"- input_shape: {row['input_shape']}",
                f"- output_shape: {row['output_shape']}",
                f"- selected_tile_shape: {row['selected_tile_shape']}",
                f"- replacement_mode: {row['replacement_mode']}",
                f"- claim_boundary: {row['claim_boundary']}",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_patch_notes(path: Path) -> None:
    text = """# Gemma ONNX Patch Notes

No full Gemma ONNX graph patch is claimed by the current artifact generator.

The implemented path creates Gemma-derived tile micrographs and candidate
tables from observed MatMul hotspots. A direct one-node graph patch should only
be promoted to a result after shape inference passes, ONNX Runtime can load the
patched graph with the intended custom op or explicit stub behavior, and a
correctness harness compares the patched node output against a CPU reference.
Until those conditions are met, full-graph patching remains future work.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_micrograph(path: Path, input_dim: int, output_dim: int) -> None:
    try:
        import onnx
        from onnx import TensorProto, helper
    except ImportError:
        path.with_suffix(".missing_onnx.txt").write_text(
            "onnx is not installed; rerun this generator in the Nix shell or Windows venv.\n",
            encoding="utf-8",
        )
        return

    activation = helper.make_tensor_value_info("activation", TensorProto.FLOAT, [1, input_dim])
    weight = helper.make_tensor_value_info("weight", TensorProto.FLOAT, [input_dim, output_dim])
    output = helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, output_dim])
    node = helper.make_node("MatMul", ["activation", "weight"], ["output"], name=path.stem)
    graph = helper.make_graph([node], path.stem, [activation, weight], [output])
    model = helper.make_model(graph, producer_name="gemma-derived-partial-tile", opset_imports=[helper.make_operatorsetid("", 17)])
    model.ir_version = min(model.ir_version, 10)
    onnx.checker.check_model(model)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, path)


def main() -> None:
    args = parse_args()
    rows = read_rows(Path(args.top_nodes_csv))
    candidates = select_candidates(rows, args.tile_input_dim, args.tile_output_dim)
    write_csv(Path(args.out_csv), candidates)
    write_plan(Path(args.plan_md), candidates)
    write_patch_notes(Path(args.patch_notes_md))
    micro_dir = Path(args.micrograph_dir)
    make_micrograph(micro_dir / "gemma_mlp_projection_tile_cpu.onnx", args.tile_input_dim, args.tile_output_dim)
    make_micrograph(micro_dir / "gemma_mlp_projection_tile_fpga_stub.onnx", args.tile_input_dim, args.tile_output_dim)
    make_micrograph(micro_dir / "gemma_lm_head_tile_cpu.onnx", args.tile_input_dim, args.tile_output_dim)
    make_micrograph(micro_dir / "gemma_lm_head_tile_fpga_stub.onnx", args.tile_input_dim, args.tile_output_dim)
    print(f"wrote {args.out_csv}")
    print(f"wrote {args.plan_md}")


if __name__ == "__main__":
    main()
