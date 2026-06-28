#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort


TOKEN_INPUT_NAMES = {"input_ids", "attention_mask", "position_ids", "token_type_ids"}
CACHE_CONTROL_NAMES = {"use_cache_branch", "use_cache", "cache_position", "past_sequence_length"}
CACHE_INPUT_KEYWORDS = ("past_key_values", "past_key_value", "past_key", "past_value", "cache")
CACHE_OUTPUT_KEYWORDS = ("present", "past_key_values", "past_key_value", "key_values", "cache")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ONNX Runtime profiling scaffold for Gemma 3 1B host-side analysis.")
    parser.add_argument("--model", type=Path, help="Path to an exported ONNX model.")
    parser.add_argument("--provider", default="CPUExecutionProvider", help="ONNX Runtime execution provider.")
    parser.add_argument("--prompt-len", type=int, default=128, help="Synthetic prompt length.")
    parser.add_argument("--decode-tokens", type=int, default=16, help="Number of decode iterations to attempt.")
    parser.add_argument("--profile", action="store_true", help="Enable ONNX Runtime profiling output.")
    parser.add_argument("--out-dir", type=Path, required=True, help="Directory for JSON outputs.")
    return parser.parse_args()


def model_exists(model_path: Path | None) -> Path:
    if model_path is None:
        raise FileNotFoundError(
            "An ONNX-exported Gemma 3 1B model path is required. "
            "Pass --model /absolute/path/to/model.onnx."
        )
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model path does not exist: {model_path}\n"
            "An ONNX-exported Gemma 3 1B model path is required for profiling."
        )
    return model_path


def shape_to_list(shape: list[Any]) -> list[Any]:
    return [dim if isinstance(dim, (int, str)) else str(dim) for dim in shape]


def describe_session(session: ort.InferenceSession) -> dict[str, Any]:
    return {
        "inputs": [
            {
                "name": meta.name,
                "type": meta.type,
                "shape": shape_to_list(meta.shape),
            }
            for meta in session.get_inputs()
        ],
        "outputs": [
            {
                "name": meta.name,
                "type": meta.type,
                "shape": shape_to_list(meta.shape),
            }
            for meta in session.get_outputs()
        ],
        "providers": session.get_providers(),
    }


def dtype_from_meta(meta_type: str) -> np.dtype[Any]:
    mapping = {
        "tensor(float16)": np.float16,
        "tensor(float)": np.float32,
        "tensor(float32)": np.float32,
        "tensor(double)": np.float64,
        "tensor(int32)": np.int32,
        "tensor(int64)": np.int64,
        "tensor(bool)": np.bool_,
    }
    if meta_type not in mapping:
        raise NotImplementedError(f"Unsupported tensor type: {meta_type}")
    return mapping[meta_type]


def is_dynamic_dim(dim: Any) -> bool:
    return isinstance(dim, str) or dim is None or (isinstance(dim, int) and dim <= 0)


def rss_bytes() -> int | None:
    status_path = Path("/proc/self/status")
    if not status_path.exists():
        return None
    for line in status_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("VmRSS:"):
            parts = line.split()
            if len(parts) >= 2:
                return int(parts[1]) * 1024
    return None


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = (len(sorted_values) - 1) * q
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return sorted_values[low]
    weight = index - low
    return sorted_values[low] * (1.0 - weight) + sorted_values[high] * weight


def is_cache_input(meta: Any) -> bool:
    lowered = meta.name.lower()
    return lowered not in TOKEN_INPUT_NAMES and any(keyword in lowered for keyword in CACHE_INPUT_KEYWORDS)


def is_cache_output(meta: Any) -> bool:
    lowered = meta.name.lower()
    return any(keyword in lowered for keyword in CACHE_OUTPUT_KEYWORDS)


def classify_session_io(session: ort.InferenceSession) -> dict[str, Any]:
    token_inputs: list[Any] = []
    control_inputs: list[Any] = []
    cache_inputs: list[Any] = []
    unsupported_inputs: list[Any] = []

    for meta in session.get_inputs():
        lowered = meta.name.lower()
        if lowered in TOKEN_INPUT_NAMES:
            token_inputs.append(meta)
        elif lowered in CACHE_CONTROL_NAMES:
            control_inputs.append(meta)
        elif is_cache_input(meta):
            cache_inputs.append(meta)
        else:
            unsupported_inputs.append(meta)

    cache_output_indices: list[int] = []
    cache_outputs: list[Any] = []
    for idx, meta in enumerate(session.get_outputs()):
        if is_cache_output(meta):
            cache_output_indices.append(idx)
            cache_outputs.append(meta)

    return {
        "token_inputs": token_inputs,
        "control_inputs": control_inputs,
        "cache_inputs": cache_inputs,
        "cache_outputs": cache_outputs,
        "cache_output_indices": cache_output_indices,
        "unsupported_inputs": unsupported_inputs,
    }


