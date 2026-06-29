# ONNX Runtime vs FPGA Primitive Evaluation Protocol

This protocol aligns host baselines and FPGA primitive validation around one fixed operation:

| field | value |
| --- | --- |
| `input_dim` | 16 |
| `output_dim` | 4 |
| `macs` | 64 |
| activation | deterministic signed int8 vector from `windows/matvec_common.py` |
| weight | deterministic signed int8 row-major matrix from `windows/matvec_common.py` |
| CPU reference | int8 inputs with int32 accumulation |
| FPGA primitive | int8 inputs with int32 accumulation |

## Evidence Classes

| artifact | evidence type | latency source | boundary |
| --- | --- | --- | --- |
| CPU NumPy primitive baseline | measured | host wall time | host-side reference only |
| ONNX Runtime MatVec micrograph | measured | `CPUExecutionProvider` `session.run` wall time | float32 MatMul equivalent |
| ONNX Runtime MatMulInteger micrograph | measured or skipped | `CPUExecutionProvider` `session.run` wall time | int8 inputs with int32 output when the local ORT build supports `MatMulInteger`; otherwise skipped with dtype boundary documented |
| FPGA JTAG total invocation | measured when a real board log exists | System Console/JTAG wall time | invocation overhead, not FPGA compute speed |
| FPGA internal cycle counter | measured when a real board log exists | `COMPUTE_CYCLES` register | primitive compute latency only |
| optimized FPGA interface model | projected | weight-preloaded low-overhead interface assumption | design estimate, not board measurement |

## Paper-Facing Outputs

- `paper_assets/tables/onnx_runtime_aligned_micrograph_baseline.csv`
- `paper_assets/tables/onnx_runtime_integer_micrograph_baseline.csv`
- `paper_assets/tables/gemma_partial_tile_baseline.csv`
- `paper_assets/tables/fpga_jtag_primitive_benchmark.csv`
- `paper_assets/tables/fpga_jtag_cycle_counter_summary.csv`
- `paper_assets/tables/quartus_resource_timing_summary.csv`

## Interpretation Rule

Do not compare JTAG total latency as FPGA compute speed. If the FPGA internal cycle counter is faster than the ONNX Runtime micrograph, describe it only as a fixed primitive compute-latency comparison. Do not describe it as full-model acceleration, full Gemma execution, custom ONNX Runtime operator speedup, or end-to-end ONNX Runtime speedup.
