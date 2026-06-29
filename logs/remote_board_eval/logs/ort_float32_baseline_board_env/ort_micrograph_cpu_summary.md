# ORT MatVec CPU Micrograph Summary

- backend: onnxruntime_cpu
- evidence_type: measured
- interface: CPUExecutionProvider
- graph: matvec_cpu_baseline.onnx
- provider: CPUExecutionProvider
- custom_op: False
- input_dim: 16
- output_dim: 4
- macs: 64
- dtype: float32
- runs: 1000
- correctness_pass: True
- latency_ms_mean: 0.012075
- latency_ms_p50: 0.0115
- latency_ms_p95: 0.0128
- log_dir: logs\ort_float32_baseline_board_env
