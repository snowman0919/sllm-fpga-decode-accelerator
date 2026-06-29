# Paper Outline

## Draft Target

Final draft file:

```text
ONNX_Runtime_온디바이스_sLLM_FPGA_Decode_가속기_논문초안.md
```

Journal-format draft file:

```text
ONNX_Runtime_온디바이스_sLLM_FPGA_Decode_가속기_논문양식본.md
```

The draft is a submission/shareable Markdown manuscript built from existing repository artifacts. It does not introduce new experiments, recompilation, or changed numeric results.

## Claim Boundary

- The study analyzes ONNX Runtime-based on-device sLLM bottlenecks and connects the result to an FPGA Decode accelerator architecture sketch.
- The strongest measured ONNX Runtime CPUExecutionProvider hotspot is MatMul-centered dense linear algebra.
- Reported core numbers:
  - MatMul share of traced prefill + decode phase time: `67.5%`
  - Decode MatMul share: `81.1%`
  - Prefill MatMul share: `53.4%`
  - `mlp_projection + lm_head` share of MatMul time: `88.90%`
- KV-cache is treated as a representative structural memory-pressure factor, not as the only bottleneck.
- FPGA evidence is limited to primitive-level INT8 Decode MatVec validation and DE10-Lite bitstream configuration.
- The draft does not claim complete Gemma 3 1B execution on DE10-Lite, full KV-cache implementation, or end-to-end ONNX Runtime speedup.
- Roofline/model values are design estimates, not measured acceleration.
- BitNet b1.58 and MatMul-free LM are discussed only as related work; the project does not implement a MatMul-free model.

## Final Manuscript Structure

1. Title
   - Korean title
   - English title
2. Author information
   - 최윤혁
   - ORCID
   - 한국디지털미디어고등학교
   - English name and affiliation
3. Korean Abstract and Keywords
4. English Abstract and Keywords
5. Introduction
   - 1.1 연구 배경 및 온디바이스 조건 정의
   - 1.2 온디바이스 sLLM 추론의 병목 문제
   - 1.3 ONNX Runtime 기반 분석의 필요성
   - 1.4 연구 목표와 기여
6. Background and Related Work
   - 2.1 Prefill과 Decode
   - 2.2 KV-cache와 long-context memory pressure
   - 2.3 ONNX Runtime과 graph-based deployment
   - 2.4 MatMul 중심 LLM 연산 병목
   - 2.5 저정밀 및 MatMul-efficient 연구와 본 연구의 차이
7. Method
   - 3.1 전체 실험 흐름
   - 3.2 ONNX export 및 graph inspection
   - 3.3 ORT profiling setup
   - 3.4 MatMul category classification 방법
   - 3.5 FPGA Decode MatVec primitive 설계 방법
   - 3.6 evidence layer 구분
8. Experimental Results
   - Results and interpretation are separated.
   - Tables include explicit source columns.
9. Discussion
   - KV-cache is not treated as the sole explanation.
   - Decode MatMul dominance is interpreted through dense projection repetition.
   - MLP projection and `lm_head` motivate tiled MatVec/MatMul rather than QK-only hardware.
   - DE10-Lite evidence is limited to primitive validation and programming success.
   - Add a requirements bridge from ONNX/ORT observations to FPGA accelerator requirements.
10. FPGA Decode Accelerator Architecture Proposal
    - 6.1 설계 목표와 비목표
    - 6.2 Host/ORT offload boundary
    - 6.3 Decode tiled MatVec dataflow
    - 6.4 Weight streaming and tiling strategy
    - 6.5 `lm_head` 처리 전략
    - 6.6 Cache-aware interface의 역할
    - 6.7 현재 primitive 검증과 future accelerator의 차이
11. Limitations
    - ORT CPUExecutionProvider scope
    - Synthetic/context sweep scope
    - MatMul category classification scope
    - PyTorch baseline and ORT profiling separation
    - FPGA primitive-level validation scope
    - Board programming and numeric board-output validation separation
    - Roofline/design estimate and measured result separation
12. Conclusion
13. References
14. Appendices
    - A. Artifact inventory
    - B. Reproducibility commands
    - C. Claim boundary checklist

## Required Tables

