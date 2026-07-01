#!/usr/bin/env python3
"""Run small ONNX Runtime micrograph benchmarks on an Android Python environment."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import time
from pathlib import Path


DEFAULT_INPUT_DIM = 16
DEFAULT_OUTPUT_DIM = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--kind", choices=["float_matmul", "matmulinteger"], required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--providers", default="CPUExecutionProvider")
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--input-dim", type=int, default=DEFAULT_INPUT_DIM)
    parser.add_argument("--output-dim", type=int, default=DEFAULT_OUTPUT_DIM)
    return parser.parse_args()


def clamp_int8(value: int) -> int:
    return max(-128, min(127, int(value)))


def deterministic_activation(input_dim: int) -> list[int]:
    values = []
    for idx in range(input_dim):
        raw = ((idx * 9 + 5) % 31) - 15
        adjusted = 11 if raw == 0 and (idx & 1) == 0 else -11 if raw == 0 else raw
        values.append(clamp_int8(adjusted))
    return values


def deterministic_weight(output_index: int, input_index: int) -> int:
    raw = ((output_index + 3) * (input_index + 5) + output_index * 7) % 29
    signed = raw - 14
    adjusted = signed if ((output_index + input_index) & 1) == 0 else -signed
    return clamp_int8(output_index - input_index if adjusted == 0 else adjusted)


def deterministic_weights(input_dim: int, output_dim: int) -> list[list[int]]:
    return [
        [deterministic_weight(row, col) for col in range(input_dim)]
        for row in range(output_dim)
    ]


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * (pct / 100.0)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def latency_summary(values: list[float]) -> dict[str, float]:
    if not values:
        return {"mean": math.nan, "p50": math.nan, "p95": math.nan, "min": math.nan, "max": math.nan}
    return {
        "mean": statistics.fmean(values),
        "p50": percentile(values, 50.0),
        "p95": percentile(values, 95.0),
        "min": min(values),
        "max": max(values),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def skipped(out_dir: Path, reason: str, args: argparse.Namespace, extra: dict[str, object] | None = None) -> None:
    payload = {
        "status": "skipped",
        "reason": reason,
        "model": args.model,
        "kind": args.kind,
        "providers_requested": args.providers,
        "runs": args.runs,
        "warmup": args.warmup,
        "claim_boundary": "No ONNX Runtime latency result is reported when the Android runtime cannot execute the graph.",
    }
    if extra:
        payload.update(extra)
    write_json(out_dir / f"{args.kind}_summary.json", payload)
    print(json.dumps(payload, ensure_ascii=False))


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        import numpy as np
    except Exception as exc:
        skipped(out_dir, f"numpy import failed: {exc}", args)
        return

    try:
        import onnxruntime as ort
    except Exception as exc:
        skipped(out_dir, f"onnxruntime import failed: {exc}", args)
        return

    available_providers = list(ort.get_available_providers())
    requested = [provider.strip() for provider in args.providers.split(",") if provider.strip()]
    unavailable = [provider for provider in requested if provider not in available_providers]
    if unavailable:
        skipped(
            out_dir,
            "requested provider unavailable",
            args,
            {"available_providers": available_providers, "unavailable_providers": unavailable},
        )
        return

    activation_i8 = np.asarray(deterministic_activation(args.input_dim), dtype=np.int8)
    weights_i8 = np.asarray(deterministic_weights(args.input_dim, args.output_dim), dtype=np.int8)
    reference = weights_i8.astype(np.int32) @ activation_i8.astype(np.int32)

    if args.kind == "matmulinteger":
        feed = {
            "activation": activation_i8.reshape(1, args.input_dim),
            "weight": weights_i8.T.copy(),
        }
        expected = reference.reshape(1, args.output_dim)
        dtype = "int8_inputs_int32_output"
    else:
        feed = {
            "activation": activation_i8.astype(np.float32).reshape(1, args.input_dim),
            "weight": weights_i8.astype(np.float32).T.copy(),
        }
        expected = reference.astype(np.float32).reshape(1, args.output_dim)
        dtype = "float32"

    try:
        session = ort.InferenceSession(str(Path(args.model)), providers=requested)
    except Exception as exc:
        skipped(
            out_dir,
            f"session creation failed: {exc}",
            args,
            {"available_providers": available_providers},
        )
        return

    rows: list[dict[str, object]] = []
    latencies: list[float] = []
    all_pass = True
    for idx in range(args.warmup + args.runs):
        phase = "warmup" if idx < args.warmup else "run"
        run_idx = idx - args.warmup if phase == "run" else idx
        t0 = time.perf_counter()
        try:
            outputs = session.run(None, feed)
            error = ""
            result = outputs[0]
            correct = bool(np.array_equal(result, expected))
        except Exception as exc:
            result = None
            correct = False
            error = str(exc)
        t1 = time.perf_counter()
        latency_ms = (t1 - t0) * 1000.0
        if phase == "run":
            latencies.append(latency_ms)
            all_pass = all_pass and correct
        rows.append(
            {
                "phase": phase,
                "run": run_idx,
                "kind": args.kind,
                "providers": ",".join(requested),
                "input_dim": args.input_dim,
                "output_dim": args.output_dim,
                "macs": args.input_dim * args.output_dim,
                "dtype": dtype,
                "latency_ms": f"{latency_ms:.9f}",
                "correctness_pass": correct,
                "reference": " ".join(str(int(v)) for v in reference.reshape(-1)),
                "result": "" if result is None else " ".join(str(int(v)) for v in result.reshape(-1)),
                "error": error,
            }
        )

    write_csv(out_dir / f"{args.kind}_runs.csv", rows)
    latency = latency_summary(latencies)
    summary = {
        "status": "completed" if all_pass else "failed_correctness",
        "model": args.model,
        "kind": args.kind,
        "providers_requested": requested,
        "available_providers": available_providers,
        "input_dim": args.input_dim,
        "output_dim": args.output_dim,
        "macs": args.input_dim * args.output_dim,
        "dtype": dtype,
        "warmup": args.warmup,
        "runs": args.runs,
        "correctness_pass": all_pass,
        "latency_ms_mean": round(latency["mean"], 9),
        "latency_ms_p50": round(latency["p50"], 9),
        "latency_ms_p95": round(latency["p95"], 9),
        "latency_ms_min": round(latency["min"], 9),
        "latency_ms_max": round(latency["max"], 9),
        "claim_boundary": "Android ONNX Runtime micrograph wall-clock session.run result only; not whole-model inference.",
    }
    write_json(out_dir / f"{args.kind}_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
