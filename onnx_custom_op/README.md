# FPGA MatVec ONNX Runtime Custom Op

The current repository includes an ORT-equivalent UART bridge harness in `windows/run_ort_fpga_custom_op.py`. That script is intentionally marked `custom_op=false` and `execution_mode=ort_equivalent_uart_bridge` because it does not load a native ONNX Runtime custom-op DLL.

A true custom-op implementation should:

- expose an `FpgaMatVec` op with activation and weight inputs
- validate `input_dim=16` and `output_dim=4` for the first fixed hardware target
- call the same UART packet encoder/decoder documented in `docs/uart_protocol.md`
- return an `int32[4]` result
- record COM port, baudrate, timeout, correctness status, and latency breakdown

Paper text must not report the current stub ONNX graph or equivalent UART harness as custom-op execution evidence. Treat it as invocation-path development only until a DLL is built, loaded by ONNX Runtime, and validated against a CPU reference.
