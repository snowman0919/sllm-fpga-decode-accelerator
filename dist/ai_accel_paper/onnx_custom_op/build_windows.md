# Windows Custom Op Build Notes

The native custom-op path is a future implementation step. A verified build should use the ONNX Runtime custom-op C/C++ API and link against the same ONNX Runtime version used by the Windows test environment.

Expected high-level flow:

```powershell
cmake -S onnx_custom_op -B build\onnx_custom_op -A x64 -DONNXRUNTIME_ROOT=C:\path\to\onnxruntime
cmake --build build\onnx_custom_op --config Release
```

The resulting DLL should be loaded by a dedicated runner that records `custom_op=true`. Until that runner exists and passes correctness checks, use `windows/run_ort_fpga_custom_op.py` only as a graph-level equivalent UART harness.