def infer_cache_sequence_axis(shape: list[Any]) -> int:
    rank = len(shape)
    candidate_indices = list(range(1, max(rank - 1, 1)))
    for idx in candidate_indices:
        if idx < rank and is_dynamic_dim(shape[idx]):
            return idx
    if rank >= 4:
        return 2
    if rank >= 3:
        return 1
    return rank - 1


def zero_cache_tensor(meta: Any) -> np.ndarray:
    dtype = dtype_from_meta(meta.type)
    shape = list(meta.shape)
    if not shape:
        raise NotImplementedError(f"Cache tensor must have rank >= 1: {meta.name}")

    seq_axis = infer_cache_sequence_axis(shape)
    concrete_shape: list[int] = []
    for idx, dim in enumerate(shape):
        if idx == seq_axis:
            concrete_shape.append(0)
        elif idx == 0:
            concrete_shape.append(1 if is_dynamic_dim(dim) else int(dim))
        elif is_dynamic_dim(dim):
            concrete_shape.append(1)
        else:
            concrete_shape.append(int(dim))
    return np.zeros(concrete_shape, dtype=dtype)


def build_prefill_inputs(session: ort.InferenceSession, prompt_len: int, io_info: dict[str, Any]) -> dict[str, np.ndarray]:
    inputs: dict[str, np.ndarray] = {}

    for meta in io_info["unsupported_inputs"]:
        raise NotImplementedError(
            "This scaffold currently auto-drives only common token inputs, common cache-control "
            f"inputs, and cache tensors. Unsupported required input: {meta.name}"
        )

    for meta in io_info["token_inputs"]:
        name = meta.name
        lowered = name.lower()
        dtype = dtype_from_meta(meta.type)

        if lowered == "input_ids":
            inputs[name] = (np.arange(prompt_len, dtype=dtype).reshape(1, prompt_len) % 251).astype(dtype)
        elif lowered == "attention_mask":
            inputs[name] = np.ones((1, prompt_len), dtype=dtype)
        elif lowered == "position_ids":
            inputs[name] = np.arange(prompt_len, dtype=dtype).reshape(1, prompt_len)
        elif lowered == "token_type_ids":
            inputs[name] = np.zeros((1, prompt_len), dtype=dtype)

    for meta in io_info["control_inputs"]:
        lowered = meta.name.lower()
        dtype = dtype_from_meta(meta.type)

        if lowered in {"use_cache_branch", "use_cache"}:
            scalar = np.array(False if np.issubdtype(dtype, np.bool_) else 0, dtype=dtype)
            inputs[meta.name] = scalar.reshape(()) if scalar.ndim == 0 else scalar
        elif lowered == "cache_position":
            inputs[meta.name] = np.arange(prompt_len, dtype=dtype)
        elif lowered == "past_sequence_length":
            inputs[meta.name] = np.array(0, dtype=dtype)

    for meta in io_info["cache_inputs"]:
        inputs[meta.name] = zero_cache_tensor(meta)

    return inputs


def build_decode_inputs(
    session: ort.InferenceSession,
    prefill_inputs: dict[str, np.ndarray],
    io_info: dict[str, Any],
    prompt_len: int,
    step: int,
    cache_tensors: dict[str, np.ndarray],
    cache_enabled: bool,
) -> dict[str, np.ndarray]:
    decode_inputs: dict[str, np.ndarray] = {}
    current_position = prompt_len + step
    current_context_len = prompt_len + step + 1

    for meta in io_info["token_inputs"]:
        lowered = meta.name.lower()
        dtype = dtype_from_meta(meta.type)

        if lowered == "input_ids":
            decode_inputs[meta.name] = np.array([[step % 251]], dtype=dtype)
        elif lowered == "attention_mask":
            if cache_enabled:
                decode_inputs[meta.name] = np.ones((1, current_context_len), dtype=dtype)
            else:
                decode_inputs[meta.name] = np.ones((1, 1), dtype=dtype)
        elif lowered == "position_ids":
            if cache_enabled:
                decode_inputs[meta.name] = np.array([[current_position]], dtype=dtype)
            else:
                decode_inputs[meta.name] = np.array([[step]], dtype=dtype)
        elif lowered == "token_type_ids":
            decode_inputs[meta.name] = np.zeros((1, 1), dtype=dtype)

    for meta in io_info["control_inputs"]:
        lowered = meta.name.lower()
        dtype = dtype_from_meta(meta.type)

        if lowered in {"use_cache_branch", "use_cache"}:
            scalar = np.array(True if np.issubdtype(dtype, np.bool_) else 1, dtype=dtype)
            decode_inputs[meta.name] = scalar.reshape(()) if scalar.ndim == 0 else scalar
        elif lowered == "cache_position":
            decode_inputs[meta.name] = np.array([current_position], dtype=dtype)
        elif lowered == "past_sequence_length":
            decode_inputs[meta.name] = np.array(current_position, dtype=dtype)

    for meta in io_info["cache_inputs"]:
        decode_inputs[meta.name] = cache_tensors.get(meta.name, zero_cache_tensor(meta))

    if not decode_inputs:
        raise NotImplementedError(
            "No supported inputs were discovered. Adjust run_profile.py to match the exported model interface."
        )

    return decode_inputs


