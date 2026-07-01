# 3단계 모델 및 Micrograph Manifest 중간 보고

## 생성한 산출물

- `paper_assets/tables/model_artifact_manifest.csv`
- `paper_assets/tables/y700_onnx_runtime_baseline.csv`
- 생성 스크립트: `scripts/build_final_analysis_tables.py`

## 현재 ONNX micrograph 상태

`onnx_micrographs/` 아래 ONNX 파일을 직접 inspection하여 manifest를 생성했다.

| 파일 | 실제 op | 실제 shape | dtype | 해석 |
| --- | --- | --- | --- | --- |
| `matvec_cpu_baseline.onnx` | MatMul | `[1,16] x [16,4] -> [1,4]` | FLOAT | 16x4 float32 synthetic micrograph |
| `matvec_int8_matmulinteger.onnx` | MatMulInteger | `[1,16] x [16,4] -> [1,4]` | INT8 -> INT32 | 16x4 integer synthetic micrograph |
| `gemma_mlp_projection_tile_cpu.onnx` | MatMul | `[1,16] x [16,4] -> [1,4]` | FLOAT | 이름은 Gemma tile이지만 현재 실제 graph는 16x4 synthetic micrograph |
| `gemma_lm_head_tile_cpu.onnx` | MatMul | `[1,16] x [16,4] -> [1,4]` | FLOAT | 이름은 Gemma tile이지만 현재 실제 graph는 16x4 synthetic micrograph |
| `gemma_mlp_projection_1152x6912_float.onnx` | MatMul | `[1,1152] x [1152,6912] -> [1,6912]` | FLOAT | Gemma MLP projection representative graph |
| `gemma_mlp_projection_1152x6912_matmulinteger.onnx` | MatMulInteger | `[1,1152] x [1152,6912] -> [1,6912]` | INT8 -> INT32 | Gemma MLP projection integer representative graph |
| `gemma_lm_head_tile_1152x4096_float.onnx` | MatMul | `[1,1152] x [1152,4096] -> [1,4096]` | FLOAT | lm_head output tile representative graph |
| `gemma_lm_head_tile_1152x4096_matmulinteger.onnx` | MatMulInteger | `[1,1152] x [1152,4096] -> [1,4096]` | INT8 -> INT32 | lm_head output tile integer representative graph |
| `gemma_attention_output_projection_1024x1152_float.onnx` | MatMul | `[1,1024] x [1024,1152] -> [1,1152]` | FLOAT | attention output projection representative graph |
| `gemma_attention_output_projection_1024x1152_matmulinteger.onnx` | MatMulInteger | `[1,1024] x [1024,1152] -> [1,1152]` | INT8 -> INT32 | attention output projection integer representative graph |

## 비평서 대응

비평서에서 "16x4 primitive를 실제 Gemma projection으로 일반화하면 안 된다"는 지적이 있었다. 이에 따라 manifest는 파일명보다 graph inspection 결과를 우선하도록 만들었다. 최종 원고에서는 `gemma_*_tile_cpu.onnx`라는 파일명을 근거로 실제 1152차원 projection graph라고 쓰지 않는다.

## Y700 baseline table 상태

`paper_assets/tables/y700_onnx_runtime_baseline.csv`에는 Android APK benchmark에서 확보한 CPU/NNAPI latency와 QNN integration blocked 행이 들어 있다. 최종 원고에서는 representative micrograph latency로만 해석하고 Gemma 전체 모델 실행 결과로 쓰지 않는다.

장치 연결 후 `scripts/y700_run_onnx_micrographs.py`가 성공하면 이 표는 CPU/NNAPI/QNN provider별 attempt 또는 completed 상태를 담도록 갱신한다.

## 남은 작업

1. Android에서 메모리/시간이 허용되는 shape부터 실행한다.
2. Gemma 전체 모델 ONNX 실행 가능 여부를 별도 manifest에 기록한다.
3. quantized/QDQ full graph가 확보되면 micrograph와 분리해 manifest에 추가한다.

## Claim boundary

현재 manifest는 ONNX 파일 존재와 graph 구조를 증명한다. Android/Y700 실행 성공, Gemma 전체 모델 실행, optimized/quantized ONNX 성공을 증명하지 않는다.
