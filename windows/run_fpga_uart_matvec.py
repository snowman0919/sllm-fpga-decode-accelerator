#!/usr/bin/env python3
"""Call the fixed Decode MatVec primitive over a DE10-Lite UART bridge."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from matvec_common import (
    DEFAULT_BAUDRATE,
    DEFAULT_INPUT_DIM,
    DEFAULT_OUTPUT_DIM,
    PROJECT_ROOT,
    build_matvec_request,
    cpu_reference,
    deterministic_activation,
    deterministic_weights,
    elapsed_ms,
    expected_response_len,
    import_serial_module,
    latency_summary,
    parse_response,
    resolve_log_dir,
    serial_read_exact,
    timer,
    update_table,
    write_csv,
    write_json,
    write_summary_md,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", help="Windows COM port, for example COM5")
    parser.add_argument("--list-ports", action="store_true", help="List detected serial ports and exit")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUDRATE)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--log-dir")
    parser.add_argument("--input-dim", type=int, default=DEFAULT_INPUT_DIM)
    parser.add_argument("--output-dim", type=int, default=DEFAULT_OUTPUT_DIM)
    parser.add_argument("--timeout-s", type=float, default=3.0)
    parser.add_argument("--dump-request-hex", action="store_true", help="Record request packet hex in the CSV")
    parser.add_argument("--dump-response-hex", action="store_true", help="Record response packet hex in the CSV")
    return parser.parse_args()


def list_ports() -> int:
    serial, serial_reason = import_serial_module()
    if serial is None:
        print(f"serial port listing unavailable: {serial_reason}")
        return 2
    try:
        from serial.tools import list_ports as serial_list_ports  # type: ignore
    except Exception as exc:
        print(f"serial port listing unavailable: {exc}")
        return 2
    ports = list(serial_list_ports.comports())
    if not ports:
        print("No serial ports detected.")
        return 0
    for port in ports:
        details = " ".join(part for part in [port.description, port.hwid] if part)
        print(f"{port.device}\t{details}")
    return 0


def skipped_summary(log_dir: Path, reason: str, args: argparse.Namespace, exit_code: int = 0) -> int:
    summary = {
        "backend": "fpga_uart",
        "skipped": True,
        "reason": reason,
        "exit_code": exit_code,
        "port": args.port or "",
        "baudrate": args.baud,
        "input_dim": args.input_dim,
        "output_dim": args.output_dim,
        "runs": args.runs,
        "checksum": "none",
        "encoding": "request activation/weight are signed int8; response result is little-endian signed int32",
        "paper_table_updated": False,
    }
    write_json(log_dir / "fpga_uart_summary.json", summary)
    write_summary_md(log_dir / "fpga_uart_summary.md", "FPGA UART MatVec Summary", summary)
    print(f"FPGA UART test skipped: {reason}")
    return exit_code


def main() -> int:
    args = parse_args()
    if args.list_ports:
        return list_ports()

    log_dir = resolve_log_dir(args.log_dir)

    if not args.port:
        return skipped_summary(log_dir, "no COM port specified", args, exit_code=0)

    serial, serial_reason = import_serial_module()
    if serial is None:
        return skipped_summary(log_dir, serial_reason, args, exit_code=2)

    try:
        port = serial.Serial(args.port, args.baud, timeout=0.05, write_timeout=args.timeout_s)
    except Exception as exc:  # pyserial exposes platform-specific exception subclasses
        return skipped_summary(log_dir, f"could not open {args.port}: {exc}", args, exit_code=2)

    rows: list[dict[str, object]] = []
    all_pass = True
    try:
        for run in range(args.runs):
            t0 = timer()
            activation = deterministic_activation(args.input_dim)
            weights = deterministic_weights(args.input_dim, args.output_dim)
            reference = cpu_reference(activation, weights)
            t1 = timer()
            request = build_matvec_request(activation, weights, seq=run)
            t2 = timer()
            port.reset_input_buffer()
            port.reset_output_buffer()
            port.write(request)
            port.flush()
            t3 = timer()
            response_bytes = serial_read_exact(port, expected_response_len(args.output_dim), args.timeout_s)
            t4 = timer()
            try:
                if len(response_bytes) != expected_response_len(args.output_dim):
                    raise TimeoutError(
                        f"timeout waiting for {expected_response_len(args.output_dim)} response bytes; got {len(response_bytes)}"
                    )
                response = parse_response(response_bytes)
                result = response["result"]
                pass_run = response["status"] == 0 and result == [int(v) for v in reference]
                error = ""
            except Exception as exc:
                response = {"status": "decode_error", "result": []}
                result = []
                pass_run = False
                error = str(exc)
            t5 = timer()
            all_pass = all_pass and pass_run
            rows.append(
                {
                    "run": run,
                    "input_dim": args.input_dim,
                    "output_dim": args.output_dim,
                    "generation_ms": elapsed_ms(t0, t1),
                    "packet_encode_ms": elapsed_ms(t1, t2),
                    "serial_tx_ms": elapsed_ms(t2, t3),
                    "fpga_wait_rx_ms": elapsed_ms(t3, t4),
                    "packet_decode_ms": elapsed_ms(t4, t5),
                    "total_latency_ms": elapsed_ms(t0, t5),
                    "status": response.get("status"),
                    "reference": " ".join(str(int(v)) for v in reference),
                    "result": " ".join(str(int(v)) for v in result),
                    "correctness_pass": pass_run,
                    "error": error,
                    "request_hex": request.hex() if args.dump_request_hex else "",
                    "response_hex": response_bytes.hex() if args.dump_response_hex else "",
                }
            )
    finally:
        port.close()

    total = latency_summary(rows, "total_latency_ms")
    tx = latency_summary(rows, "serial_tx_ms")
    rx = latency_summary(rows, "fpga_wait_rx_ms")
    macs_per_run = args.input_dim * args.output_dim
    summary = {
        "backend": "fpga_uart",
        "port": args.port,
        "baudrate": args.baud,
        "input_dim": args.input_dim,
        "output_dim": args.output_dim,
        "runs": args.runs,
        "correctness_pass": all_pass,
        "total_latency_ms_mean": round(total["mean"], 6),
        "total_latency_ms_p50": round(total["p50"], 6),
        "total_latency_ms_p95": round(total["p95"], 6),
        "tx_latency_ms_mean": round(tx["mean"], 6),
        "rx_wait_latency_ms_mean": round(rx["mean"], 6),
        "effective_macs_per_s": round((macs_per_run / (total["mean"] / 1000.0)) if total["mean"] else 0.0, 3),
        "log_dir": str(log_dir),
        "checksum": "none",
        "encoding": "request activation/weight are signed int8; response result is little-endian signed int32",
        "paper_table_updated": all_pass,
        "note": "UART is a low-speed verification/control path, not a performance bus.",
    }
    write_csv(log_dir / "fpga_uart_matvec.csv", rows)
    write_json(log_dir / "fpga_uart_summary.json", summary)
    write_summary_md(log_dir / "fpga_uart_summary.md", "FPGA UART MatVec Summary", summary)

    if all_pass:
        update_table(
            PROJECT_ROOT / "paper_assets/tables/fpga_uart_primitive_benchmark.csv",
            ["backend", "input_dim", "output_dim", "baudrate"],
            {
                "backend": "fpga_uart",
                "input_dim": args.input_dim,
                "output_dim": args.output_dim,
                "runs": args.runs,
                "correctness_pass": all_pass,
                "total_latency_ms_mean": round(total["mean"], 6),
                "total_latency_ms_p50": round(total["p50"], 6),
                "total_latency_ms_p95": round(total["p95"], 6),
                "tx_latency_ms_mean": round(tx["mean"], 6),
                "rx_wait_latency_ms_mean": round(rx["mean"], 6),
                "effective_macs_per_s": summary["effective_macs_per_s"],
                "baudrate": args.baud,
                "note": "Measured only when a DE10-Lite UART bitstream is connected and correctness passes; speedup is not implied.",
            },
        )
    print(f"wrote {log_dir / 'fpga_uart_summary.md'}")
    return 0 if all_pass else 3


if __name__ == "__main__":
    sys.exit(main())
