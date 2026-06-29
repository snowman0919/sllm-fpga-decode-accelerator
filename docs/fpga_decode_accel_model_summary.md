# FPGA Decode MatVec Accelerator Model Summary

## Scope

This summary uses the existing ONNX Runtime MatMul category table as profiling evidence. The roofline-style values are architecture estimates for a candidate INT8 tiled MatVec/MatMul datapath, not measured speedup.

## Inputs

- MatMul category CSV: `paper_assets/tables/ort_matmul_category_by_context.csv`
- Top-node shape CSV: `paper_assets/tables/ort_matmul_top_nodes.csv`
- ONNX graph inspection: 7837 nodes, 237 MatMul nodes, cache I/O 52/52, decode cache reuse ready=True

## Profiling Implication

- MatMul share of traced phase time: 67.5%
- Decode MatMul share: 81.1%
- Prefill MatMul share: 53.4%
- `mlp_projection + lm_head` share of MatMul time: 88.90%

The current evidence therefore does not support a MatMul-free direction or a QK-only accelerator story. The first FPGA optimization target should be a decode-stage dense tiled MatVec/MatMul datapath, with QK remaining one primitive among several.

## Candidate Priority

- Highest estimated priorities: mlp_projection, lm_head, attention_qkv_projection
- `lm_head` requires tiled/streaming treatment because the representative vocabulary projection output dimension is very large.
- KV-cache remains a structural memory-pressure factor and should inform stream/cache interfaces, but it is not treated as the single proven bottleneck.

## Generated Tables

- `paper_assets/tables/fpga_decode_accel_candidate_ops.csv`
- `paper_assets/tables/fpga_decode_accel_roofline_estimate.csv`
- `paper_assets/tables/fpga_decode_accel_priority.csv`
