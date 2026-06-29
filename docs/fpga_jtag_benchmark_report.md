# FPGA JTAG Primitive Benchmark Report

## Summary

The current paper-facing JTAG evidence is a measured correctness and invocation result for the fixed INT8 Decode MatVec primitive over a USB-Blaster JTAG-to-Avalon register path.

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

The paper-facing CSV is `paper_assets/tables/fpga_jtag_primitive_benchmark.csv`.

## Latency Interpretation

The JTAG-to-Avalon experiment confirms that the synthesized primitive can be invoked through the board register path and can return the same deterministic result as the CPU reference. The provided success record does not include an archived numeric latency breakdown, so the latency columns in the CSV are intentionally left blank.

Even when a future run records `total_latency_ms`, that value must be interpreted as System Console/JTAG invocation overhead. It includes host tool execution, JTAG service setup or access, register write/read traffic, and polling. It is not the pure FPGA compute time of the MatVec datapath.

## Claim Boundary

Allowed interpretation:

- JTAG measured result: correctness/invocation evidence.
- JTAG latency, when present: low-speed invocation overhead.
- The result supports primitive feasibility on a real board path.

Disallowed interpretation:

- Do not use JTAG latency as FPGA compute speedup evidence.
- Do not claim measured FPGA acceleration over ONNX Runtime from the JTAG path.
- Do not claim full Gemma 3 1B execution, full KV-cache management, custom ONNX Runtime operator speedup, or end-to-end FPGA acceleration.
