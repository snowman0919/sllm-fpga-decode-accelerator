# Y700 ONNX Runtime APK Benchmark Summary

- status: completed
- source: android_apk_onnxruntime_1.27.0
- warmup: 3
- runs: 20
- claim_boundary: Android ONNX Runtime APK micrograph session.run latency only; not whole-model inference.

## Completed Rows

- CPU matvec_cpu_baseline.onnx float_matmul: mean/p50/p95 0.034799 / 0.034349 / 0.038094 ms
- CPU matvec_int8_matmulinteger.onnx matmulinteger: mean/p50/p95 0.054076 / 0.051485 / 0.064391 ms
- CPU gemma_attention_output_projection_1024x1152_float.onnx float_matmul: mean/p50/p95 2.268490 / 1.135730 / 8.917177 ms
- CPU gemma_attention_output_projection_1024x1152_matmulinteger.onnx matmulinteger: mean/p50/p95 1.542326 / 0.737864 / 2.819753 ms
- CPU gemma_lm_head_tile_1152x4096_float.onnx float_matmul: mean/p50/p95 7.573016 / 5.587657 / 16.507326 ms
- CPU gemma_lm_head_tile_1152x4096_matmulinteger.onnx matmulinteger: mean/p50/p95 5.121320 / 3.582136 / 12.761268 ms
- CPU gemma_mlp_projection_1152x6912_float.onnx float_matmul: mean/p50/p95 10.378763 / 10.051172 / 12.064734 ms
- CPU gemma_mlp_projection_1152x6912_matmulinteger.onnx matmulinteger: mean/p50/p95 3.442503 / 3.427839 / 3.557123 ms
- NNAPI matvec_cpu_baseline.onnx float_matmul: mean/p50/p95 0.231219 / 0.197188 / 0.323895 ms
- NNAPI matvec_int8_matmulinteger.onnx matmulinteger: mean/p50/p95 0.169477 / 0.158959 / 0.215813 ms
- NNAPI gemma_attention_output_projection_1024x1152_float.onnx float_matmul: mean/p50/p95 0.969104 / 0.980521 / 1.122414 ms
- NNAPI gemma_attention_output_projection_1024x1152_matmulinteger.onnx matmulinteger: mean/p50/p95 0.575617 / 0.518334 / 0.745722 ms
- NNAPI gemma_lm_head_tile_1152x4096_float.onnx float_matmul: mean/p50/p95 6.127086 / 5.856459 / 7.130895 ms
- NNAPI gemma_lm_head_tile_1152x4096_matmulinteger.onnx matmulinteger: mean/p50/p95 3.853310 / 2.988881 / 6.517250 ms
- NNAPI gemma_mlp_projection_1152x6912_float.onnx float_matmul: mean/p50/p95 9.064807 / 9.390442 / 10.219078 ms
- NNAPI gemma_mlp_projection_1152x6912_matmulinteger.onnx matmulinteger: mean/p50/p95 3.346432 / 3.332890 / 3.443781 ms

## Blocked Rows

- QNN: integration_blocked; ai.onnxruntime.OrtException: Error code - ORT_INVALID_ARGUMENT - message: QNN execution provider is not supported in this build.
