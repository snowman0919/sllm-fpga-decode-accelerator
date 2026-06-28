#!/usr/bin/env python3

from __future__ import annotations

import argparse
import gc
import inspect
import json
import math
import resource
import statistics
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

plt = None
pd = None
torch = None
AutoModelForCausalLM = None
AutoTokenizer = None

DEFAULT_CONTEXT_LENGTHS = [128, 512, 1024, 2048, 4096, 8192, 16384, 32768]
DEFAULT_PROMPT_TEXT = (
    "PyTorch baseline context sweep for Gemma 3 1B decode profiling. "
    "This host-side run measures prefill and decode latency with KV-cache reuse."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "PyTorch/Transformers host-side context sweep baseline for Gemma 3 1B. "
            "This script is not an ONNX Runtime profiler."
        )
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        required=True,
        help="Path to the local safetensors model directory.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Directory for raw and tabular outputs.",
    )
    parser.add_argument(
        "--device",
        default="auto",
        help="Execution device: auto, cpu, cuda, or cuda:N. Falls back to cpu if the requested GPU is unavailable.",
    )
    parser.add_argument(
        "--dtype",
        default="auto",
        help="Model dtype: auto, float32, float16, or bfloat16. Auto uses float32 on cpu and float16 on cuda.",
    )
    parser.add_argument(
        "--context-lengths",
        type=int,
        nargs="+",
        default=DEFAULT_CONTEXT_LENGTHS,
        help="Prompt lengths to sweep.",
    )
    parser.add_argument(
        "--decode-tokens",
        type=int,
        default=8,
        help="Number of decode steps per measured run.",
    )
    parser.add_argument(
        "--runs", type=int, default=5, help="Measured runs per context length."
    )
    parser.add_argument(
        "--warmup-runs", type=int, default=1, help="Warmup runs per context length."
    )
    parser.add_argument(
        "--prompt-source",
        default="",
        help="Optional prompt text or a path to a text file. If omitted, a built-in prompt seed is used.",
    )
    parser.add_argument(
        "--max-context",
        type=int,
        default=32768,
        help="Maximum allowed context length for this sweep.",
    )
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def mib_from_bytes(value: float | int | None) -> float | None:
    if value is None:
        return None
    return float(value) / (1024**2)


def rss_bytes() -> int:
    status_path = Path("/proc/self/status")
    if status_path.exists():
        for line in status_path.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines():
            if line.startswith("VmRSS:"):
                parts = line.split()
                if len(parts) >= 2:
                    return int(parts[1]) * 1024
    return 0


def peak_rss_bytes() -> int:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return int(peak)
    return int(peak) * 1024


def snapshot_memory() -> dict[str, int]:
    return {
        "rss_bytes": rss_bytes(),
        "peak_rss_bytes": peak_rss_bytes(),
    }


def delta_bytes(after: int | None, before: int | None) -> int | None:
    if after is None or before is None:
        return None
    return int(after - before)


def summarize(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "std": None,
        }
    return {
        "mean": float(statistics.mean(values)),
        "median": float(statistics.median(values)),
        "min": float(min(values)),
        "max": float(max(values)),
        "std": float(statistics.pstdev(values)) if len(values) > 1 else 0.0,
    }


def average_int(values: list[int]) -> int | None:
    if not values:
        return None
    return int(round(sum(values) / len(values)))


