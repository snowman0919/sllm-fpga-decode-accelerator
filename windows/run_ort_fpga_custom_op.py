#!/usr/bin/env python3
"""Run the FPGA UART path as an ORT graph-level equivalent harness.

This is not a native ONNX Runtime custom-op DLL. It uses the same deterministic
micrograph inputs and records custom_op=false so paper tables cannot confuse it
with a true in-ORT execution provider/custom-op implementation.
"""

from __future__ import annotations

import argparse

from matvec_common import (
    DEFAULT_BAUDRATE,
    DEFAULT_INPUT_DIM,
    DEFAULT_OUTPUT_DIM,
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
    write_csv,
    write_json,
    write_summary_md,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUDRATE)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--log-dir")
    parser.add_argument("--input-dim", type=int, default=DEFAULT_INPUT_DIM)
    parser.add_argument("--output-dim", type=int, default=DEFAULT_OUTPUT_DIM)
    parser.add_argument("--timeout-s", type=float, default=3.0)
    return parser.parse_args()


def skipped(log_dir, reason: str, args: argparse.Namespace) -> None:
    summary = {
        "backend": "ort_equivalent_uart_bridge",
        "custom_op": False,
        "execution_mode": "ort_equivalent_uart_bridge",
        "true_custom_op_dll_loaded": False,
        "skipped": True,
        "reason": reason,
        "port": args.port or "",
        "baudrate": args.baud,
    }
    write_json(log_dir / "ort_fpga_custom_op_summary.json", summary)
    write_summary_md(log_dir / "ort_fpga_custom_op_summary.md", "ORT-Equivalent FPGA UART Summary", summary)
    print(f"ORT-equivalent FPGA UART test skipped: {reason}")


def main() -> None:
    args = parse_args()
    log_dir = resolve_log_dir(args.log_dir)
    if not args.port:
        skipped(log_dir, "no COM port specified", args)
        return
    serial, reason = import_serial_module()
    if serial is None:
        skipped(log_dir, reason, args)
        return
    try:
        port = serial.Serial(args.port, args.baud, timeout=0.05, write_timeout=args.timeout_s)
    except Exception as exc:
        skipped(log_dir, f"could not open {args.port}: {exc}", args)
        return

    rows: list[dict[str, object]] = []
    all_pass = True
    try:
        for run in range(args.runs):
            activation = deterministic_activation(args.input_dim)
            weights = deterministic_weights(args.input_dim, args.output_dim)
            reference = cpu_reference(activation, weights)
            request = build_matvec_request(activation, weights, seq=run)
            t0 = timer()
            port.reset_input_buffer()
            port.reset_output_buffer()
            port.write(request)
            port.flush()
            t1 = timer()
            response_bytes = serial_read_exact(port, expected_response_len(args.output_dim), args.timeout_s)
            t2 = timer()
            try:
                response = parse_response(response_bytes)
                result = response["result"]
                pass_run = response["status"] == 0 and result == [int(v) for v in reference]
                error = ""
            except Exception as exc:
                response = {"status": "decode_error", "result": []}
                result = []
                pass_run = False
                error = str(exc)
            t3 = timer()
            all_pass = all_pass and pass_run
            rows.append(
                {
                    "run": run,
                    "backend": "ort_equivalent_uart_bridge",
                    "graph": "matvec_fpga_custom_stub.onnx",
                    "provider": "UART bridge outside ORT",
                    "custom_op": False,
                    "execution_mode": "ort_equivalent_uart_bridge",
                    "true_custom_op_dll_loaded": False,
                    "input_dim": args.input_dim,
                    "output_dim": args.output_dim,
                    "dtype": "int8_to_int32",
                    "uart_tx_ms": elapsed_ms(t0, t1),
                    "uart_rx_wait_ms": elapsed_ms(t1, t2),
                    "packet_decode_ms": elapsed_ms(t2, t3),
                    "latency_ms": elapsed_ms(t0, t3),
                    "correctness_pass": pass_run,
                    "status": response.get("status"),
                    "result": " ".join(str(int(v)) for v in result),
                    "error": error,
                }
            )
    finally:
        port.close()

    latency = latency_summary(rows, "latency_ms")
    tx = latency_summary(rows, "uart_tx_ms")
    rx = latency_summary(rows, "uart_rx_wait_ms")
    txrx_mean = tx["mean"] + rx["mean"]
    summary = {
        "backend": "ort_equivalent_uart_bridge",
        "graph": "matvec_fpga_custom_stub.onnx",
        "provider": "UART bridge outside ORT",
        "custom_op": False,
        "execution_mode": "ort_equivalent_uart_bridge",
        "true_custom_op_dll_loaded": False,
        "input_dim": args.input_dim,
        "output_dim": args.output_dim,
        "dtype": "int8_to_int32",
        "runs": args.runs,
        "correctness_pass": all_pass,
        "latency_ms_mean": round(latency["mean"], 6),
        "latency_ms_p50": round(latency["p50"], 6),
        "latency_ms_p95": round(latency["p95"], 6),
        "uart_txrx_ms_mean": round(txrx_mean, 6),
        "note": "Graph-level equivalent harness only; not a true ORT custom-op DLL and not a paper result.",
    }
    write_csv(log_dir / "ort_fpga_custom_op.csv", rows)
    write_json(log_dir / "ort_fpga_custom_op_summary.json", summary)
    write_summary_md(log_dir / "ort_fpga_custom_op_summary.md", "ORT-Equivalent FPGA UART Summary", summary)
    print(f"wrote {log_dir / 'ort_fpga_custom_op_summary.md'}")


if __name__ == "__main__":
    main()
