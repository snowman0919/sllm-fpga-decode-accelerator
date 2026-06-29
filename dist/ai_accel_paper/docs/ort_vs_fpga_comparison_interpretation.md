# ORT vs FPGA Comparison Interpretation

This comparison separates measured host baselines, measured JTAG correctness/invocation evidence, measured FPGA internal cycle-counter evidence, and projected optimized-interface estimates.

| backend | evidence | latency source | mean us | p50 us | p95 us | boundary |
| --- | --- | --- | ---: | ---: | ---: | --- |
| CPU NumPy primitive baseline | measured | Python/NumPy host wall time | 28.922000 | 18.426000 | 49.805000 | host-side primitive baseline; not ONNX Runtime profiling |
| ONNX Runtime MatVec micrograph | measured | ONNX Runtime CPUExecutionProvider session.run wall time | 63.135000 | 14.327000 | 153.809000 | aligned micrograph baseline only; not full Gemma ONNX Runtime profiling |
| ONNX Runtime MatMulInteger micrograph | measured | ORT session.run MatMulInteger wall time | 13.012000 | 11.000000 | 17.300000 | integer micrograph baseline only; not full Gemma ONNX Runtime profiling |
| FPGA JTAG total invocation | measured | System Console/JTAG total invocation wall time | 7720850.160000 | 7720451.150000 | 7748848.330000 | JTAG invocation overhead; not compute latency |
| FPGA internal Decode MatVec | board_measured | FPGA COMPUTE_CYCLES register at 50 MHz | 1.300000 | 1.300000 | 1.300000 | primitive internal cycle measurement only; not end-to-end ONNX Runtime or full-model speedup |
| FPGA optimized interface estimate | projected | weight-preloaded low-overhead host interface model | 5.142768 |  |  | design estimate only; not measured board latency |

JTAG-to-Avalon total latency is not FPGA compute latency. It includes System Console execution, JTAG service access, register writes/reads, and polling.

The FPGA cycle-counter value is fixed primitive compute latency only. It must not be used to claim full-model, full Gemma, custom-op, or end-to-end ONNX Runtime speedup.