| Table | Caption | Main source |
| ---: | --- | --- |
| 1 | ONNX graph inspection 요약 | `onnx_profile/results_onnx/raw/onnx_graph_inspection.json` |
| 2 | ONNX Runtime profiling 설정 및 산출물 | `docs/onnx_runtime_sweep_report.md`, `paper_assets/tables/ort_context_sweep_latency.csv` |
| 3 | ONNX Runtime MatMul phase 비중 | `docs/current_bottleneck_implications.md` |
| 4 | Long-decode ONNX Runtime CPUExecutionProvider sweep 요약 | `paper_assets/tables/ort_long_decode_sweep_latency.csv`, `paper_assets/tables/ort_long_decode_operator_share.csv` |
| 5 | MatMul category별 누적 시간과 비중 | `paper_assets/tables/ort_matmul_category_by_context.csv`, `docs/ort_matmul_hotspot_analysis.md` |
| 6 | INT8 Decode MatVec RTL simulation 결과 | `paper_assets/tables/decode_matvec_int8_sim.csv` |
| 7 | Decode MatVec demo Quartus resource 요약 | `paper_assets/tables/decode_matvec_fpga_resource.csv` |
| 8 | Decode MatVec demo timing 및 board programming 요약 | `paper_assets/tables/decode_matvec_fpga_timing.csv`, `paper_assets/tables/decode_matvec_board_validation.csv` |
| 9 | 실험 환경 요약 | `paper_assets/tables/experiment_environment.csv`, `docs/experiment_environment.md` |
| 10 | ONNX/ORT 병목 분석으로부터 도출한 FPGA 설계 요구사항 | `docs/current_bottleneck_implications.md`, `docs/ort_long_decode_sweep_report.md`, `docs/fpga_decode_accelerator_optimization_plan.md` |
| 11 | 제안 FPGA Decode 가속기 구조의 구성요소와 역할 | `docs/current_bottleneck_implications.md`, `docs/fpga_decode_accelerator_optimization_plan.md` |
| 12 | FPGA Decode accelerator roofline/design estimate 요약 | `paper_assets/tables/fpga_decode_accel_roofline_estimate.csv` |

## Required Figures

| Figure | Caption | Main source |
| ---: | --- | --- |
| 1 | 연구 전체 흐름도 | `paper_assets/figures/research_flow.png`, `docs/current_bottleneck_implications.md` |
| 2 | ONNX Runtime MatMul phase 비중 | `paper_assets/figures/ort_matmul_phase_share.png`, `docs/current_bottleneck_implications.md` |
| 3 | Long-decode ORT CPU MatMul share | `paper_assets/figures/ort_long_decode_matmul_share.png`, `paper_assets/tables/ort_long_decode_operator_share.csv` |
| 4 | Long-decode ORT CPU shape-related op share | `paper_assets/figures/ort_long_decode_shape_ops_share.png`, `paper_assets/tables/ort_long_decode_operator_share.csv` |
| 5 | MatMul category breakdown | `paper_assets/figures/ort_matmul_category_breakdown.png`, `paper_assets/tables/ort_matmul_category_by_context.csv` |
| 6 | FPGA Decode tiled MatVec/MatMul accelerator architecture | `paper_assets/figures/fpga_decode_accelerator_architecture.png`, `docs/fpga_decode_accelerator_optimization_plan.md` |

HWP/PDF insertion metadata is tracked in `paper_assets/figures/figure_index.csv` and `paper_assets/figures/figure_index.md`.

## Paper-facing Artifacts

- `paper_assets/tables/ort_context_sweep_latency.csv`
- `paper_assets/tables/ort_operator_share_by_context.csv`
- `paper_assets/tables/ort_prefill_decode_comparison.csv`
- `paper_assets/tables/ort_long_decode_sweep_latency.csv`
- `paper_assets/tables/ort_long_decode_operator_share.csv`
- `paper_assets/tables/ort_matmul_category_by_context.csv`
- `paper_assets/tables/ort_matmul_top_nodes.csv`
- `paper_assets/tables/ort_attention_matmul_candidates.csv`
- `paper_assets/tables/fpga_decode_accel_candidate_ops.csv`
- `paper_assets/tables/fpga_decode_accel_roofline_estimate.csv`
- `paper_assets/tables/fpga_decode_accel_priority.csv`
- `paper_assets/tables/decode_matvec_int8_sim.csv`
- `paper_assets/tables/decode_matvec_fpga_resource.csv`
- `paper_assets/tables/decode_matvec_fpga_timing.csv`
- `paper_assets/tables/decode_matvec_board_validation.csv`
- `paper_assets/tables/experiment_environment.csv`
- `paper_assets/figures/research_flow.png`
- `paper_assets/figures/ort_matmul_phase_share.png`
- `paper_assets/figures/ort_long_decode_matmul_share.png`
- `paper_assets/figures/ort_long_decode_shape_ops_share.png`
- `paper_assets/figures/ort_matmul_category_breakdown.png`
- `paper_assets/figures/fpga_decode_accelerator_architecture.png`
- `paper_assets/figures/figure_index.csv`
- `paper_assets/figures/figure_index.md`
- `docs/ort_long_decode_sweep_report.md`
- `docs/ort_attention_qk_classification_note.md`
- `docs/experiment_environment.md`
