# DE10-Lite JTAG Cycle-Counter Board Run Manifest

## Host

| field | value |
| --- | --- |
| host | Pocket4 |
| user | `pocket4\dbsgu` |
| board | DE10-Lite / 10M50DA/DC |
| cable | USB-Blaster [USB-0] |
| Quartus version | 25.1std.0 Build 1129 |
| System Console | `C:\altera_lite\25.1std\quartus\sopc_builder\bin\system-console.exe` |
| `.sof` SHA-256 | `3b4f2cb50d5aa5608019c550f29b42779ff9c7197383d58cf3132c0bdd635cc5` |
| source commit before this manifest | `23eef6ba` |

## Board Result

| metric | value |
| --- | ---: |
| runs | 20 |
| pass_count | 20 |
| fail_count | 0 |
| reference | `-271 239 287 797` |
| result | `-271 239 287 797` |
| `COMPUTE_CYCLES` mean / p50 / p95 | `65.0 / 65.0 / 65.0` |
| compute time at 50 MHz mean / p50 / p95 | `1.3 us / 1.3 us / 1.3 us` |
| JTAG total latency mean / p50 / p95 | `7756.72185 ms / 7734.1137 ms / 7819.554125 ms` |
| ORT MatMulInteger baseline mean / p50 / p95 | `0.013012 ms / 0.011 ms / 0.0173 ms` |

## Evidence Boundary

This manifest freezes a real Windows Pocket4 board run for the fixed 16x4 INT8
Decode MatVec primitive. `COMPUTE_CYCLES` is board-measured primitive internal
compute evidence. JTAG total latency is System Console/JTAG invocation overhead
and is not FPGA compute latency, full ONNX model acceleration, or end-to-end
sLLM inference speedup evidence.

Primary files:

- `logs/remote_board_eval/logs/jtag_cycle_counter_real_final/fpga_jtag_summary.json`
- `logs/remote_board_eval/logs/jtag_cycle_counter_real_final/fpga_jtag_matvec.csv`
- `logs/remote_board_eval/logs/ort_integer_baseline_board_env/ort_matmulinteger_summary.json`
