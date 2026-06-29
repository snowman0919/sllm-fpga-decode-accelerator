# Claim Boundary

This repository may claim:

- ONNX export, graph inspection, and ONNX Runtime profiling where an exported model interface permits it.
- PyTorch host-side reference baselines as PyTorch results only.
- FPGA primitive validation for fixed INT8 Decode MatVec or QK-style dot-product blocks.
- UART-based host-to-FPGA primitive invocation feasibility, correctness, and latency overhead when real logs exist.
- USB-Blaster JTAG-to-Avalon register invocation feasibility and correctness when real passing logs exist.
- USB-Blaster JTAG-to-Avalon latency overhead only when a numeric passing log is archived; this is invocation overhead, not FPGA compute time.
- FPGA internal compute cycle latency only when a real passing board log reads the `COMPUTE_CYCLES` register from the cycle-counter-enabled bitstream.
- Optimized FPGA interface comparisons as projected design estimates only, separated from measured rows.
- Gemma-derived partial tile experiments as selected node/category feasibility evidence only.

This repository must not claim:

- Full Gemma 3 1B execution on DE10-Lite.
- Full ONNX Runtime end-to-end acceleration by FPGA.
- CPUExecutionProvider speedup unless real logs prove it for the exact measured path.
- UART as a performance-optimized accelerator interconnect.
- JTAG offload as a performance-optimized accelerator interconnect.
- JTAG measured latency as FPGA compute latency or measured speedup evidence.
- Cycle-counter values as measured evidence when they come from simulation, estimates, stale logs, or missing board runs rather than a real passing JTAG register read.
- Optimized FPGA design estimates as measured board latency.
- Process RSS deltas as direct KV-cache allocation measurements.
- Synthetic tile weights as full Gemma weight evidence.

Paper tables should include FPGA UART numbers only when the corresponding log contains a passing correctness check, latency breakdown, COM port, baudrate, and environment information.

A no-COM skip summary, timeout summary, failed UART response, stub ONNX graph, or ORT-equivalent UART harness is not a paper result.

A missing-Quartus, missing-USB-Blaster, missing-JTAG-master, timeout, failed register read/write, or failed JTAG correctness summary is not a paper result.

For the current JTAG-to-Avalon MatVec result, the measured evidence is the correctness result `[-271, 239, 287, 797]` from the register invocation path. The provided success record does not include an archived numeric latency breakdown, so the paper-facing JTAG benchmark table leaves latency fields blank and treats the result as correctness/invocation evidence only.

The register bank now includes `COMPUTE_CYCLES`, `CORE_TOTAL_CYCLES`, `LAST_RUN_ID`, and `DEBUG_STATUS`, and the Windows runner can archive those fields. In the current repository state, no repeated real-board cycle-counter log has been added, so FPGA internal compute latency remains pending rather than measured.

Optimized FPGA comparison rows must be labeled `projected` or `design estimate`. They may use assumptions such as weight preloading, batched register access, DMA, or shared-memory-style invocation, but they must not be described as measured speedup over ONNX Runtime.

No current artifact supports a measured full-model acceleration claim or measured ONNX Runtime end-to-end speedup claim.