def sync_device(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def select_device(requested: str) -> tuple[torch.device, list[str]]:
    normalized = requested.strip().lower() or "auto"
    notes: list[str] = []

    if normalized == "auto":
        if torch.cuda.is_available():
            notes.append("CUDA is available, so the PyTorch baseline will run on GPU.")
            return torch.device("cuda"), notes
        notes.append("CUDA is not available, so the PyTorch baseline will run on CPU.")
        return torch.device("cpu"), notes

    if normalized.startswith("cuda"):
        if torch.cuda.is_available():
            return torch.device(normalized), notes
        notes.append(
            "Requested CUDA, but no GPU is available. Falling back to CPU for the PyTorch baseline."
        )
        return torch.device("cpu"), notes

    if normalized == "cpu":
        return torch.device("cpu"), notes

    if normalized == "mps":
        mps_backend = getattr(torch.backends, "mps", None)
        if mps_backend is not None and torch.backends.mps.is_available():
            return torch.device("mps"), notes
        notes.append(
            "Requested MPS, but it is unavailable. Falling back to CPU for the PyTorch baseline."
        )
        return torch.device("cpu"), notes

    raise ValueError(f"Unsupported device request: {requested}")


def select_dtype(requested: str, device: torch.device) -> tuple[torch.dtype, str]:
    dtype_map: dict[str, Any] = {
        "float32": torch.float32,
        "float": torch.float32,
        "fp32": torch.float32,
        "float16": torch.float16,
        "half": torch.float16,
        "fp16": torch.float16,
        "bfloat16": torch.bfloat16,
        "bf16": torch.bfloat16,
    }
    normalized = requested.strip().lower() or "auto"
    if normalized == "auto":
        if device.type == "cuda":
            return torch.float16, "auto selected float16 for CUDA"
        return torch.float32, "auto selected float32 for CPU"
    if normalized not in dtype_map:
        raise ValueError(f"Unsupported dtype request: {requested}")
    return dtype_map[normalized], f"user selected {normalized}"


def resolve_prompt_text(prompt_source: str) -> tuple[str, str]:
    if not prompt_source:
        return DEFAULT_PROMPT_TEXT, "builtin"

    source_path = Path(prompt_source)
    if source_path.exists() and source_path.is_file():
        return source_path.read_text(encoding="utf-8"), "file"

    return prompt_source, "literal"


def load_seed_token_ids(
    tokenizer: Any, prompt_source: str
) -> tuple[list[int], dict[str, Any]]:
    prompt_text, prompt_kind = resolve_prompt_text(prompt_source)
    token_ids = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
    if not token_ids:
        fallback_token_id = tokenizer.eos_token_id
        if fallback_token_id is None:
            fallback_token_id = tokenizer.bos_token_id
        if fallback_token_id is None:
            raise ValueError(
                "Tokenizer did not yield any tokens and does not expose eos_token_id or bos_token_id."
            )
        token_ids = [int(fallback_token_id)]

    metadata = {
        "prompt_kind": prompt_kind,
        "prompt_preview": prompt_text[:160],
        "seed_token_count": len(token_ids),
    }
    return [int(token_id) for token_id in token_ids], metadata


def build_prompt_tensors(
    seed_token_ids: list[int], context_length: int, device: torch.device
) -> tuple[torch.Tensor, torch.Tensor]:
    repeats = math.ceil(context_length / len(seed_token_ids))
    prompt_ids = (seed_token_ids * repeats)[:context_length]
    input_ids = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    attention_mask = torch.ones((1, context_length), dtype=torch.long, device=device)
    return input_ids, attention_mask


def build_forward_kwargs(
    forward_params: set[str],
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    past_key_values: Any,
    cache_position_start: int,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "use_cache": True,
        "return_dict": True,
    }
    if "past_key_values" in forward_params and past_key_values is not None:
        kwargs["past_key_values"] = past_key_values
    if "position_ids" in forward_params:
        position_ids = attention_mask.cumsum(dim=-1) - 1
        position_ids = position_ids.masked_fill(attention_mask == 0, 0)
        kwargs["position_ids"] = position_ids[:, -input_ids.shape[1] :]
    if "cache_position" in forward_params:
        kwargs["cache_position"] = torch.arange(
            cache_position_start,
            cache_position_start + input_ids.shape[1],
            device=input_ids.device,
            dtype=torch.long,
        )
    return kwargs


def run_single_measurement(
    model: Any,
    forward_params: set[str],
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    decode_tokens: int,
    device: torch.device,
) -> dict[str, Any]:
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()

    before_prefill = snapshot_memory()

    sync_device(device)
    prefill_start = time.perf_counter()
    with torch.inference_mode():
        prefill_outputs = model(
            **build_forward_kwargs(
                forward_params=forward_params,
                input_ids=input_ids,
                attention_mask=attention_mask,
                past_key_values=None,
                cache_position_start=0,
            )
        )
    sync_device(device)
    prefill_end = time.perf_counter()
    after_prefill = snapshot_memory()

    decode_step_ms: list[float] = []
    past_key_values = getattr(prefill_outputs, "past_key_values", None)
    next_input_ids = prefill_outputs.logits[:, -1:, :].argmax(dim=-1)
    decode_attention_mask = attention_mask

    for step in range(decode_tokens):
        decode_attention_mask = torch.cat(
            [
                decode_attention_mask,
                torch.ones((1, 1), dtype=decode_attention_mask.dtype, device=device),
            ],
            dim=1,
        )
        sync_device(device)
        step_start = time.perf_counter()
        with torch.inference_mode():
            decode_outputs = model(
                **build_forward_kwargs(
                    forward_params=forward_params,
                    input_ids=next_input_ids,
                    attention_mask=decode_attention_mask,
                    past_key_values=past_key_values,
                    cache_position_start=input_ids.shape[1] + step,
                )
            )
        sync_device(device)
        step_end = time.perf_counter()
        decode_step_ms.append((step_end - step_start) * 1000.0)
        past_key_values = getattr(decode_outputs, "past_key_values", None)
        next_input_ids = decode_outputs.logits[:, -1:, :].argmax(dim=-1)

    after_decode = snapshot_memory()

    return {
        "prefill_ms": (prefill_end - prefill_start) * 1000.0,
        "decode_step_ms": decode_step_ms,
        "decode_total_ms": float(sum(decode_step_ms)),
        "memory": {
            "before_prefill": before_prefill,
            "after_prefill": after_prefill,
            "after_decode": after_decode,
        },
        "past_key_values_type": type(past_key_values).__name__
        if past_key_values is not None
        else None,
    }


def render_latency_plot(latency_frame: pd.DataFrame, figure_path: Path) -> None:
    plt.figure(figsize=(8, 4.5))
    plt.plot(
        latency_frame["context_length"],
        latency_frame["decode_ms_per_token_mean"],
        marker="o",
        label="Decode mean (ms/token)",
    )
    plt.fill_between(
        latency_frame["context_length"],
        latency_frame["decode_ms_per_token_min"],
        latency_frame["decode_ms_per_token_max"],
        alpha=0.15,
        label="Decode min-max",
    )
    plt.xlabel("Context Length")
    plt.ylabel("Latency (ms/token)")
    plt.title("PyTorch Baseline Decode Latency by Context Length")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figure_path, dpi=160)
    plt.close()


