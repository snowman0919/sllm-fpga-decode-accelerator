#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


TOKENIZER_FILES = [
    "tokenizer.json",
    "tokenizer.model",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "added_tokens.json",
]
REQUIRED_CORE_FILES = ["config.json"]


def kv_cache_bytes(layers: int, kv_heads: int, head_dim: int, seq_len: int, bytes_per_element: int) -> int:
    return 2 * layers * kv_heads * head_dim * seq_len * bytes_per_element


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect a raw Hugging Face model directory before ONNX export.")
    parser.add_argument("--model-dir", type=Path, required=True, help="Path to the raw Hugging Face model directory.")
    parser.add_argument("--out-dir", type=Path, required=True, help="Base output directory, usually onnx_profile/results.")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dtype_bytes(torch_dtype: str | None) -> int | None:
    mapping = {
        "float32": 4,
        "float": 4,
        "float16": 2,
        "half": 2,
        "bfloat16": 2,
        "int8": 1,
        "uint8": 1,
        "int16": 2,
        "int32": 4,
        "int64": 8,
    }
    if torch_dtype is None:
        return None
    return mapping.get(torch_dtype.lower())


def derive_head_dim(config: dict[str, Any]) -> int | None:
    if isinstance(config.get("head_dim"), int):
        return int(config["head_dim"])
    hidden_size = config.get("hidden_size")
    num_attention_heads = config.get("num_attention_heads")
    if isinstance(hidden_size, int) and isinstance(num_attention_heads, int) and num_attention_heads > 0:
        if hidden_size % num_attention_heads == 0:
            return hidden_size // num_attention_heads
    return None


def build_summary_row(report: dict[str, Any], json_path: Path) -> dict[str, Any]:
    cfg = report.get("config_summary", {})
    kv_defaults = report.get("kv_cache_defaults", {})
    return {
        "model_dir": report["model_dir"],
        "inspection_passed": report["inspection_passed"],
        "missing_required_items": "; ".join(report["missing_required_items"]),
        "model_type": cfg.get("model_type"),
        "architectures": "; ".join(cfg.get("architectures", [])),
        "hidden_size": cfg.get("hidden_size"),
        "num_hidden_layers": cfg.get("num_hidden_layers"),
        "num_attention_heads": cfg.get("num_attention_heads"),
        "num_key_value_heads": cfg.get("num_key_value_heads"),
        "head_dim": cfg.get("head_dim"),
        "vocab_size": cfg.get("vocab_size"),
        "torch_dtype": cfg.get("torch_dtype"),
        "max_position_embeddings": cfg.get("max_position_embeddings"),
        "safetensors_count": len(report["safetensors_files"]),
        "has_model_safetensors_index": report["files"]["model_safetensors_index_json"]["exists"],
        "has_pytorch_model_bin": report["files"]["pytorch_model_bin"]["exists"],
        "kv_cache_args_ready": kv_defaults.get("ready", False),
        "kv_cache_layers": kv_defaults.get("layers"),
        "kv_cache_kv_heads": kv_defaults.get("kv_heads"),
        "kv_cache_head_dim": kv_defaults.get("head_dim"),
        "kv_cache_bytes_per_element": kv_defaults.get("bytes_per_element"),
        "inspection_json": str(json_path.resolve()),
    }


