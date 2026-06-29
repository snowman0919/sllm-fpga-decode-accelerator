# FPGA JTAG Primitive Benchmark Report

## Summary

The current paper-facing JTAG evidence is a measured correctness, invocation, and internal cycle-counter result for the fixed INT8 Decode MatVec primitive over a USB-Blaster JTAG-to-Avalon register path.

Recorded result:

| field | value |
| --- | --- |
| backend | FPGA JTAG register offload |
| interface | `jtag_to_avalon` |
| input dimension | 16 |
| output dimension | 4 |
| MACs | 64 |
| reference | `-271 239 287 797` |
| result | `-271 239 287 797` |
| correctness | `True` |
| runs | `20` |
| pass / fail | `20 / 0` |
| JTAG total latency mean / p50 / p95 | `7756.72185 ms / 7734.1137 ms / 7819.554125 ms` |
| `COMPUTE_CYCLES` mean / p50 / p95 | `65 / 65 / 65` |
| compute time at 50 MHz mean / p50 / p95 | `1.3 us / 1.3 us / 1.3 us` |

The paper-facing CSV is `paper_assets/tables/fpga_jtag_primitive_benchmark.csv`.

The updated register bank also exposes an internal cycle-counter path:

| register | meaning |
| --- | --- |
| `COMPUTE_CYCLES` | cycles latched from accepted start pulse to MatVec `done` |
| `CORE_TOTAL_CYCLES` | cycles from host start register write observation to `done` latch |
| `LAST_RUN_ID` | sequence id captured for the most recent accepted run |
| `DEBUG_STATUS` | low-level FSM/status bits for diagnosing failed or partial runs |

The real board cycle-counter paper CSV is `paper_assets/tables/fpga_jtag_cycle_counter_summary.csv`. It should only contain rows generated from real passing board runs.

The register-bank RTL simulation writes a separate simulation-only CSV:

```text
paper_assets/tables/decode_matvec_regbank_cycle_counter_sim.csv
```

That file verifies register writes, `CONTROL.start`, `STATUS.done`, `RESULT`, `LAST_RUN_ID`, and a nonzero expected-range `COMPUTE_CYCLES` value before a board run. It is simulation evidence only and must not be promoted to measured board latency.

## Latency Interpretation

The JTAG-to-Avalon experiment confirms that the synthesized primitive can be invoked through the board register path and can return the same deterministic result as the CPU reference. The archived 20-run board log includes both total JTAG invocation latency and the FPGA internal cycle-counter value.

`total_wall_latency_ms` and `system_console_elapsed_ms` must be interpreted as System Console/JTAG invocation overhead. They include host tool execution, JTAG service setup or access, register write/read traffic, and polling. They are not the pure FPGA compute time of the MatVec datapath.

FPGA compute latency must be taken from `COMPUTE_CYCLES` and converted with the documented clock frequency, normally `50 MHz` on DE10-Lite:

```text
compute_time_us = compute_cycles / 50_000_000 * 1e6
```

If Quartus timing extraction provides an Fmax, an additional `compute_time_at_fmax_us` value may be reported as timing-analysis-derived context. Keep that value separate from the 50 MHz board-clock conversion.

## Claim Boundary

Allowed interpretation:

- JTAG measured result: correctness/invocation evidence.
- JTAG latency, when present: low-speed invocation overhead.
- Internal `COMPUTE_CYCLES`: primitive compute latency evidence only.
- The result supports primitive feasibility on a real board path.

Disallowed interpretation:

- Do not use JTAG latency as FPGA compute speedup evidence.
- Do not claim measured FPGA acceleration over ONNX Runtime from the JTAG path.
- Do not claim full Gemma 3 1B execution, full KV-cache management, custom ONNX Runtime operator speedup, or end-to-end FPGA acceleration.
