# Claim Boundary

This repository may claim:

- ONNX export, graph inspection, and ONNX Runtime profiling where an exported model interface permits it.
- PyTorch host-side reference baselines as PyTorch results only.
- FPGA primitive validation for fixed INT8 Decode MatVec or QK-style dot-product blocks.
- UART-based host-to-FPGA primitive invocation feasibility, correctness, and latency overhead when real logs exist.
- Gemma-derived partial tile experiments as selected node/category feasibility evidence only.

This repository must not claim:

- Full Gemma 3 1B execution on DE10-Lite.
- Full ONNX Runtime end-to-end acceleration by FPGA.
- CPUExecutionProvider speedup unless real logs prove it for the exact measured path.
- UART as a performance-optimized accelerator interconnect.
- Process RSS deltas as direct KV-cache allocation measurements.
- Synthetic tile weights as full Gemma weight evidence.

Paper tables should include FPGA UART numbers only when the corresponding log contains a passing correctness check, latency breakdown, COM port, baudrate, and environment information.
