# Paper Outline

## Abstract

- Problem statement: decode-stage KV-cache access pressure in on-device sLLM inference.
- Method summary: host-side ONNX Runtime analysis plus FPGA validation of a narrow decode primitive.
- Main contribution: a grounded research workflow rather than an overclaimed full accelerator.

## Introduction

- Why on-device sLLM inference matters.
- Why decode-stage latency matters more than bulk throughput in interactive generation.
- Why KV-cache growth can become a bottleneck as sequence length increases.
- Why a small FPGA board is suitable for validating selected hardware blocks but not full-model deployment.

## Main Body

- ONNX Runtime profiling setup and assumptions.
- Prefill/decode-separated latency sweep by context length.
- Theoretical KV-cache size analysis.
- Comparison between theoretical KV-cache growth and measured host memory growth.
- Selection of an INT8 QK dot-product as the first validation target.
- SpinalHDL implementation flow and simulation results.
- Quartus synthesis and DE10-Lite board validation process.
- A bridge paragraph explaining how host-side decode bottlenecks motivate narrow FPGA block validation without claiming full-model acceleration.
- Limitations and scope boundaries.

## Conclusion

- Findings should stay focused on on-device small language model inference behavior.
- The conclusion should discuss selective decode-stage acceleration opportunities, not generic AI hardware acceleration claims.
