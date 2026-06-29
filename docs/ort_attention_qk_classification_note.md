# Attention QK MatMul Fallback Classification Note

## Scope

This note supplements the ORT profile event name/path classification where `attention_qk_score` appeared as `0.00%`.
The fallback analysis inspects the exported ONNX graph directly, using MatMul node names, input/output names, and immediate parent/child operators.

## Result

- Self-attention internal MatMul nodes inspected: `156`.
- Confirmed `attention_qk_score` graph nodes: `26`.
- Confirmed `attention_v_weighted_sum` graph nodes: `26`.
- Unconfirmed candidate nodes: `104`.
- Output table: `paper_assets/tables/ort_attention_matmul_candidates.csv`.

## Interpretation Boundary

The graph-level fallback confirms that QK-score-like MatMul nodes exist in the exported ONNX graph.
It does not assign runtime share to those nodes when ORT profiling reports optimized or fused events under different operator names.
Therefore the earlier `attention_qk_score` runtime category should be read as "not confirmed by the conservative profile-event classifier," not as absence of QK score computation.
