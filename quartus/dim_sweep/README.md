# Quartus Dim Sweep

This directory is reserved for synthesis-only Quartus projects used in the INT8 QK dot-product dim sweep.

Purpose:

- compile `dim = 16, 32, 64, 128` variants of the INT8 QK dot-product primitive
- collect resource and timing scaling data on the MAX 10 target device
- keep the board-facing `quartus/de10_lite_qk/` flow separate from the synthesis sweep

Important interpretation limit:

- These projects are for primitive-level synthesis experiments only.
- The measured object is the INT8 QK dot-product primitive, not KV-cache storage or a full decode accelerator.
- They do not claim full sLLM execution on FPGA.
- They do not provide end-to-end comparison data against ONNX Runtime or PyTorch.