def map_cache_outputs(io_info: dict[str, Any], output_values: list[np.ndarray]) -> dict[str, np.ndarray]:
    cache_output_values = [output_values[idx] for idx in io_info["cache_output_indices"]]
    cache_inputs = io_info["cache_inputs"]
    if not cache_inputs or not cache_output_values:
        return {}

    if len(cache_inputs) != len(cache_output_values):
        raise NotImplementedError(
            "Cache input/output count mismatch. "
            f"inputs={len(cache_inputs)} outputs={len(cache_output_values)}"
        )

    mapped: dict[str, np.ndarray] = {}
    for input_meta, value in zip(cache_inputs, cache_output_values):
        mapped[input_meta.name] = value
    return mapped


def profile_model(
    model_path: Path,
    provider: str,
    prompt_len: int,
    decode_tokens: int,
    out_dir: Path,
    enable_profile: bool = False,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)

    session_options = ort.SessionOptions()
    if enable_profile:
        session_options.enable_profiling = True
        session_options.profile_file_prefix = str(out_dir / "ort_profile")

    rss_before_session = rss_bytes()
    t0 = time.perf_counter()
    session = ort.InferenceSession(
        str(model_path),
        sess_options=session_options,
        providers=[provider],
    )
    session_init_s = time.perf_counter() - t0
    rss_after_session = rss_bytes()

    io_info = classify_session_io(session)
    cache_enabled = bool(io_info["cache_inputs"] and io_info["cache_outputs"])

    summary: dict[str, Any] = {
        "model": str(model_path),
        "provider": provider,
        "prompt_len": prompt_len,
        "decode_tokens": decode_tokens,
        "session_init_s": session_init_s,
        "prefill_s": None,
        "decode_step_s": [],
        "decode_avg_s": None,
        "decode_p50_s": None,
        "decode_p95_s": None,
        "profiling_json": None,
        "session_description": describe_session(session),
        "decode_mode": "with_past_kv_cache" if cache_enabled else "single_token_without_cache_feedback",
        "cache_io": {
            "cache_input_names": [meta.name for meta in io_info["cache_inputs"]],
            "cache_output_names": [meta.name for meta in io_info["cache_outputs"]],
            "cache_pair_count": min(len(io_info["cache_inputs"]), len(io_info["cache_outputs"])),
        },
        "rss_bytes": {
            "before_session": rss_before_session,
            "after_session": rss_after_session,
            "before_prefill": None,
            "after_prefill": None,
            "after_each_decode": [],
            "after_decode": None,
        },
    }

    try:
        prefill_inputs = build_prefill_inputs(session, prompt_len, io_info)

        summary["rss_bytes"]["before_prefill"] = rss_bytes()
        t1 = time.perf_counter()
        prefill_outputs = session.run(None, prefill_inputs)
        summary["prefill_s"] = time.perf_counter() - t1
        summary["rss_bytes"]["after_prefill"] = rss_bytes()

        cache_tensors = map_cache_outputs(io_info, prefill_outputs)

        for step in range(decode_tokens):
            decode_inputs = build_decode_inputs(
                session=session,
                prefill_inputs=prefill_inputs,
                io_info=io_info,
                prompt_len=prompt_len,
                step=step,
                cache_tensors=cache_tensors,
                cache_enabled=cache_enabled,
            )
            step_t0 = time.perf_counter()
            decode_outputs = session.run(None, decode_inputs)
            summary["decode_step_s"].append(time.perf_counter() - step_t0)
            summary["rss_bytes"]["after_each_decode"].append(rss_bytes())
            if cache_enabled:
                cache_tensors = map_cache_outputs(io_info, decode_outputs)

        summary["rss_bytes"]["after_decode"] = (
            summary["rss_bytes"]["after_each_decode"][-1]
            if summary["rss_bytes"]["after_each_decode"]
            else summary["rss_bytes"]["after_prefill"]
        )

    except NotImplementedError as exc:
        summary["note"] = (
            "Session creation succeeded, but automated prefill/decode execution needs "
            f"model-specific input mapping: {exc}"
        )

    if summary["decode_step_s"]:
        summary["decode_avg_s"] = sum(summary["decode_step_s"]) / len(summary["decode_step_s"])
        summary["decode_p50_s"] = percentile(summary["decode_step_s"], 0.50)
        summary["decode_p95_s"] = percentile(summary["decode_step_s"], 0.95)

    if enable_profile:
        summary["profiling_json"] = session.end_profiling()

    out_path = out_dir / "profile_summary.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    args = parse_args()

    try:
        model_path = model_exists(args.model)
    except FileNotFoundError as exc:
        print(exc)
        raise SystemExit(1) from exc

    summary = profile_model(
        model_path=model_path,
        provider=args.provider,
        prompt_len=args.prompt_len,
        decode_tokens=args.decode_tokens,
        out_dir=args.out_dir,
        enable_profile=args.profile,
    )

    print(json.dumps(summary, indent=2))
    print(f"\nSaved summary: {args.out_dir / 'profile_summary.json'}")


if __name__ == "__main__":
    main()