def render_memory_plot(memory_frame: pd.DataFrame, figure_path: Path) -> None:
    plt.figure(figsize=(8, 4.5))
    plt.plot(
        memory_frame["context_length"],
        memory_frame["prefill_rss_delta_mib_mean"],
        marker="o",
        label="Prefill RSS delta (MiB)",
    )
    plt.plot(
        memory_frame["context_length"],
        memory_frame["decode_rss_delta_mib_mean"],
        marker="s",
        label="Decode RSS delta (MiB)",
    )
    plt.plot(
        memory_frame["context_length"],
        memory_frame["peak_rss_mib_max"],
        marker="^",
        label="Peak RSS (MiB)",
    )
    plt.xlabel("Context Length")
    plt.ylabel("Memory (MiB)")
    plt.title("PyTorch Baseline RSS by Context Length")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figure_path, dpi=160)
    plt.close()


def add_memory_mib_columns(memory_frame: pd.DataFrame) -> pd.DataFrame:
    for column in [
        "rss_before_load_bytes",
        "rss_after_load_bytes",
        "model_load_rss_delta_bytes",
        "rss_before_prefill_bytes_mean",
        "rss_after_prefill_bytes_mean",
        "rss_after_decode_bytes_mean",
        "prefill_rss_delta_bytes_mean",
        "decode_rss_delta_bytes_mean",
        "total_rss_delta_bytes_mean",
        "peak_rss_bytes_max",
    ]:
        memory_frame[column.replace("_bytes", "_mib")] = memory_frame[column].apply(
            mib_from_bytes
        )
    return memory_frame


