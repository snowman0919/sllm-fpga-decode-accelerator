# ONNX Runtime Long-Decode Sweep Report

## Scope

- Runtime provider: ONNX Runtime `CPUExecutionProvider`.
- Context lengths: `128`, `512`, `2048`.
- Decode steps: `8`, `32`, `64`, `128`, `256`.
- Runs / warmup: `1` / `0`.
- This sweep extends the earlier decode-step <= 8 artifact and is still a CPUExecutionProvider host-side profile.
- No FPGA recompilation, custom operator integration, or end-to-end acceleration measurement is included.

## Summary Table

| context | decode steps | decode/token ms | MatMul share | shape-op share | Expand share | Concat share | Unsqueeze share |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 128 | 8 | 139.651 | 85.76% | 4.76% | 1.07% | 2.08% | 1.62% |
| 128 | 32 | 136.898 | 87.03% | 3.82% | 0.79% | 1.44% | 1.59% |
| 128 | 64 | 136.518 | 86.24% | 4.23% | 0.97% | 1.53% | 1.73% |
| 128 | 128 | 137.689 | 86.78% | 4.04% | 0.95% | 1.49% | 1.59% |
| 128 | 256 | 140.496 | 86.57% | 4.35% | 1.17% | 1.61% | 1.57% |
| 512 | 8 | 249.288 | 81.32% | 9.20% | 5.24% | 2.39% | 1.57% |
| 512 | 32 | 214.922 | 84.51% | 6.84% | 3.45% | 1.73% | 1.65% |
| 512 | 64 | 204.436 | 86.47% | 5.67% | 2.42% | 1.81% | 1.43% |
| 512 | 128 | 201.547 | 87.29% | 5.11% | 1.83% | 1.94% | 1.34% |
| 512 | 256 | 203.674 | 83.55% | 7.29% | 3.09% | 2.36% | 1.85% |
| 2048 | 8 | 225.187 | 78.33% | 12.01% | 6.87% | 4.13% | 1.01% |
| 2048 | 32 | 286.634 | 72.51% | 17.15% | 12.08% | 3.63% | 1.43% |
| 2048 | 64 | 179.428 | 75.34% | 14.55% | 8.79% | 4.45% | 1.31% |
| 2048 | 128 | 174.435 | 74.66% | 15.32% | 9.12% | 4.88% | 1.32% |
| 2048 | 256 | 240.789 | 72.91% | 17.71% | 10.74% | 5.70% | 1.27% |

## Interpretation

- MatMul remains the largest traced decode operator group across all long-decode points.
- At context 2048, MatMul share decreases from `78.33%` at 8 decode steps to `72.91%` at 256 decode steps.
- At context 2048 and 256 decode steps, `Expand + Concat + Unsqueeze` accounts for `17.71%` of traced decode node time.
- This supports treating KV-cache and shape-related graph work as a growing long-decode pressure source, while not reducing the bottleneck to KV-cache alone.
- Per-token latency is noisy with one run, so trends are reported as host-side evidence rather than a statistically final latency model.

## Artifacts

- `paper_assets/tables/ort_long_decode_sweep_latency.csv`
- `paper_assets/tables/ort_long_decode_operator_share.csv`
- `paper_assets/figures/ort_long_decode_matmul_share.png`
- `paper_assets/figures/ort_long_decode_shape_ops_share.png`
