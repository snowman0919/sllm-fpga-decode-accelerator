# ONNX Runtime Context Sweep Report

## Scope

- Runtime: ONNX Runtime `CPUExecutionProvider`.
- Model: `/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx`.
- Context lengths: `128, 512, 1024, 2048`.
- Decode steps: `1, 2, 4, 8`.
- Runs / warmup: `3` / `1`.
- PyTorch baselines are not used as ONNX Runtime measurements.
- FPGA primitive results are not used as end-to-end ONNX Runtime acceleration evidence.

## Cache I/O

- Decode input generation possible: `True`.
- Cache inputs / outputs: `52` / `52`.
- Cache I/O is treated as a decode profiling enabler and memory-pressure candidate, not as proof of a single bottleneck.

## Latency Summary

- Context `128`, decode `1`: prefill `250.475 ms`, decode/token `157.668 ms`, MatMul share prefill `77.1%`, decode `82.2%`.
- Context `128`, decode `2`: prefill `250.475 ms`, decode/token `145.891 ms`, MatMul share prefill `77.1%`, decode `87.1%`.
- Context `128`, decode `4`: prefill `250.475 ms`, decode/token `154.602 ms`, MatMul share prefill `77.1%`, decode `87.4%`.
- Context `128`, decode `8`: prefill `250.475 ms`, decode/token `144.057 ms`, MatMul share prefill `77.1%`, decode `86.7%`.
- Context `512`, decode `1`: prefill `856.681 ms`, decode/token `164.573 ms`, MatMul share prefill `71.7%`, decode `83.7%`.
- Context `512`, decode `2`: prefill `856.681 ms`, decode/token `162.026 ms`, MatMul share prefill `71.7%`, decode `83.0%`.
- Context `512`, decode `4`: prefill `856.681 ms`, decode/token `156.978 ms`, MatMul share prefill `71.7%`, decode `84.2%`.
- Context `512`, decode `8`: prefill `856.681 ms`, decode/token `152.071 ms`, MatMul share prefill `71.7%`, decode `85.1%`.
- Context `1024`, decode `1`: prefill `2330.855 ms`, decode/token `179.041 ms`, MatMul share prefill `55.5%`, decode `82.1%`.
- Context `1024`, decode `2`: prefill `2330.855 ms`, decode/token `189.636 ms`, MatMul share prefill `55.5%`, decode `79.4%`.
- Context `1024`, decode `4`: prefill `2330.855 ms`, decode/token `157.771 ms`, MatMul share prefill `55.5%`, decode `81.6%`.
- Context `1024`, decode `8`: prefill `2330.855 ms`, decode/token `197.350 ms`, MatMul share prefill `55.5%`, decode `81.6%`.
- Context `2048`, decode `1`: prefill `5782.708 ms`, decode/token `198.687 ms`, MatMul share prefill `48.9%`, decode `70.7%`.
- Context `2048`, decode `2`: prefill `5782.708 ms`, decode/token `196.203 ms`, MatMul share prefill `48.9%`, decode `71.5%`.
- Context `2048`, decode `4`: prefill `5782.708 ms`, decode/token `176.494 ms`, MatMul share prefill `48.9%`, decode `72.4%`.
- Context `2048`, decode `8`: prefill `5782.708 ms`, decode/token `170.136 ms`, MatMul share prefill `48.9%`, decode `74.5%`.

## Operator Findings

- Context `128` prefill top ops: `MatMul` 562234us, `SimplifiedLayerNormalization` 67591us, `Mul` 31653us, `Add` 9337us, `Unsqueeze` 7193us.
- Context `128` decode 8 top ops: `MatMul` 2855042us, `Unsqueeze` 49724us, `Mul` 47833us, `Concat` 45483us, `SimplifiedLayerNormalization` 43612us.
- Context `512` prefill top ops: `MatMul` 1823128us, `Mul` 393346us, `Add` 86877us, `Where` 72274us, `SimplifiedLayerNormalization` 48010us.
- Context `512` decode 8 top ops: `MatMul` 2959962us, `Expand` 70177us, `Concat` 66936us, `Unsqueeze` 51750us, `Mul` 48028us.
- Context `1024` prefill top ops: `MatMul` 3865142us, `Mul` 1527319us, `Add` 510774us, `Where` 415062us, `Tanh` 165389us.
- Context `1024` decode 8 top ops: `MatMul` 3694603us, `Expand` 187069us, `Concat` 136009us, `Unsqueeze` 85290us, `FusedMatMul` 63065us.
- Context `2048` prefill top ops: `MatMul` 8460286us, `Mul` 3201130us, `Where` 1985918us, `Add` 1551530us, `Softmax` 492400us.
- Context `2048` decode 8 top ops: `MatMul` 2915126us, `Expand` 414235us, `Concat` 150814us, `FusedMatMul` 91792us, `Unsqueeze` 51256us.

## Interpretation Limits

- These are short synthetic CPU runs and should not be treated as final bottleneck proof.
- MatMul is currently an evidence-backed runtime hotspot candidate because it dominates traced node time in these runs.
- KV-cache is reported as cache I/O and memory-pressure candidate context only.
- No claim is made that FPGA is faster than ONNX Runtime or that DE10-Lite runs Gemma 3 1B.

## Artifacts

- Status JSON: `/home/monad/develop/ai_accel/sllm-fpga-decode-accelerator/onnx_profile/results_onnx_sweep/raw/ort_sweep_status.json`
- Latency CSV: `/home/monad/develop/ai_accel/sllm-fpga-decode-accelerator/paper_assets/tables/ort_context_sweep_latency.csv`
- Operator latency CSV: `/home/monad/develop/ai_accel/sllm-fpga-decode-accelerator/paper_assets/tables/ort_operator_latency_by_context.csv`
- Operator share CSV: `/home/monad/develop/ai_accel/sllm-fpga-decode-accelerator/paper_assets/tables/ort_operator_share_by_context.csv`
- Prefill/decode comparison CSV: `/home/monad/develop/ai_accel/sllm-fpga-decode-accelerator/paper_assets/tables/ort_prefill_decode_comparison.csv`
