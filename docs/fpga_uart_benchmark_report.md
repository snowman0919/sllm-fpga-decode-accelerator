# FPGA UART Benchmark Report

This report separates completed host-side checks from pending FPGA UART board measurements.

## Completed Host-Side Checks

- CPU fixed INT8 MatVec baseline: smoke-tested with 3 runs in the Nix environment.
- ONNX Runtime MatVec micrograph CPU baseline: smoke-tested with 3 runs in the Nix environment.
- Gemma-derived partial tile CPU baseline: smoke-tested with 3 runs in the Nix environment.
- FPGA UART no-COM behavior: runner writes a skipped summary when no COM port is available or a requested port cannot be opened.

## Pending FPGA Board Measurement

No real COM-port FPGA UART latency log has been captured in this repository state. Therefore:

- no FPGA UART latency number should be used in the manuscript
- no table 13 or figure 7 should be added to the paper yet
- `paper_assets/tables/fpga_uart_primitive_benchmark.csv`, if present, must be read as a host-side staging table unless it contains a real `backend=fpga_uart` row with `correctness_pass=true`, COM port, baudrate, and latency breakdown from a board run

## Required Evidence Before Paper Use

A paper-facing FPGA UART result requires all of the following:

- Windows COM port recorded
- baudrate recorded
- request/response protocol version documented
- correctness comparison against CPU int32 reference passes
- `fpga_uart_matvec.csv` exists with latency breakdown columns
- `fpga_uart_summary.json` records `paper_table_updated=true`

Until those conditions are met, the FPGA UART path is implementation readiness evidence only.
