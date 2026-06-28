# Research Note

The core claim of this project is narrow and testable:

ONNX Runtime-based on-device small language model inference can suffer from bottlenecks that appear in model export, graph structure, runtime execution, memory pressure, prefill, decode, or interactions among these layers. KV-cache is a representative structural factor for long-context decode memory pressure, but this project does not assume KV-cache is the only bottleneck before profiling evidence is reviewed.

This repository studies that problem in two linked but separate layers:

1. ONNX-centered host analysis: export, graph inspection, ONNX Runtime profiling, and PyTorch host-side reference baselines.
2. FPGA validation of small deterministic hardware blocks that represent hardware-feasible decode-stage attention primitives.

The FPGA is not proposed as a full replacement for GPU or NPU inference. The DE10-Lite is used only to validate selected streaming operations, beginning with an INT8 QK dot-product primitive. It does not implement full KV-cache management, run Gemma 3 1B, or provide end-to-end ONNX Runtime comparison data.

This framing matters because the board resource budget is far below what would be needed for a complete modern small language model deployment. The value of the FPGA work here is architectural isolation, determinism, and visibility into specific decode-stage dataflow patterns. A later FPGA Decode accelerator architecture may extend the validated primitive toward QK dot-product, scale, softmax or approximation, V weighted sum, and buffer/stream interfaces.
