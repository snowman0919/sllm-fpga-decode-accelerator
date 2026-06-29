#!/usr/bin/env python3
"""Shared helpers for the fixed Decode MatVec UART and baseline harnesses."""

from __future__ import annotations

import csv
import json
import math
import statistics
import struct
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIM = 16
DEFAULT_OUTPUT_DIM = 4
DEFAULT_BAUDRATE = 115200
MATVEC_PAYLOAD_LEN = DEFAULT_INPUT_DIM + (DEFAULT_INPUT_DIM * DEFAULT_OUTPUT_DIM)

REQ_MAGIC = b"\xA5\x5A"
RESP_MAGIC = b"\x5A\xA5"
CMD_PING = 0x01
CMD_RESET = 0x02
CMD_MATVEC = 0x10
RSP_PING_ACK = 0x81
RSP_RESET_ACK = 0x82
RSP_MATVEC_RESULT = 0x90
STATUS_OK = 0


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def resolve_log_dir(log_dir: str | None, prefix: str = "logs") -> Path:
    path = Path(log_dir) if log_dir else PROJECT_ROOT / prefix / timestamp()
    path.mkdir(parents=True, exist_ok=True)
    return path


def clamp_int8(value: int) -> int:
    return max(-128, min(127, int(value)))


def deterministic_activation(input_dim: int = DEFAULT_INPUT_DIM) -> np.ndarray:
    values = []
    for idx in range(input_dim):
        raw = ((idx * 9 + 5) % 31) - 15
        adjusted = 11 if raw == 0 and (idx & 1) == 0 else -11 if raw == 0 else raw
        values.append(clamp_int8(adjusted))
    return np.asarray(values, dtype=np.int8)


def deterministic_weight(output_index: int, input_index: int) -> int:
    raw = ((output_index + 3) * (input_index + 5) + output_index * 7) % 29
    signed = raw - 14
    adjusted = signed if ((output_index + input_index) & 1) == 0 else -signed
    return clamp_int8(output_index - input_index if adjusted == 0 else adjusted)


def deterministic_weights(
    input_dim: int = DEFAULT_INPUT_DIM,
    output_dim: int = DEFAULT_OUTPUT_DIM,
) -> np.ndarray:
    rows = [
        [deterministic_weight(row, col) for col in range(input_dim)]
        for row in range(output_dim)
    ]
    return np.asarray(rows, dtype=np.int8)


def cpu_reference(activation: np.ndarray, weights: np.ndarray) -> np.ndarray:
    return weights.astype(np.int32) @ activation.astype(np.int32)


def build_matvec_request(
    activation: np.ndarray,
    weights: np.ndarray,
    seq: int,
    flags: int = 0,
) -> bytes:
    input_dim = int(activation.shape[0])
    output_dim = int(weights.shape[0])
    payload = activation.astype(np.int8).tobytes() + weights.astype(np.int8).tobytes()
    header = struct.pack(
        "<2sBBHHBI",
        REQ_MAGIC,
        CMD_MATVEC,
        seq & 0xFF,
        input_dim,
        output_dim,
        flags & 0xFF,
        len(payload),
    )
    return header + payload


def parse_response(packet: bytes) -> dict[str, object]:
    if len(packet) < 11:
        raise ValueError(f"response too short: {len(packet)} bytes")
    magic, cmd, seq, status, out_dim, payload_len = struct.unpack("<2sBBBHI", packet[:11])
    if magic != RESP_MAGIC:
        raise ValueError(f"bad response magic: {magic.hex()}")
    payload = packet[11:]
    if len(payload) != payload_len:
        raise ValueError(f"payload length mismatch: expected {payload_len}, got {len(payload)}")
    if payload_len % 4 != 0:
        raise ValueError("MATVEC payload is not int32-aligned")
    result = list(struct.unpack(f"<{payload_len // 4}i", payload)) if payload else []
    return {
        "cmd": cmd,
        "seq": seq,
        "status": status,
        "out_dim": out_dim,
        "payload_len": payload_len,
        "result": result,
    }


def expected_response_len(output_dim: int = DEFAULT_OUTPUT_DIM) -> int:
    return 11 + output_dim * 4


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


def latency_summary(rows: list[dict[str, object]], key: str) -> dict[str, float]:
    values = [float(row[key]) for row in rows if row.get(key) not in ("", None)]
    if not values:
        return {"mean": math.nan, "p50": math.nan, "p95": math.nan}
    return {
        "mean": statistics.fmean(values),
        "p50": percentile(values, 50.0),
        "p95": percentile(values, 95.0),
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


def write_summary_md(path: Path, title: str, summary: dict[str, object]) -> None:
    lines = [f"# {title}", ""]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def timer() -> float:
    return time.perf_counter()


def elapsed_ms(start: float, end: float | None = None) -> float:
    stop = timer() if end is None else end
    return (stop - start) * 1000.0


def update_table(path: Path, key_fields: Iterable[str], row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    if path.exists() and path.stat().st_size:
        with path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    key_fields = list(key_fields)
    row_key = tuple(str(row.get(field, "")) for field in key_fields)
    kept = [old for old in rows if tuple(str(old.get(field, "")) for field in key_fields) != row_key]
    kept.append({key: "" if value is None else value for key, value in row.items()})
    fieldnames = list(row.keys())
    for old in kept:
        for key in old.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(kept)


def import_serial_module():
    try:
        import serial  # type: ignore
    except ImportError:
        return None, "pyserial is not installed"
    return serial, ""


def serial_read_exact(port, length: int, timeout_s: float) -> bytes:
    deadline = timer() + timeout_s
    chunks = bytearray()
    while len(chunks) < length and timer() < deadline:
        chunk = port.read(length - len(chunks))
        if chunk:
            chunks.extend(chunk)
    return bytes(chunks)


def python_executable() -> str:
    return sys.executable or "python"
