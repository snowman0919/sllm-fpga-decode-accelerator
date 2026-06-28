#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

try:
    import psutil
except ImportError:  # pragma: no cover - optional dependency
    psutil = None


DTYPE_MAP = {
    "auto": None,
    "float32": torch.float32,
    "float": torch.float32,
    "float16": torch.float16,
    "fp16": torch.float16,
    "bfloat16": torch.bfloat16,
    "bf16": torch.bfloat16,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Profile a raw Hugging Face Gemma directory with Transformers/PyTorch."
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("/home/monad/develop/ai_accel/gemma3-1B"),
        help="Path to the raw Hugging Face Gemma model directory.",
    )
    parser.add_argument("--prompt", required=True, help="Prompt text to tokenize and run.")
    parser.add_argument("--new-tokens", type=int, default=8, help="Number of greedy tokens to generate.")
    parser.add_argument("--device", default="cpu", help="Torch device, for example cpu or cuda.")
    parser.add_argument(
        "--dtype",
        default="auto",
        choices=sorted(DTYPE_MAP.keys()),
        help="Weight dtype to request when loading the model.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("onnx_profile/results"),
        help="Base output directory. JSON goes to raw/ and CSV goes to tables/.",
    )
    parser.add_argument(
        "--trust-remote-code",
        action="store_true",
        help="Pass trust_remote_code=True when loading the tokenizer and model.",
    )
    return parser.parse_args()


def rss_bytes() -> int | None:
    if psutil is None:
        return None
    return psutil.Process().memory_info().rss


def bytes_to_mib(value: int | None) -> float | None:
    if value is None:
        return None
    return value / (1024.0 * 1024.0)


def ensure_model_dir(model_dir: Path) -> Path:
    resolved = model_dir.resolve()
    if not resolved.is_dir():
        raise FileNotFoundError(f"Model directory does not exist: {resolved}")
    if not (resolved / "config.json").is_file():
        raise FileNotFoundError(f"Missing config.json in model directory: {resolved}")
    return resolved


def kv_cache_defaults(config: Any) -> dict[str, Any]:
    layers = getattr(config, "num_hidden_layers", None)
    kv_heads = getattr(config, "num_key_value_heads", None)
    head_dim = getattr(config, "head_dim", None)
    torch_dtype = getattr(config, "torch_dtype", None)
    if isinstance(torch_dtype, torch.dtype):
        torch_dtype = str(torch_dtype).replace("torch.", "")

    bytes_per_element = None
    if torch_dtype in {"bfloat16", "float16"}:
        bytes_per_element = 2
    elif torch_dtype == "float32":
        bytes_per_element = 4

    ready = all(value is not None for value in [layers, kv_heads, head_dim, bytes_per_element])
    return {
        "ready": ready,
        "layers": layers,
        "kv_heads": kv_heads,
        "head_dim": head_dim,
        "bytes_per_element": bytes_per_element,
    }


def theoretical_kv_cache_bytes(sequence_length: int, defaults: dict[str, Any]) -> int | None:
    if not defaults["ready"]:
        return None
    return (
        2
        * int(defaults["layers"])
        * int(defaults["kv_heads"])
        * int(defaults["head_dim"])
        * int(sequence_length)
        * int(defaults["bytes_per_element"])
    )


def to_device(inputs: dict[str, torch.Tensor], device: str) -> dict[str, torch.Tensor]:
    return {name: tensor.to(device) for name, tensor in inputs.items()}


def serialize_dtype(dtype: torch.dtype | None) -> str:
    return str(dtype).replace("torch.", "") if dtype is not None else "auto"


def serialize_cache(cache: Any) -> dict[str, Any]:
    if cache is None:
        return {"type": None}
    info = {"type": type(cache).__name__}
    if hasattr(cache, "get_seq_length"):
        try:
            info["seq_length"] = int(cache.get_seq_length())
        except Exception:
            info["seq_length"] = None
    return info


def safe_decode(tokenizer: Any, token_ids: list[int]) -> str:
    if not token_ids:
        return ""
    return tokenizer.decode(token_ids, skip_special_tokens=True)


