# Paper Outline

## Abstract

- Problem statement: bottleneck location is unclear in ONNX Runtime-based on-device sLLM inference until export, graph structure, runtime execution, memory pressure, prefill, and decode are inspected together.
- Method summary: ONNX export, graph inspection, ONNX Runtime profiling, PyTorch host-side reference baselines, and FPGA validation of a narrow decode primitive.
- Main contribution: a grounded research workflow rather than an overclaimed full accelerator.

## Introduction

- Why on-device sLLM inference matters.
- Why decode-stage latency matters more than bulk throughput in interactive generation.
- Why KV-cache growth is a representative structural source of long-context decode memory pressure.
- Why the study does not assume KV-cache is the only bottleneck before profiling.
- Why a small FPGA board is suitable for validating selected hardware blocks but not full-model deployment.

## Main Body

- ONNX Runtime profiling setup and assumptions.
- ONNX export and graph inspection results.
- Prefill/decode-separated latency sweep by context length.
- Theoretical KV-cache size analysis.
- Caveated comparison between theoretical KV-cache growth and measured host process memory growth.
- PyTorch CPU/CUDA host-side reference baselines, explicitly separated from ONNX Runtime results.
- Selection of an INT8 QK dot-product as the first validation target.
- SpinalHDL implementation flow and simulation results.
- Quartus synthesis and DE10-Lite board validation process.
- FPGA Decode accelerator architecture sketch: QK dot-product, scale, softmax or approximation, V weighted sum, and buffer/stream interfaces.
- A bridge paragraph explaining how ONNX-centered bottleneck analysis motivates narrow FPGA block validation without claiming full-model acceleration.
- Limitations and scope boundaries.

## Conclusion

- Findings should stay focused on on-device small language model inference behavior.
- The conclusion should discuss selective decode-stage acceleration opportunities, not generic AI hardware acceleration claims.
