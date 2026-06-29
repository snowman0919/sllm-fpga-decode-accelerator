# Gemma ONNX Patch Notes

No full Gemma ONNX graph patch is claimed by the current artifact generator.

The implemented path creates Gemma-derived tile micrographs and candidate
tables from observed MatMul hotspots. A direct one-node graph patch should only
be promoted to a result after shape inference passes, ONNX Runtime can load the
patched graph with the intended custom op or explicit stub behavior, and a
correctness harness compares the patched node output against a CPU reference.
Until those conditions are met, full-graph patching remains future work.

`onnx_micrographs/matvec_fpga_custom_stub.onnx` and the Gemma `*_fpga_stub.onnx`
files are not evidence of true custom-op execution. They are placeholders for
the graph shape and packaging flow only. The current executable evidence is
limited to CPUExecutionProvider micrographs and optional UART-equivalent harness
logs outside ONNX Runtime.