def write_step_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "decode_forward_index",
                "latency_ms",
                "generated_token_id",
                "generated_token_text",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    model_dir = ensure_model_dir(args.model_dir)
    out_dir = args.out_dir.resolve()
    raw_dir = out_dir / "raw"
    tables_dir = out_dir / "tables"
    raw_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    requested_dtype = DTYPE_MAP[args.dtype]
    rss_before_load = rss_bytes()

    load_start = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=args.trust_remote_code)
    model_kwargs: dict[str, Any] = {"trust_remote_code": args.trust_remote_code}
    if requested_dtype is not None:
        model_kwargs["dtype"] = requested_dtype
    model = AutoModelForCausalLM.from_pretrained(model_dir, **model_kwargs)
    model.to(args.device)
    model.eval()
    load_seconds = time.perf_counter() - load_start
    rss_after_load = rss_bytes()

    tokenize_start = time.perf_counter()
    encoded = tokenizer(args.prompt, return_tensors="pt")
    encoded = to_device(encoded, args.device)
    prompt_token_count = int(encoded["input_ids"].shape[-1])
    tokenize_seconds = time.perf_counter() - tokenize_start

    with torch.no_grad():
        prefill_start = time.perf_counter()
        prefill_outputs = model(**encoded, use_cache=True)
        prefill_seconds = time.perf_counter() - prefill_start

    rss_after_prefill = rss_bytes()

    generated_ids = encoded["input_ids"]
    attention_mask = encoded.get("attention_mask")
    cache = prefill_outputs.past_key_values
    first_token = torch.argmax(prefill_outputs.logits[:, -1, :], dim=-1, keepdim=True)
    generated_token_ids: list[int] = []
    decode_step_rows: list[dict[str, Any]] = []
    decode_forward_seconds: list[float] = []

    if args.new_tokens > 0:
        generated_ids = torch.cat([generated_ids, first_token], dim=-1)
        generated_token_ids.append(int(first_token[0, 0].item()))
        if attention_mask is not None:
            one_mask = torch.ones((attention_mask.shape[0], 1), dtype=attention_mask.dtype, device=attention_mask.device)
            attention_mask = torch.cat([attention_mask, one_mask], dim=-1)

    for decode_forward_index in range(max(args.new_tokens - 1, 0)):
        cache_position = torch.tensor(
            [generated_ids.shape[1] - 1],
            device=generated_ids.device,
            dtype=torch.long,
        )
        model_inputs = model.prepare_inputs_for_generation(
            generated_ids,
            past_key_values=cache,
            attention_mask=attention_mask,
            cache_position=cache_position,
            use_cache=True,
        )

        with torch.no_grad():
            step_start = time.perf_counter()
            decode_outputs = model(**model_inputs)
            step_seconds = time.perf_counter() - step_start

        decode_forward_seconds.append(step_seconds)
        cache = decode_outputs.past_key_values
        next_token = torch.argmax(decode_outputs.logits[:, -1, :], dim=-1, keepdim=True)
        token_id = int(next_token[0, 0].item())
        generated_token_ids.append(token_id)
        generated_ids = torch.cat([generated_ids, next_token], dim=-1)

        if attention_mask is not None:
            one_mask = torch.ones((attention_mask.shape[0], 1), dtype=attention_mask.dtype, device=attention_mask.device)
            attention_mask = torch.cat([attention_mask, one_mask], dim=-1)

        decode_step_rows.append(
            {
                "decode_forward_index": decode_forward_index,
                "latency_ms": round(step_seconds * 1000.0, 3),
                "generated_token_id": token_id,
                "generated_token_text": safe_decode(tokenizer, [token_id]),
            }
        )

    rss_after_decode = rss_bytes()
    final_sequence_length = int(generated_ids.shape[-1])
    prompt_kv_bytes = theoretical_kv_cache_bytes(prompt_token_count, kv_cache_defaults(model.config))
    final_kv_bytes = theoretical_kv_cache_bytes(final_sequence_length, kv_cache_defaults(model.config))

    result = {
        "model_dir": str(model_dir),
        "device": args.device,
        "requested_dtype": args.dtype,
        "resolved_model_dtype": serialize_dtype(getattr(model, "dtype", requested_dtype)),
        "prompt": args.prompt,
        "prompt_token_count": prompt_token_count,
        "new_tokens_requested": args.new_tokens,
        "new_tokens_generated": len(generated_token_ids),
        "first_generated_token_from_prefill_logits": args.new_tokens > 0,
        "decode_forward_pass_count": len(decode_forward_seconds),
        "tokenize_seconds": tokenize_seconds,
        "load_seconds": load_seconds,
        "prefill_seconds": prefill_seconds,
        "decode_forward_seconds_total": sum(decode_forward_seconds),
        "decode_forward_seconds_avg": (
            sum(decode_forward_seconds) / len(decode_forward_seconds) if decode_forward_seconds else None
        ),
        "decode_forward_seconds_per_step": decode_forward_seconds,
        "generated_token_ids": generated_token_ids,
        "generated_text_suffix": safe_decode(tokenizer, generated_token_ids),
        "full_decoded_text": tokenizer.decode(generated_ids[0], skip_special_tokens=True),
        "cache_summary": serialize_cache(cache),
        "config_summary": {
            "model_type": getattr(model.config, "model_type", None),
            "architectures": getattr(model.config, "architectures", None),
            "hidden_size": getattr(model.config, "hidden_size", None),
            "num_hidden_layers": getattr(model.config, "num_hidden_layers", None),
            "num_attention_heads": getattr(model.config, "num_attention_heads", None),
            "num_key_value_heads": getattr(model.config, "num_key_value_heads", None),
            "head_dim": getattr(model.config, "head_dim", None),
            "max_position_embeddings": getattr(model.config, "max_position_embeddings", None),
            "use_cache": getattr(model.config, "use_cache", None),
            "cache_implementation": getattr(model.config, "cache_implementation", None),
        },
        "kv_cache_theoretical": {
            "prompt_sequence_length": prompt_token_count,
            "prompt_kv_cache_bytes": prompt_kv_bytes,
            "prompt_kv_cache_mib": bytes_to_mib(prompt_kv_bytes),
            "final_sequence_length": final_sequence_length,
            "final_kv_cache_bytes": final_kv_bytes,
            "final_kv_cache_mib": bytes_to_mib(final_kv_bytes),
        },
        "rss_bytes": {
            "before_load": rss_before_load,
            "after_load": rss_after_load,
            "after_prefill": rss_after_prefill,
            "after_decode": rss_after_decode,
            "delta_load": (
                rss_after_load - rss_before_load if rss_before_load is not None and rss_after_load is not None else None
            ),
            "delta_prefill": (
                rss_after_prefill - rss_after_load if rss_after_prefill is not None and rss_after_load is not None else None
            ),
            "delta_decode": (
                rss_after_decode - rss_after_prefill
                if rss_after_decode is not None and rss_after_prefill is not None
                else None
            ),
        },
        "rss_mib": {
            "before_load": bytes_to_mib(rss_before_load),
            "after_load": bytes_to_mib(rss_after_load),
            "after_prefill": bytes_to_mib(rss_after_prefill),
            "after_decode": bytes_to_mib(rss_after_decode),
            "delta_load": bytes_to_mib(
                rss_after_load - rss_before_load if rss_before_load is not None and rss_after_load is not None else None
            ),
            "delta_prefill": bytes_to_mib(
                rss_after_prefill - rss_after_load if rss_after_prefill is not None and rss_after_load is not None else None
            ),
            "delta_decode": bytes_to_mib(
                rss_after_decode - rss_after_prefill
                if rss_after_decode is not None and rss_after_prefill is not None
                else None
            ),
        },
        "notes": [
            "This script profiles the raw Hugging Face Gemma directory with Transformers/PyTorch, not ONNX Runtime.",
            "Prefill is the full-prompt forward pass.",
            "Decode timing covers cached forward passes after the first generated token is selected from prefill logits.",
            "Do not compare these numbers as FPGA speedup evidence.",
        ],
    }

    json_path = raw_dir / "torch_gemma_profile.json"
    csv_path = tables_dir / "torch_gemma_decode_step_latencies.csv"
    json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_step_csv(csv_path, decode_step_rows)

    print(json.dumps(result, indent=2))
    print(f"\nSaved JSON: {json_path}")
    print(f"Saved CSV: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
