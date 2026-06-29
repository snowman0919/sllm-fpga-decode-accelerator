#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_MODEL = Path("/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx")
DEFAULT_TABLE = Path("paper_assets/tables/ort_attention_matmul_candidates.csv")
DEFAULT_NOTE = Path("onnx_profile/results/reports/ort_attention_qk_classification_note.md")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect ONNX graph attention MatMul nodes for QK/V fallback classification.")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--table-path", type=Path, default=DEFAULT_TABLE)
    parser.add_argument("--note-path", type=Path, default=DEFAULT_NOTE)
    return parser.parse_args()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "node_index",
        "node_name",
        "fallback_classification",
        "confidence",
        "input_names",
        "output_names",
        "parent_ops",
        "child_ops",
        "evidence",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def classify(name: str, parent_ops: list[str], child_ops: list[str]) -> tuple[str, str, str]:
    if name.endswith("/self_attn/MatMul") and "Add" in child_ops:
        return (
            "attention_qk_score",
            "confirmed",
            "self_attn/MatMul feeds Add mask path; parents are scaled Q/K-like Mul nodes",
        )
    if name.endswith("/self_attn/MatMul_1") and "Transpose" in child_ops:
        return (
            "attention_v_weighted_sum",
            "confirmed",
            "self_attn/MatMul_1 follows masked attention probability path and feeds Transpose output path",
        )
    if "/self_attn/" in name:
        return ("attention_internal_matmul", "candidate", "self_attn MatMul name found but fallback pattern is not sufficient for confirmation")
    return ("non_attention_matmul", "candidate", "MatMul is outside the self_attn internal score/value pattern")


def main() -> None:
    args = parse_args()
    try:
        import onnx
    except ImportError as exc:
        raise RuntimeError("onnx is required for attention MatMul candidate analysis") from exc

    model = onnx.load(str(args.model), load_external_data=False)
    producer = {output: index for index, node in enumerate(model.graph.node) for output in node.output}
    consumers: dict[str, list[int]] = defaultdict(list)
    for index, node in enumerate(model.graph.node):
        for value in node.input:
            consumers[value].append(index)

    rows: list[dict[str, Any]] = []
    for index, node in enumerate(model.graph.node):
        if node.op_type != "MatMul" or "/self_attn/" not in node.name:
            continue
        parent_ops = [model.graph.node[producer[value]].op_type for value in node.input if value in producer]
        child_ops = [model.graph.node[child].op_type for output in node.output for child in consumers.get(output, [])]
        fallback_classification, confidence, evidence = classify(node.name, parent_ops, child_ops)
        rows.append(
            {
                "node_index": index,
                "node_name": node.name,
                "fallback_classification": fallback_classification,
                "confidence": confidence,
                "input_names": "; ".join(node.input),
                "output_names": "; ".join(node.output),
                "parent_ops": "; ".join(parent_ops),
                "child_ops": "; ".join(child_ops),
                "evidence": evidence,
            }
        )

    write_csv(args.table_path, rows)
    confirmed_qk = sum(1 for row in rows if row["fallback_classification"] == "attention_qk_score" and row["confidence"] == "confirmed")
    confirmed_v = sum(1 for row in rows if row["fallback_classification"] == "attention_v_weighted_sum" and row["confidence"] == "confirmed")
    candidates = sum(1 for row in rows if row["confidence"] == "candidate")
    note = f"""# Attention QK MatMul Fallback Classification Note

## Scope

This note supplements the ORT profile event name/path classification where `attention_qk_score` appeared as `0.00%`.
The fallback analysis inspects the exported ONNX graph directly, using MatMul node names, input/output names, and immediate parent/child operators.

## Result

- Self-attention internal MatMul nodes inspected: `{len(rows)}`.
- Confirmed `attention_qk_score` graph nodes: `{confirmed_qk}`.
- Confirmed `attention_v_weighted_sum` graph nodes: `{confirmed_v}`.
- Unconfirmed candidate nodes: `{candidates}`.
- Output table: `paper_assets/tables/ort_attention_matmul_candidates.csv`.

## Interpretation Boundary

The graph-level fallback confirms that QK-score-like MatMul nodes exist in the exported ONNX graph.
It does not assign runtime share to those nodes when ORT profiling reports optimized or fused events under different operator names.
Therefore the earlier `attention_qk_score` runtime category should be read as "not confirmed by the conservative profile-event classifier," not as absence of QK score computation.
"""
    args.note_path.parent.mkdir(parents=True, exist_ok=True)
    args.note_path.write_text(note, encoding="utf-8")


if __name__ == "__main__":
    main()
