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

- Context `128`, decode `1`: prefill `247.375 ms`, decode/token `143.206 ms`, MatMul share prefill `83.1%`, decode `86.0%`.
- Context `128`, decode `2`: prefill `247.375 ms`, decode/token `139.193 ms`, MatMul share prefill `83.1%`, decode `86.3%`.
- Context `128`, decode `4`: prefill `247.375 ms`, decode/token `153.442 ms`, MatMul share prefill `83.1%`, decode `87.6%`.
- Context `128`, decode `8`: prefill `247.375 ms`, decode/token `139.875 ms`, MatMul share prefill `83.1%`, decode `86.4%`.
- Context `512`, decode `1`: prefill `868.861 ms`, decode/token `148.753 ms`, MatMul share prefill `72.0%`, decode `84.3%`.
- Context `512`, decode `2`: prefill `868.861 ms`, decode/token `147.697 ms`, MatMul share prefill `72.0%`, decode `83.7%`.
- Context `512`, decode `4`: prefill `868.861 ms`, decode/token `144.894 ms`, MatMul share prefill `72.0%`, decode `83.8%`.
- Context `512`, decode `8`: prefill `868.861 ms`, decode/token `141.185 ms`, MatMul share prefill `72.0%`, decode `84.6%`.
- Context `1024`, decode `1`: prefill `2195.164 ms`, decode/token `169.562 ms`, MatMul share prefill `56.6%`, decode `78.4%`.
- Context `1024`, decode `2`: prefill `2195.164 ms`, decode/token `160.479 ms`, MatMul share prefill `56.6%`, decode `78.8%`.
- Context `1024`, decode `4`: prefill `2195.164 ms`, decode/token `152.485 ms`, MatMul share prefill `56.6%`, decode `80.5%`.
- Context `1024`, decode `8`: prefill `2195.164 ms`, decode/token `152.230 ms`, MatMul share prefill `56.6%`, decode `82.1%`.
- Context `2048`, decode `1`: prefill `5610.581 ms`, decode/token `205.640 ms`, MatMul share prefill `48.5%`, decode `69.2%`.
- Context `2048`, decode `2`: prefill `5610.581 ms`, decode/token `183.094 ms`, MatMul share prefill `48.5%`, decode `69.9%`.
- Context `2048`, decode `4`: prefill `5610.581 ms`, decode/token `174.665 ms`, MatMul share prefill `48.5%`, decode `72.8%`.
- Context `2048`, decode `8`: prefill `5610.581 ms`, decode/token `173.685 ms`, MatMul share prefill `48.5%`, decode `74.6%`.

## Operator Findings

- Context `128` prefill top ops: `MatMul` 598636us, `SimplifiedLayerNormalization` 25600us, `Mul` 25361us, `Add` 9239us, `Gather` 9184us.
- Context `128` decode 8 top ops: `MatMul` 2747502us, `Mul` 54512us, `Concat` 54128us, `Unsqueeze` 52901us, `Gather` 43141us.
- Context `512` prefill top ops: `MatMul` 1856229us, `Mul` 391870us, `Add` 90495us, `Where` 77777us, `SimplifiedLayerNormalization` 38482us.
- Context `512` decode 8 top ops: `MatMul` 2724704us, `Expand` 68349us, `Concat` 65012us, `Unsqueeze` 50139us, `Mul` 47710us.
- Context `1024` prefill top ops: `MatMul` 3708708us, `Mul` 1395611us, `Add` 473769us, `Where` 399057us, `Tanh` 175264us.
- Context `1024` decode 8 top ops: `MatMul` 2860909us, `Expand` 158675us, `Concat` 92071us, `Unsqueeze` 49213us, `Mul` 46552us.
- Context `2048` prefill top ops: `MatMul` 8150092us, `Mul` 3142071us, `Where` 1978703us, `Add` 1475960us, `Softmax` 469388us.
- Context `2048` decode 8 top ops: `MatMul` 2979900us, `Expand` 414792us, `Concat` 153904us, `FusedMatMul` 95083us, `Unsqueeze` 51445us.

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
