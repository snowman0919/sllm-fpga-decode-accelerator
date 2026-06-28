# Research Note

The core claim of this project is narrow and testable:

ONNX Runtime-based on-device small language model inference can suffer from token-by-token decode bottlenecks because KV-cache tensors are repeatedly accessed as context length grows. The longer the active sequence becomes, the more decode-stage work depends on streaming previously generated key and value data.

This repository studies that problem in two linked but separate layers:

1. Host-side profiling with ONNX Runtime and Gemma 3 1B-derived ONNX artifacts.
2. FPGA validation of small deterministic hardware blocks that represent a subset of decode-stage attention computation.

The FPGA is not proposed as a full replacement for GPU or NPU inference. The DE10-Lite is used only to validate selected streaming operations, beginning with an INT8 QK dot-product primitive and later expanding only if measurements justify it.

This framing matters because the board resource budget is far below what would be needed for a complete modern small language model deployment. The value of the FPGA work here is architectural isolation, determinism, and visibility into specific decode-stage dataflow patterns, not end-to-end model execution.
