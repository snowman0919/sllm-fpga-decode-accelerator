# Clean Rebuild DE10-Lite JTAG Cycle-Counter Run Manifest

| field | value |
| --- | --- |
| host | Pocket4 |
| user | `pocket4\dbsgu` |
| board | DE10-Lite / 10M50DA/DC |
| cable | USB-Blaster [USB-0] |
| Quartus version | 25.1std.0 Build 1129 |
| System Console | Windows Quartus `system-console.exe` |
| Linux source commit archived to Windows | `70953945` |
| clean rebuild `.sof` SHA-256 | `40a4f84167d2fd75972ea33684ec949b6c22e61057f1c134dd5bd4b936ef4a84` |
| prior historical board-run `.sof` SHA-256 | `3b4f2cb50d5aa5608019c550f29b42779ff9c7197383d58cf3132c0bdd635cc5` |

## Final rerun after parameterization patch

The board-facing 16x4, tileDim=1 path was rebuilt on Windows Pocket4 after the
SpinalHDL parameterization patch. The regenerated design was programmed to
DE10-Lite and rerun through the same JTAG-to-Avalon validation script.

| field | value |
| --- | --- |
| run date | 2026-07-01 |
| Quartus version | 25.1std.0 Build 1129 |
| `.sof` SHA-256 | `d3e07b8b14a19bede927d7af7e72d17f48741bb0cd03fc4c3c666172d9abb989` |
| run summary | `logs/jtag_cycle_counter_clean_rebuild_final/fpga_jtag_summary.md` |

| metric | value |
| --- | ---: |
| runs | 20 |
| pass_count | 20 |
| fail_count | 0 |
| `COMPUTE_CYCLES` mean / p50 / p95 | `65.0 / 65.0 / 65.0` |
| compute time at 50 MHz mean / p50 / p95 | `1.3 us / 1.3 us / 1.3 us` |
| JTAG total latency mean / p50 / p95 | `7756.114875 ms / 7755.08985 ms / 7775.94519 ms` |

## Result

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

## Boundary

This clean rebuild run is the primary board-measured evidence for the fixed
16x4 INT8 Decode MatVec primitive. The FPGA compute latency evidence is the
internal `COMPUTE_CYCLES` register only. JTAG total latency is System
Console/JTAG host-tool invocation overhead and is not FPGA compute latency or
whole-runtime acceleration evidence.
