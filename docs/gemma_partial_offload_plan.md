# Gemma-Derived Partial Offload Plan

This plan selects small MatMul tiles from measured Gemma ONNX MatMul categories. It does not patch or accelerate the full Gemma 3 1B graph.

## Selection Rules

- Prefer `mlp_projection` because it has the highest cumulative MatMul contribution in the current ORT profile artifacts.
- Treat `lm_head` as a tile-only candidate; full vocabulary projection over UART is intentionally out of scope.
- Use synthetic deterministic activation/weight values unless a later experiment resolves and records a real external initializer tile.
- Record all results as partial node/tile feasibility evidence only.

## Candidates

## Current Implementation Status

Available now:

- candidate selection from existing ORT MatMul hotspot artifacts
- Gemma-derived small tile ONNX CPU baseline
- FPGA stub/equivalent harness files for packaging and future integration

Not available yet:

- full Gemma ONNX patched execution
- full node replacement correctness
- true ONNX Runtime custom-op DLL execution
- end-to-end Gemma speedup evidence

Any paper use must describe this as Gemma-derived partial tile feasibility only.

### mlp_projection: `/model/layers.4/mlp/up_proj/MatMul`

- input_shape: [1, 128, 1152]
- output_shape: [1, 128, 6912]
- selected_tile_shape: [1,16] x [16,4] projection tile
- replacement_mode: Gemma-derived projection tile micrograph
- claim_boundary: partial node/tile offload feasibility only; no full Gemma ONNX execution or speedup claim

### lm_head: `/lm_head/MatMul`

- input_shape: [1, 128, 1152]
- output_shape: [1, 128, 262144]
- selected_tile_shape: [1,16] x [16,4] vocabulary tile
- replacement_mode: small output tile extraction only
- claim_boundary: partial node/tile offload feasibility only; no full Gemma ONNX execution or speedup claim

### attention_qkv_projection: `/model/layers.19/self_attn/q_proj/MatMul`

- input_shape: [1, 128, 1152]
- output_shape: [1, 128, 1024]
- selected_tile_shape: [1,16] x [16,4] candidate tile
- replacement_mode: candidate only unless a later tile benchmark is logged
- claim_boundary: partial node/tile offload feasibility only; no full Gemma ONNX execution or speedup claim

### attention_output_projection: `/model/layers.8/self_attn/o_proj/MatMul`

- input_shape: [1, 128, 1024]
- output_shape: [1, 128, 1152]
- selected_tile_shape: [1,16] x [16,4] candidate tile
- replacement_mode: candidate only unless a later tile benchmark is logged
- claim_boundary: partial node/tile offload feasibility only; no full Gemma ONNX execution or speedup claim
