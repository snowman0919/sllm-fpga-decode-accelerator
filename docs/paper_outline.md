# Paper Outline

## Abstract

- Problem statement: bottleneck location is unclear in ONNX Runtime-based on-device sLLM inference until export, graph structure, runtime execution, memory pressure, prefill, and decode are inspected together.
- Method summary: ONNX export and graph inspection, ONNX Runtime prefill/decode profiling, PyTorch host-side reference baselines, profiling-derived MatMul category analysis, and primitive-level FPGA validation.
- Main finding: current ORT CPU profiling shows MatMul as the dominant traced runtime hotspot, with decode MatMul share at 81.1% and `mlp_projection + lm_head` at 88.90% of MatMul time.
- Hardware scope: the FPGA result validates a small INT8 Decode MatVec primitive and DE10-Lite bitstream configuration only; it is not full Gemma 3 1B execution or measured FPGA speedup.
- Main contribution: an evidence-bounded workflow connecting ONNX Runtime bottleneck analysis to realistic primitive-level FPGA validation.

## Introduction

- Why on-device sLLM inference matters.
- Why decode-stage latency matters more than bulk throughput in interactive generation.
- Why KV-cache growth is a representative structural source of long-context decode memory pressure.
- Why the study does not assume KV-cache is the only bottleneck before profiling.
- Why profiling shifted the first hardware direction from QK-only attention to dense decode-stage tiled MatVec/MatMul for MLP projection and `lm_head`.
- Why a small FPGA board is suitable for validating selected hardware blocks and programming artifacts but not full-model deployment.

## Main Body

- ONNX Runtime profiling setup and assumptions.
- ONNX export and graph inspection results.
- Prefill/decode-separated latency sweep by context length.
- MatMul category analysis:
  - MatMul is 67.5% of traced phase time.
  - Decode MatMul is 81.1%; prefill MatMul is 53.4%.
  - `mlp_projection + lm_head` is 88.90% of MatMul time.
  - KV-cache is a structural pressure factor, not the only proven bottleneck.
- Theoretical KV-cache size analysis.
- Caveated comparison between theoretical KV-cache growth and measured host process memory growth.
- PyTorch CPU/CUDA host-side reference baselines, explicitly separated from ONNX Runtime results.
- Selection of INT8 tiled/sequential Decode MatVec as the first projection-oriented primitive extension, while preserving QK dot-product as a prior narrow attention primitive.
- SpinalHDL implementation flow and simulation results:
  - fixed `inputDim=16`, `outputDim=4`
  - expected/observed outputs `[-271, 239, 287, 797]`
  - simulation CSV in `paper_assets/tables/decode_matvec_int8_sim.csv`
- Quartus synthesis and DE10-Lite programming evidence:
  - resource/timing tables in `paper_assets/tables/decode_matvec_fpga_resource.csv` and `paper_assets/tables/decode_matvec_fpga_timing.csv`
  - Windows Quartus Programmer configured `de10_lite_decode_matvec.sof` on `10M50DAF484` with `0 errors, 0 warnings`
  - programming success is bitstream configuration evidence only, not numeric board-output validation by itself
- FPGA Decode accelerator architecture sketch: Host/ORT interface, activation buffer, weight tile streamer, INT8 tiled MatVec engine, accumulator, scale/requant unit, optional element-wise/fusion unit, and optional cache-aware interface.
- A bridge paragraph explaining how ONNX-centered bottleneck analysis motivates narrow FPGA block validation without claiming full-model acceleration.
- Limitations and scope boundaries.

## Conclusion

- Findings should stay focused on on-device small language model inference behavior.
- The conclusion should discuss selective decode-stage dense projection acceleration opportunities, not generic AI hardware acceleration claims.
- Do not state that FPGA runs Gemma 3 1B, implements full KV-cache management, or provides measured ONNX Runtime speedup.
