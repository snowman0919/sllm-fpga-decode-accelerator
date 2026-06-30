#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import onnx


CACHE_KEYWORDS = ("past", "present", "cache", "key_values")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect an exported ONNX graph for profiling readiness.")
    parser.add_argument("--model", type=Path, required=True, help="Path to an ONNX model file.")
    parser.add_argument("--out-dir", type=Path, required=True, help="Base output directory, usually onnx_profile/results.")
    return parser.parse_args()


def tensor_shape(value_info: Any) -> list[Any]:
    shape: list[Any] = []
    tensor_type = value_info.type.tensor_type
    for dim in tensor_type.shape.dim:
        if dim.HasField("dim_value"):
            shape.append(dim.dim_value)
        elif dim.HasField("dim_param"):
            shape.append(dim.dim_param)
        else:
            shape.append("?")
    return shape


def has_external_data(model: onnx.ModelProto) -> bool:
    for initializer in model.graph.initializer:
        if initializer.data_location == onnx.TensorProto.EXTERNAL:
            return True
    return False


def inspect_onnx_model(model_path: Path) -> dict[str, Any]:
    if not model_path.exists() or not model_path.is_file():
        raise FileNotFoundError(f"ONNX model file not found: {model_path}")

    model = onnx.load(str(model_path), load_external_data=False)
    inputs = [
        {
            "name": value.name,
            "shape": tensor_shape(value),
            "elem_type": value.type.tensor_type.elem_type,
        }
        for value in model.graph.input
    ]
    outputs = [
        {
            "name": value.name,
            "shape": tensor_shape(value),
            "elem_type": value.type.tensor_type.elem_type,
        }
        for value in model.graph.output
    ]
    cache_inputs = [item for item in inputs if any(keyword in item["name"].lower() for keyword in CACHE_KEYWORDS)]
    cache_outputs = [item for item in outputs if any(keyword in item["name"].lower() for keyword in CACHE_KEYWORDS)]

    return {
        "model_path": str(model_path.resolve()),
        "ir_version": model.ir_version,
        "opset_imports": [{"domain": item.domain or "ai.onnx", "version": item.version} for item in model.opset_import],
        "graph_name": model.graph.name,
        "input_count": len(inputs),
        "output_count": len(outputs),
        "inputs": inputs,
        "outputs": outputs,
        "cache_input_names": [item["name"] for item in cache_inputs],
        "cache_output_names": [item["name"] for item in cache_outputs],
        "decode_cache_reuse_ready": bool(cache_inputs and cache_outputs),
        "has_external_data": has_external_data(model),
    }


def write_outputs(report: dict[str, Any], out_dir: Path, model_path: Path) -> tuple[Path, Path, Path]:
    raw_dir = out_dir / "raw"
    tables_dir = out_dir / "tables"
    paper_tables_dir = Path("assets")
    raw_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    paper_tables_dir.mkdir(parents=True, exist_ok=True)

    stem = model_path.stem
    json_path = raw_dir / f"{stem}_inspection.json"
    csv_path = tables_dir / f"{stem}_summary.csv"
    paper_csv_path = paper_tables_dir / f"{stem}_summary.csv"

    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    row = {
        "model_path": report["model_path"],
        "graph_name": report["graph_name"],
        "input_count": report["input_count"],
        "output_count": report["output_count"],
        "has_external_data": report["has_external_data"],
        "cache_input_count": len(report["cache_input_names"]),
        "cache_output_count": len(report["cache_output_names"]),
        "decode_cache_reuse_ready": report["decode_cache_reuse_ready"],
        "cache_input_names": "; ".join(report["cache_input_names"]),
        "cache_output_names": "; ".join(report["cache_output_names"]),
        "inspection_json": str(json_path.resolve()),
    }
    fieldnames = list(row.keys())
    for path in (csv_path, paper_csv_path):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(row)
    return json_path, csv_path, paper_csv_path


def main() -> None:
    args = parse_args()
    report = inspect_onnx_model(args.model)
    json_path, csv_path, paper_csv_path = write_outputs(report, args.out_dir, args.model)
    print(json.dumps(report, indent=2))
    print(f"\nSaved JSON: {json_path}")
    print(f"Saved CSV: {csv_path}")
    print(f"Saved paper CSV: {paper_csv_path}")


if __name__ == "__main__":
    main()
