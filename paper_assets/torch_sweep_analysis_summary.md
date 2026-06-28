# PyTorch CPU Baseline Context Sweep Analysis

## Experimental Conditions

- Baseline under analysis: PyTorch CPU baseline. This summary does not describe ONNX Runtime, CUDA/GPU execution, or end-to-end FPGA decode acceleration.
- Input latency table used for analysis: `paper_assets/tables/torch_decode_latency_by_context.csv`
- Input memory table used for analysis: `paper_assets/tables/torch_memory_by_context.csv`
- Device and dtype recorded in the sweep: `cpu` / `bfloat16`
- Context lengths analyzed: 128, 512, 1024, 2048, 4096, 8192, 16384, 32768
- Decode tokens per run: 16
- Measured runs per context: 5 with 1 warmup run(s)
- Theoretical KV-cache parameters: layers=26, kv_heads=1, head_dim=256, bytes_per_element=2

## Key Numbers

- Decode latency increased from 65.99 ms/token at context 128 to 130.48 ms/token at context 32768 (1.98x).
- Prefill latency increased by 1331.16x across the same context range, from 124.51 ms to 165746.77 ms.
- Theoretical KV-cache size increased from 3.25 MiB to 832.00 MiB (256.00x).
- Observed prefill RSS delta increased from 64.00 MiB to 16415.93 MiB (256.48x).
- The observed peak RSS reached 20812.91 MiB at the maximum analyzed context length.
- The ratio between observed prefill RSS delta and theoretical KV-cache size stayed within 19.69x to 20.60x over the sweep.

## Interpretable Scope

Within this PyTorch CPU baseline, decode latency grows gradually with context length while prefill latency and process RSS growth rise much more sharply. The tables and figures support a host-side comparison between theoretical KV-cache scaling and observed memory movement at the process level, but they should be interpreted only as a baseline characterization for this software stack and this measurement setup.

## RSS Interpretation Limits

The observed RSS delta values in these outputs are process-level resident-set-size changes measured around prefill. They are not a direct measurement of KV-cache bytes, and they should not be treated as proof that all of the RSS change is caused only by KV-cache allocation. Other allocator effects, framework buffers, page residency changes, and host-side bookkeeping can contribute to the observed delta.

## Connection to FPGA Primitive Validation

These PyTorch CPU baseline trends help motivate why long-context decode workloads become increasingly sensitive to memory footprint and latency, but they do not demonstrate FPGA acceleration of real Gemma 3 1B decode. In this repository, the FPGA evidence remains at the primitive-validation level, such as operator-scale correctness checks plus resource, timing, and latency studies for the implemented building blocks.
