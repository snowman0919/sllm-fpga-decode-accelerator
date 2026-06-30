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
| primary board-measured `.sof` SHA-256 | `40a4f84167d2fd75972ea33684ec949b6c22e61057f1c134dd5bd4b936ef4a84` |
| source commit archived to Windows before clean rebuild run | `70953945` |
| historical prior board-run `.sof` SHA-256 | `3b4f2cb50d5aa5608019c550f29b42779ff9c7197383d58cf3132c0bdd635cc5` |

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
| JTAG total latency mean / p50 / p95 | `7720.85016 ms / 7720.45115 ms / 7748.84833 ms` |
| ORT MatMulInteger baseline mean / p50 / p95 | `0.013012 ms / 0.011 ms / 0.0173 ms` |

## Evidence Boundary

This manifest freezes the primary real Windows Pocket4 board run for the fixed
16x4 INT8 Decode MatVec primitive using a clean-rebuilt Quartus `.sof`.
`COMPUTE_CYCLES` is board-measured primitive internal compute evidence. JTAG
total latency is System Console/JTAG invocation overhead and is not FPGA compute
latency, full ONNX model acceleration, or end-to-end sLLM inference speedup
evidence.

Primary files:

- `logs/jtag_cycle_counter_clean_rebuild_final/jtag_cycle_counter_clean_rebuild_final/fpga_jtag_summary.json`
- `logs/jtag_cycle_counter_clean_rebuild_final/jtag_cycle_counter_clean_rebuild_final/fpga_jtag_matvec.csv`
- `quartus/de10_lite_jtag_matvec/output_files/de10_lite_jtag_matvec.sof`
- `assets/c11.csv`

Historical prior files:

- `logs/remote_board_eval/logs/jtag_cycle_counter_real_final/fpga_jtag_summary.json`
- `logs/remote_board_eval/logs/jtag_cycle_counter_real_final/fpga_jtag_matvec.csv`
- `logs/remote_board_eval/logs/ort_integer_baseline_board_env/ort_matmulinteger_summary.json`
