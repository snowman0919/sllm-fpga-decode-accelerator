# ONNX Bottleneck Report

## Export Status

- Export success: `True`
- Fallback used: `False`
- Final task: `text-generation-with-past`
- Final model path: `/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx`

## Graph Inspection

- Model path: `/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx`
- External data: `True`
- Total model bytes: `15658526302`
- Inputs / outputs: `54` / `53`
- Cache I/O present: `True`
- Cache input count: `52`
- Cache output count: `52`
- Symbolic shapes present: `True`
- Top operators: `Constant`=2738, `Unsqueeze`=828, `Mul`=766, `Shape`=401, `Gather`=346, `Add`=342, `Concat`=319, `Cast`=280, `MatMul`=237, `Reshape`=214

## ORT Profiling

- CPU attempt status: `ok`
- CPU session init time: `1.8986423619999186`
- CPU prefill latency: `0.18080204000034428`
- CPU decode average latency: `0.13351462000036918`
- CPU decode mode: `with_past_kv_cache`
- Top traced runtime ops: `MatMul`=349520.0us/633 calls, `SimplifiedLayerNormalization`=18728.0us/471 calls, `Mul`=8292.0us/1020 calls, `Tanh`=7469.0us/78 calls, `Unsqueeze`=6248.0us/1377 calls
- Profiling blocked: `False`
- CUDA attempt status: `skipped`
- CUDA note: CUDAExecutionProvider not available in this onnxruntime build.

## Current Bottleneck Candidates

- The model uses external ONNX data, so model packaging and model-loading I/O are practical bottleneck candidates.
- Cache-related graph I/O exists, so decode-stage cache handling is measurable and remains a candidate rather than an assumption.
- High-frequency graph operators include Constant (2738), Unsqueeze (828), Mul (766), Shape (401), Gather (346).
- Session initialization on CPU is measurable (1.899s) and is one host-side overhead candidate.
- Prefill latency on CPU is measurable (0.181s) and is a direct runtime bottleneck candidate.
- Per-step decode latency on CPU is measurable (0.134s average for this short run).
- In the ORT node trace, MatMul has the largest accumulated duration (349520.0 us across 633 node executions), so dense linear algebra is an immediate runtime hotspot candidate.

## Still Unconfirmed

- Whole-model bottleneck ranking across export, graph structure, runtime, memory pressure, prefill, and decode is not yet fully resolved from this minimal run.
- Cache-related memory pressure remains a candidate factor, but not a confirmed sole bottleneck.
- CUDA-side ONNX Runtime behavior should not be inferred if the CUDA provider was unavailable or failed to initialize.

## Evidence Positioning

- PyTorch CPU/CUDA context sweep data remains a host-side reference baseline and is not reported here as ONNX Runtime profiling.
- FPGA results remain primitive-level validation for the INT8 QK dot-product block and are not used here as end-to-end ONNX Runtime acceleration evidence.
