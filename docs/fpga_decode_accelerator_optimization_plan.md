# FPGA Decode MatVec/MatMul Accelerator Optimization Plan

## Evidence-Bounded Direction

The latest ONNX Runtime CPUExecutionProvider profile points to dense linear algebra as the primary measured runtime hotspot. MatMul accounts for `67.5%` of traced prefill + decode phase node time, with `81.1%` in decode and `53.4%` in prefill. Inside MatMul time, `mlp_projection + lm_head` account for `88.90%`.

This changes the first optimization target from a QK-only block to a broader decode-stage tiled MatVec/MatMul datapath. It does not mean MatMul should be removed from the model. It means the repeated MLP projections and the large `lm_head` projection are the most evidence-backed candidates for a low-precision streaming accelerator path.

## Interpretation Limits

- KV-cache is not the single proven bottleneck. It remains a representative structural memory-pressure factor through cache I/O, tensor shape expansion, concat/update behavior, and long-context memory movement.
- The accelerator direction is not MatMul-free modeling. The current model and ONNX Runtime traces are projection-heavy, so the design keeps dense MatVec/MatMul as the workload.
- The design is not QK-only. QK dot-product remains a valid decode-attention primitive, but the measured MatMul hotspot is dominated by MLP projection and `lm_head`.
- DE10-Lite is not claimed to run Gemma 3 1B or a complete sLLM.
- Any FPGA result in this stage is primitive validation and synthesis feasibility evidence, not end-to-end ONNX Runtime speedup.

## Proposed First Architecture

1. Host/ORT interface
   - Receives selected projection workloads after profiling-guided operator selection.
   - Keeps host-side shape, quantization, and cache-binding decisions explicit.

2. Activation buffer
   - Holds the decode-token activation vector or a small prefill tile.
   - Broadcasts activation elements across the MatVec engine while keeping the design independent from full-model storage.

3. Weight tile streamer
   - Streams INT8 weight tiles for MLP projection, attention projections, and `lm_head`.
   - Treats `lm_head` as a bandwidth-sensitive case because of the large vocabulary dimension.

4. INT8 tiled MatVec engine
   - Computes dot products over a configurable `inputDim`, `outputDim`, and sequential/tiled inner dimension.
   - Reuses the same primitive for MLP projection, `lm_head`, attention QKV projection, attention output projection, and selected attention weighted-sum style kernels where the data layout permits it.

5. Accumulator
   - Uses INT32 accumulation for deterministic primitive validation.
   - Exposes low bits for small DE10-Lite demo display without implying full numerical integration.

6. Scale/requant unit
   - Converts INT32 accumulators toward downstream low-precision format in a future integrated path.
   - Current artifact may keep raw INT32 outputs for verification.

7. Optional element-wise/fusion unit
   - Candidate future stage for bias, activation, residual, or approximation/fusion work.
   - Included as an architecture placeholder only when profiling and graph rewrite evidence justify it.

8. Optional cache-aware interface
   - Handles KV-cache stream/buffer layout, past/present update, and cache-related graph pressure.
   - This is separate from claiming the current FPGA primitive implements KV-cache management.

## Current FPGA Validation Scope

The current extension validates an INT8 tiled MatVec primitive with deterministic activation and weight tiles, INT32 accumulation, simulation CSV artifacts, and a small DE10-Lite compile target where available. It is not a full accelerator, not full KV-cache storage or movement, and not Gemma 3 1B execution on FPGA.

## Board Programming Evidence

A Windows Quartus Prime Programmer run successfully configured the DE10-Lite with the Decode MatVec demo bitstream. The observed programmer log shows Quartus Prime Programmer `25.1std.0`, cable `USB-Blaster [USB-0]`, programming file `de10_lite_decode_matvec.sof`, target device `10M50DAF484`, and final status `configuration succeeded` with `0 errors, 0 warnings`.

This evidence supports only successful FPGA configuration of the small fixed-dimension INT8 Decode MatVec primitive bitstream. It does not show Gemma 3 1B execution, full sLLM inference, full accelerator integration, or ONNX Runtime speedup. Board-level numeric output validation remains separate from bitstream programming success and should be recorded from `HEX3..HEX0` or `LEDR` observations if captured.

Detailed board-programming evidence is recorded in `fpga_test/captured/decode_matvec_board_validation.md` and summarized in `paper_assets/tables/decode_matvec_board_validation.csv`.

## First Optimization Deliverables

- Profiling-derived candidate ranking for dense projection categories.
- Roofline-style design estimate that labels compute-bound or bandwidth-bound tendencies as estimates.
- INT8 tiled MatVec primitive simulation with deterministic software-reference comparison.
- Small fixed-dimension DE10-Lite demo top for synthesis and `.sof` generation only.
- NAS package copy when the local `nas/` symlink is writable.
