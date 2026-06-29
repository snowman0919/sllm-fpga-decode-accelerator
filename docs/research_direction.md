# Research Direction

## Final Research Title

- Korean: ONNX Runtime 기반 온디바이스 소형 언어모델 추론의 병목 분석 및 FPGA 기반 Decode 가속기 구조 설계
- English: Bottleneck Analysis of ONNX Runtime-based On-device Small Language Model Inference and Design of an FPGA-based Decode Accelerator Architecture

## Research Purpose

This project analyzes where bottlenecks actually occur in ONNX Runtime-based on-device small language model inference, then uses that evidence to define a realistic FPGA Decode accelerator architecture. KV-cache is treated as a representative structural source of long-context decode memory pressure, but it is not assumed to be the only bottleneck.

The current DE10-Lite hardware work is not a full accelerator. It is a feasibility validation of the INT8 QK dot-product primitive, which is one core operation inside decode attention.

## Research Questions

- Where do practical bottlenecks arise in ONNX Runtime-based on-device sLLM inference?
- Are the bottlenecks located in model export, graph structure, runtime execution, memory pressure, prefill, decode, or interactions among these factors?
- Which decode-stage primitives are suitable for FPGA hardware implementation after profiling evidence is reviewed?

## Experimental Data Axes

1. ONNX export, graph inspection, and profiling
   - Raw Hugging Face directory inspection
   - ONNX export preflight and export result
   - Graph input/output inspection, including cache-related I/O
   - Operator and tensor-shape inspection
   - ONNX Runtime profiling traces and prefill/decode timing

2. PyTorch CPU/CUDA host-side reference baseline
   - Direct Transformers/PyTorch execution from local `safetensors`
   - Context-length sweep
   - Prefill latency, decode latency, and process RSS snapshots
   - Baseline evidence only; these values are not ONNX Runtime results

3. FPGA primitive 수준 검증
   - Deterministic INT8 Q/K vector generation
   - RTL simulation of INT8 QK dot-product
   - Quartus synthesis and dim sweep
   - DE10-Lite HEX-display validation for the primitive
   - Feasibility evidence only; this is not Gemma 3 1B execution and not end-to-end ONNX Runtime comparison evidence

## Current Data

- PyTorch CPU context sweep summary with decode latency, prefill latency, theoretical KV-cache size, and process RSS observations.
- Deterministic INT8 QK dot-product RTL simulation.
- Quartus synthesis and DE10-Lite validation path for the INT8 QK dot-product primitive.
- Dim-sweep flow for `dim = 16, 32, 64, 128` resource, timing, and estimated latency tables.

## Remaining Data

- Successful ONNX export artifact for the target Gemma 3 1B model.
- ONNX graph inspection outputs showing whether past-KV or cache-style graph I/O exists.
- ONNX Runtime profiling JSON and prefill/decode timing tables.
- ONNX Runtime process memory observations with explicit RSS caveats.
- CPU/CUDA PyTorch host-side reference comparisons aligned to the same prompt lengths and decode-token counts as the ONNX Runtime runs.
- Architecture-level estimate for a future FPGA Decode accelerator that extends beyond QK dot-product to scale, softmax or approximation, V weighted sum, and buffer/stream interfaces.

## Draft Paper Structure

1. Introduction
   - On-device sLLM motivation
   - Why ONNX Runtime deployment needs export, graph, runtime, and memory analysis
   - Why KV-cache is important but not the only assumed bottleneck
   - Research questions and contribution boundary

2. Background
   - Prefill and decode in autoregressive sLLM inference
   - ONNX export and graph execution constraints
   - KV-cache as a long-context decode memory-pressure factor
   - FPGA suitability for selected streaming primitives

3. Method
   - HF model inspection and ONNX export
   - ONNX graph inspection
   - ONNX Runtime profiling design
   - PyTorch CPU/CUDA host-side reference baseline
   - INT8 QK dot-product primitive 수준 검증 flow

4. Results
   - ONNX export and graph findings
   - ONNX Runtime prefill/decode profiling
   - Host-side PyTorch reference baseline
   - Theoretical KV-cache size and process RSS caveats
   - FPGA simulation, synthesis, dim sweep, and DE10-Lite primitive 수준 검증

5. FPGA Decode Accelerator Architecture
   - Primitive selection from profiling results
   - QK dot-product block
   - Scale stage
   - Softmax or approximation stage
   - V weighted-sum stage
   - Buffer and stream interface
   - Integration limits

6. Discussion and Limitations
   - What the data supports
   - What the data does not support
   - Difference between ONNX Runtime profiling and PyTorch reference baselines
   - Difference between primitive 수준 검증 and full-model acceleration

7. Conclusion
   - Bottleneck-analysis findings
   - Hardware-feasible decode primitive summary
   - Next steps for ONNX-centered profiling and FPGA architecture extension

## Interpretation Limits

- FPGA does not implement full KV-cache storage, movement, or management in the current implementation.
- DE10-Lite does not run Gemma 3 1B or a full sLLM.
- FPGA results are not end-to-end ONNX Runtime comparison data.
- RSS change is a process-level memory observation, not a direct KV-cache byte measurement.
- PyTorch CPU/CUDA baselines are host-side reference data, not ONNX Runtime results.