def inspect_model_dir(model_dir: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "model_dir": str(model_dir.resolve()),
        "inspection_passed": False,
        "missing_required_items": [],
        "files": {},
        "safetensors_files": [],
        "config_summary": {},
        "kv_cache_defaults": {"ready": False},
    }

    if not model_dir.exists() or not model_dir.is_dir():
        report["missing_required_items"].append(f"model directory missing: {model_dir}")
        return report

    for name in REQUIRED_CORE_FILES:
        path = model_dir / name
        report["files"][name.replace(".", "_")] = {
            "path": str(path.resolve()),
            "exists": path.is_file(),
        }
        if not path.is_file():
            report["missing_required_items"].append(f"missing required file: {name}")

    tokenizer_presence = []
    for name in TOKENIZER_FILES:
        path = model_dir / name
        exists = path.is_file()
        tokenizer_presence.append(exists)
        report["files"][name.replace(".", "_")] = {
            "path": str(path.resolve()),
            "exists": exists,
        }

    tokenizer_config_exists = (model_dir / "tokenizer_config.json").is_file()
    tokenizer_main_exists = any((model_dir / name).is_file() for name in ("tokenizer.json", "tokenizer.model"))
    if not tokenizer_config_exists:
        report["missing_required_items"].append("missing required tokenizer file: tokenizer_config.json")
    if not tokenizer_main_exists:
        report["missing_required_items"].append("missing tokenizer payload: tokenizer.json or tokenizer.model")

    safetensors_files = sorted(model_dir.glob("*.safetensors"))
    report["safetensors_files"] = [str(path.resolve()) for path in safetensors_files]
    if not safetensors_files:
        report["missing_required_items"].append("missing safetensors weights (*.safetensors)")

    model_index_path = model_dir / "model.safetensors.index.json"
    pytorch_bin_path = model_dir / "pytorch_model.bin"
    report["files"]["model_safetensors_index_json"] = {
        "path": str(model_index_path.resolve()),
        "exists": model_index_path.is_file(),
    }
    report["files"]["pytorch_model_bin"] = {
        "path": str(pytorch_bin_path.resolve()),
        "exists": pytorch_bin_path.is_file(),
    }

    config_path = model_dir / "config.json"
    if config_path.is_file():
        config = read_json(config_path)
        head_dim = derive_head_dim(config)
        cfg = {
            "model_type": config.get("model_type"),
            "architectures": config.get("architectures", []),
            "hidden_size": config.get("hidden_size"),
            "num_hidden_layers": config.get("num_hidden_layers"),
            "num_attention_heads": config.get("num_attention_heads"),
            "num_key_value_heads": config.get("num_key_value_heads"),
            "head_dim": head_dim,
            "vocab_size": config.get("vocab_size"),
            "torch_dtype": config.get("torch_dtype"),
            "max_position_embeddings": config.get("max_position_embeddings"),
            "use_cache": config.get("use_cache"),
            "cache_implementation": config.get("cache_implementation"),
        }
        report["config_summary"] = cfg

        bytes_per_element = dtype_bytes(config.get("torch_dtype"))
        layers = config.get("num_hidden_layers")
        kv_heads = config.get("num_key_value_heads")
        if isinstance(layers, int) and isinstance(kv_heads, int) and isinstance(head_dim, int) and bytes_per_element is not None:
            report["kv_cache_defaults"] = {
                "ready": True,
                "layers": layers,
                "kv_heads": kv_heads,
                "head_dim": head_dim,
                "bytes_per_element": bytes_per_element,
                "theoretical_examples": [
                    {
                        "sequence_length": seq_len,
                        "kv_cache_bytes": kv_cache_bytes(layers, kv_heads, head_dim, seq_len, bytes_per_element),
                        "kv_cache_mib": kv_cache_bytes(layers, kv_heads, head_dim, seq_len, bytes_per_element) / (1024 ** 2),
                    }
                    for seq_len in (128, 1024, 4096)
                ],
            }

    report["inspection_passed"] = len(report["missing_required_items"]) == 0
    return report


def write_outputs(report: dict[str, Any], out_dir: Path) -> tuple[Path, Path, Path]:
    raw_dir = out_dir / "raw"
    tables_dir = out_dir / "tables"
    paper_tables_dir = Path("paper_assets/tables")
    raw_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    paper_tables_dir.mkdir(parents=True, exist_ok=True)

    json_path = raw_dir / "hf_model_dir_inspection.json"
    csv_path = tables_dir / "hf_model_dir_summary.csv"
    paper_csv_path = paper_tables_dir / "hf_model_dir_summary.csv"

    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    row = build_summary_row(report, json_path)
    fieldnames = list(row.keys())
    for path in (csv_path, paper_csv_path):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(row)

    return json_path, csv_path, paper_csv_path


def main() -> None:
    args = parse_args()
    report = inspect_model_dir(args.model_dir)
    json_path, csv_path, paper_csv_path = write_outputs(report, args.out_dir)

    print(json.dumps(report, indent=2))
    print(f"\nSaved JSON: {json_path}")
    print(f"Saved CSV: {csv_path}")
    print(f"Saved paper CSV: {paper_csv_path}")

    if not report["inspection_passed"]:
        missing = "\n".join(f"- {item}" for item in report["missing_required_items"])
        raise SystemExit(f"HF model directory inspection failed.\nMissing or invalid items:\n{missing}")


if __name__ == "__main__":
    main()