def validate_context_lengths(context_lengths: list[int], max_context: int) -> None:
    if not context_lengths:
        raise ValueError("At least one context length is required.")
    if max_context <= 0:
        raise ValueError("--max-context must be positive.")
    invalid = [length for length in context_lengths if length <= 0]
    if invalid:
        raise ValueError(f"Context lengths must be positive integers: {invalid}")
    oversized = [length for length in context_lengths if length > max_context]
    if oversized:
        raise ValueError(
            f"Requested context lengths exceed --max-context={max_context}: {oversized}"
        )


def write_status(status_path: Path, payload: dict[str, Any]) -> None:
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def import_runtime_dependencies() -> None:
    global plt, pd, torch, AutoModelForCausalLM, AutoTokenizer

    import matplotlib.pyplot as imported_plt
    import pandas as imported_pd
    import torch as imported_torch
    from transformers import AutoModelForCausalLM as imported_auto_model
    from transformers import AutoTokenizer as imported_auto_tokenizer

    plt = imported_plt
    pd = imported_pd
    torch = imported_torch
    AutoModelForCausalLM = imported_auto_model
    AutoTokenizer = imported_auto_tokenizer


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    raw_dir = args.out_dir / "raw"
    tables_dir = args.out_dir / "tables"
    paper_tables_dir = repo_root / "paper_assets" / "tables"
    paper_figures_dir = repo_root / "paper_assets" / "figures"

    raw_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    paper_tables_dir.mkdir(parents=True, exist_ok=True)
    paper_figures_dir.mkdir(parents=True, exist_ok=True)

    status_path = raw_dir / "torch_context_sweep_status.json"
    raw_json_path = raw_dir / "torch_context_sweep_raw.json"
    latency_csv_path = tables_dir / "torch_decode_latency_by_context.csv"
    memory_csv_path = tables_dir / "torch_memory_by_context.csv"
    paper_latency_csv_path = paper_tables_dir / "torch_decode_latency_by_context.csv"
    paper_memory_csv_path = paper_tables_dir / "torch_memory_by_context.csv"
    paper_latency_figure_path = (
        paper_figures_dir / "torch_decode_latency_by_context.png"
    )
    paper_memory_figure_path = paper_figures_dir / "torch_memory_by_context.png"

    status_payload: dict[str, Any] = {
        "status": "running",
        "baseline_type": "pytorch",
        "is_onnx_runtime_profile": False,
        "message": "PyTorch host-side context sweep baseline in progress.",
        "started_at": now_iso(),
        "model_dir": str(args.model_dir.resolve()),
        "out_dir": str(args.out_dir.resolve()),
        "requested_device": args.device,
        "requested_dtype": args.dtype,
        "context_lengths": args.context_lengths,
        "decode_tokens": args.decode_tokens,
        "runs": args.runs,
        "warmup_runs": args.warmup_runs,
        "max_context": args.max_context,
        "outputs": {
            "raw_json": str(raw_json_path.resolve()),
            "status_json": str(status_path.resolve()),
            "latency_csv": str(latency_csv_path.resolve()),
            "memory_csv": str(memory_csv_path.resolve()),
            "paper_latency_csv": str(paper_latency_csv_path.resolve()),
            "paper_memory_csv": str(paper_memory_csv_path.resolve()),
            "paper_latency_figure": str(paper_latency_figure_path.resolve()),
            "paper_memory_figure": str(paper_memory_figure_path.resolve()),
        },
    }
    write_status(status_path, status_payload)

    try:
        validate_context_lengths(args.context_lengths, args.max_context)
        if args.runs <= 0:
            raise ValueError("--runs must be positive.")
        if args.warmup_runs < 0:
            raise ValueError("--warmup-runs cannot be negative.")
        if args.decode_tokens <= 0:
            raise ValueError("--decode-tokens must be positive.")
        if not args.model_dir.exists():
            raise FileNotFoundError(
                f"Model directory does not exist: {args.model_dir}\n"
                "Point --model-dir to a local Gemma 3 1B safetensors directory."
            )
        if not args.model_dir.is_dir():
            raise NotADirectoryError(
                f"Model directory is not a directory: {args.model_dir}"
            )

        import_runtime_dependencies()

        rss_before_load = rss_bytes()
        device, device_notes = select_device(args.device)
        dtype, dtype_note = select_dtype(args.dtype, device)

        tokenizer_start = time.perf_counter()
        tokenizer = AutoTokenizer.from_pretrained(args.model_dir, local_files_only=True)
        tokenizer_end = time.perf_counter()

        model_start = time.perf_counter()
        model = AutoModelForCausalLM.from_pretrained(
            args.model_dir,
            torch_dtype=dtype,
            local_files_only=True,
        )
        model.to(device)
        model.eval()
        sync_device(device)
        model_end = time.perf_counter()
        rss_after_load = rss_bytes()

        config_max_context = getattr(model.config, "max_position_embeddings", None)
        if isinstance(config_max_context, int):
            too_long = [
                length for length in args.context_lengths if length > config_max_context
            ]
            if too_long:
                raise ValueError(
                    "Requested context lengths exceed model.config.max_position_embeddings="
                    f"{config_max_context}: {too_long}"
                )

        seed_token_ids, prompt_metadata = load_seed_token_ids(
            tokenizer, args.prompt_source
        )
        forward_params = set(inspect.signature(model.forward).parameters)

        context_summaries: list[dict[str, Any]] = []
        latency_rows: list[dict[str, Any]] = []
        memory_rows: list[dict[str, Any]] = []

        ordered_context_lengths = list(args.context_lengths)
        for context_length in ordered_context_lengths:
            input_ids, attention_mask = build_prompt_tensors(
                seed_token_ids, context_length, device
            )
            runs_payload: list[dict[str, Any]] = []

            for _ in range(args.warmup_runs):
                run_single_measurement(
                    model=model,
                    forward_params=forward_params,
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    decode_tokens=args.decode_tokens,
                    device=device,
                )

            prefill_ms_values: list[float] = []
            decode_total_ms_values: list[float] = []
            decode_step_ms_values: list[float] = []
            before_prefill_values: list[int] = []
            after_prefill_values: list[int] = []
            after_decode_values: list[int] = []
            prefill_delta_values: list[int] = []
            decode_delta_values: list[int] = []
            total_delta_values: list[int] = []
            peak_rss_values: list[int] = []
            past_key_values_types: set[str] = set()

            for run_index in range(args.runs):
                measurement = run_single_measurement(
                    model=model,
                    forward_params=forward_params,
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    decode_tokens=args.decode_tokens,
                    device=device,
                )
                prefill_ms_values.append(measurement["prefill_ms"])
                decode_total_ms_values.append(measurement["decode_total_ms"])
                decode_step_ms_values.extend(measurement["decode_step_ms"])

                before_prefill_rss = measurement["memory"]["before_prefill"][
                    "rss_bytes"
                ]
                after_prefill_rss = measurement["memory"]["after_prefill"]["rss_bytes"]
                after_decode_rss = measurement["memory"]["after_decode"]["rss_bytes"]
                before_prefill_values.append(before_prefill_rss)
                after_prefill_values.append(after_prefill_rss)
                after_decode_values.append(after_decode_rss)
                prefill_delta_values.append(
                    delta_bytes(after_prefill_rss, before_prefill_rss) or 0
                )
                decode_delta_values.append(
                    delta_bytes(after_decode_rss, after_prefill_rss) or 0
                )
                total_delta_values.append(
                    delta_bytes(after_decode_rss, before_prefill_rss) or 0
                )
                peak_rss_values.append(
                    measurement["memory"]["after_decode"]["peak_rss_bytes"]
                )

                if measurement["past_key_values_type"] is not None:
                    past_key_values_types.add(measurement["past_key_values_type"])

                runs_payload.append(
                    {
                        "run_index": run_index,
                        "prefill_ms": measurement["prefill_ms"],
                        "decode_total_ms": measurement["decode_total_ms"],
                        "decode_step_ms": measurement["decode_step_ms"],
                        "memory": measurement["memory"],
                        "past_key_values_type": measurement["past_key_values_type"],
                    }
                )

            prefill_stats = summarize(prefill_ms_values)
            decode_total_stats = summarize(decode_total_ms_values)
            decode_step_stats = summarize(decode_step_ms_values)

            latency_rows.append(
                {
                    "baseline": "PyTorch host-side baseline",
                    "context_length": context_length,
                    "decode_tokens": args.decode_tokens,
                    "runs": args.runs,
                    "warmup_runs": args.warmup_runs,
                    "device": str(device),
                    "dtype": str(dtype).replace("torch.", ""),
                    "model_load_ms": (model_end - model_start) * 1000.0,
                    "tokenizer_load_ms": (tokenizer_end - tokenizer_start) * 1000.0,
                    "prefill_ms_mean": prefill_stats["mean"],
                    "prefill_ms_median": prefill_stats["median"],
                    "prefill_ms_min": prefill_stats["min"],
                    "prefill_ms_max": prefill_stats["max"],
                    "prefill_ms_std": prefill_stats["std"],
                    "decode_total_ms_mean": decode_total_stats["mean"],
                    "decode_total_ms_median": decode_total_stats["median"],
                    "decode_total_ms_min": decode_total_stats["min"],
                    "decode_total_ms_max": decode_total_stats["max"],
                    "decode_total_ms_std": decode_total_stats["std"],
                    "decode_ms_per_token_mean": decode_step_stats["mean"],
                    "decode_ms_per_token_median": decode_step_stats["median"],
                    "decode_ms_per_token_min": decode_step_stats["min"],
                    "decode_ms_per_token_max": decode_step_stats["max"],
                    "decode_ms_per_token_std": decode_step_stats["std"],
                    "past_key_values_types": ";".join(sorted(past_key_values_types)),
                    "raw_json": str(raw_json_path.resolve()),
                }
            )

            memory_rows.append(
                {
                    "baseline": "PyTorch host-side baseline",
                    "context_length": context_length,
                    "decode_tokens": args.decode_tokens,
                    "runs": args.runs,
                    "device": str(device),
                    "dtype": str(dtype).replace("torch.", ""),
                    "rss_before_load_bytes": rss_before_load,
                    "rss_after_load_bytes": rss_after_load,
                    "model_load_rss_delta_bytes": delta_bytes(
                        rss_after_load, rss_before_load
                    ),
                    "rss_before_prefill_bytes_mean": average_int(before_prefill_values),
                    "rss_after_prefill_bytes_mean": average_int(after_prefill_values),
                    "rss_after_decode_bytes_mean": average_int(after_decode_values),
                    "prefill_rss_delta_bytes_mean": average_int(prefill_delta_values),
                    "decode_rss_delta_bytes_mean": average_int(decode_delta_values),
                    "total_rss_delta_bytes_mean": average_int(total_delta_values),
                    "peak_rss_bytes_max": max(peak_rss_values)
                    if peak_rss_values
                    else None,
                    "raw_json": str(raw_json_path.resolve()),
                }
            )

            context_summaries.append(
                {
                    "context_length": context_length,
                    "runs": runs_payload,
                    "prefill_ms_stats": prefill_stats,
                    "decode_total_ms_stats": decode_total_stats,
                    "decode_ms_per_token_stats": decode_step_stats,
                    "memory_summary": {
                        "rss_before_prefill_bytes_mean": average_int(
                            before_prefill_values
                        ),
                        "rss_after_prefill_bytes_mean": average_int(
                            after_prefill_values
                        ),
                        "rss_after_decode_bytes_mean": average_int(after_decode_values),
                        "prefill_rss_delta_bytes_mean": average_int(
                            prefill_delta_values
                        ),
                        "decode_rss_delta_bytes_mean": average_int(decode_delta_values),
                        "total_rss_delta_bytes_mean": average_int(total_delta_values),
                        "peak_rss_bytes_max": max(peak_rss_values)
                        if peak_rss_values
                        else None,
                    },
                }
            )

            del input_ids
            del attention_mask
            gc.collect()
            if device.type == "cuda":
                torch.cuda.empty_cache()

        latency_frame = pd.DataFrame(latency_rows)
        memory_frame = add_memory_mib_columns(pd.DataFrame(memory_rows))

        latency_frame.to_csv(latency_csv_path, index=False)
        memory_frame.to_csv(memory_csv_path, index=False)
        latency_frame.to_csv(paper_latency_csv_path, index=False)
        memory_frame.to_csv(paper_memory_csv_path, index=False)
        render_latency_plot(latency_frame, paper_latency_figure_path)
        render_memory_plot(memory_frame, paper_memory_figure_path)

        raw_payload = {
            "baseline_type": "pytorch",
            "is_onnx_runtime_profile": False,
            "interpretation_limit": (
                "PyTorch context sweep is not ONNX Runtime profiling. "
                "It is a host-side baseline for observing Gemma 3 1B decode and KV-cache pressure."
            ),
            "started_at": status_payload["started_at"],
            "finished_at": now_iso(),
            "requested_device": args.device,
            "resolved_device": str(device),
            "requested_dtype": args.dtype,
            "resolved_dtype": str(dtype).replace("torch.", ""),
            "device_notes": device_notes,
            "dtype_note": dtype_note,
            "model_dir": str(args.model_dir.resolve()),
            "model_type": getattr(model.config, "model_type", None),
            "tokenizer_class": tokenizer.__class__.__name__,
            "model_class": model.__class__.__name__,
            "model_config_max_position_embeddings": config_max_context,
            "tokenizer_load_ms": (tokenizer_end - tokenizer_start) * 1000.0,
            "model_load_ms": (model_end - model_start) * 1000.0,
            "rss_before_load_bytes": rss_before_load,
            "rss_after_load_bytes": rss_after_load,
            "model_load_rss_delta_bytes": delta_bytes(rss_after_load, rss_before_load),
            "prompt_metadata": prompt_metadata,
            "decode_tokens": args.decode_tokens,
            "runs": args.runs,
            "warmup_runs": args.warmup_runs,
            "contexts": context_summaries,
        }
        raw_json_path.write_text(json.dumps(raw_payload, indent=2), encoding="utf-8")

        status_payload.update(
            {
                "status": "success",
                "message": (
                    "PyTorch host-side context sweep baseline completed successfully. "
                    "These outputs are not ONNX Runtime profiling results."
                ),
                "finished_at": now_iso(),
                "resolved_device": str(device),
                "resolved_dtype": str(dtype).replace("torch.", ""),
                "device_notes": device_notes,
                "dtype_note": dtype_note,
                "model_load_ms": (model_end - model_start) * 1000.0,
                "tokenizer_load_ms": (tokenizer_end - tokenizer_start) * 1000.0,
            }
        )
        write_status(status_path, status_payload)

        print("PyTorch host-side baseline completed.")
        print(latency_frame.to_string(index=False))
        print()
        print(memory_frame.to_string(index=False))
        print(f"\nSaved latency CSV: {latency_csv_path.resolve()}")
        print(f"Saved memory CSV: {memory_csv_path.resolve()}")
        print(f"Saved raw JSON: {raw_json_path.resolve()}")
        print(f"Saved status JSON: {status_path.resolve()}")
        print(f"Saved latency figure: {paper_latency_figure_path.resolve()}")
        print(f"Saved memory figure: {paper_memory_figure_path.resolve()}")
    except Exception as exc:
        status_payload.update(
            {
                "status": "failed",
                "message": (
                    "PyTorch host-side context sweep baseline failed before producing complete results. "
                    "This status is not an ONNX Runtime profiling result."
                ),
                "finished_at": now_iso(),
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
        write_status(status_path, status_payload)
        print(status_payload["message"], file=sys.stderr)
        print(f"Saved failure status: {status_path.resolve()}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
