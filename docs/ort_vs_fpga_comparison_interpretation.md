# ORT vs FPGA Comparison Interpretation

This comparison separates measured host baselines, measured JTAG correctness/invocation evidence, pending FPGA cycle-counter evidence, and projected optimized-interface estimates.

| backend | evidence | latency source | latency us | boundary |
| --- | --- | --- | ---: | --- |
| CPU NumPy primitive baseline | measured | host wall time around NumPy int32 reference | 28.922000 | host-side primitive baseline; not ONNX Runtime profiling |
| ONNX Runtime MatVec micrograph | measured | ONNX Runtime CPUExecutionProvider session.run wall time | 63.135000 | aligned micrograph baseline only; not full Gemma ONNX Runtime profiling |
| ONNX Runtime MatMulInteger micrograph | measured | ONNX Runtime CPUExecutionProvider MatMulInteger session.run wall time | 43.146000 | integer micrograph baseline only; not full Gemma ONNX Runtime profiling |
| FPGA JTAG total invocation | measured | not archived in current success record |  | JTAG invocation overhead; not compute speed |
| FPGA internal compute cycles | pending_hardware_measurement | FPGA COMPUTE_CYCLES register |  | do not report as measured until a real board log reads COMPUTE_CYCLES |
| FPGA optimized interface estimate | projected | weight-preloaded low-overhead host interface model | 5.142768 | design estimate only; not measured board latency |

JTAG-to-Avalon total latency is not FPGA compute latency. It includes System Console execution, JTAG service access, register writes/reads, and polling.

Any future FPGA cycle-counter value should be described as fixed primitive compute latency only. It must not be used to claim full-model, full Gemma, custom-op, or end-to-end ONNX Runtime speedup.
