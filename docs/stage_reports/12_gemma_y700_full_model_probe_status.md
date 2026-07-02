# 12단계 보강: Y700 full Gemma ONNX probe 결과

## 목적

논문 초반에서 Gemma 3 1B를 문제 설정의 기준 모델로 언급하지만, 본문 실험 근거가 representative projection micrograph 중심으로 남아 있다는 약점을 보완하기 위해 Lenovo Y700에서 full Gemma ONNX graph의 실행 가능성을 별도로 확인했다.

## 로컬 artifact

- HF 원본 모델: `/home/monad/develop/ai_accel/gemma3-1B`
- ONNX export: `/home/monad/develop/ai_accel/gemma3-1B-onnx`
- ONNX graph: `model.onnx`, 1,468,819 bytes
- ONNX external data: `model.onnx_data`, 5,207,504,384 bytes
- 주요 config: hidden size 1152, intermediate size 6912, layers 26, KV heads 1, head dim 256, vocab size 262144

ONNX graph는 external data를 사용하는 full Gemma graph이며, 입력은 `input_ids`, `attention_mask`, 26개 layer의 key/value past cache로 구성된다. Export log에는 opset 17 경고와 ONNX validation tolerance warning이 남았지만, export 자체는 완료되었고 graph inspection에서 past/present cache 입출력이 확인되었다.

## Android benchmark app 보강

`android/y700_ort_benchmark` 앱에 full Gemma probe를 추가했다.

- probe 이름: `gemma3-1B-onnx/full_decode_step_probe`
- 실행 provider: ONNX Runtime Android CPU EP
- 입력: batch 1, sequence length 1, artificial past length 1
- 출력: logits `[1, 1, 262144]` 및 present KV cache
- model path: 앱 내부 파일 디렉터리의 `gemma3-1B-onnx/model.onnx`
- external data path: 같은 디렉터리의 `gemma3-1B-onnx/model.onnx_data`

처음에는 `/sdcard/Android/data/...`에 `adb push`한 파일이 앱 프로세스에서 `artifact_missing`으로 기록되었다. Android 15 scoped storage와 shell 소유 파일 접근 문제로 판단하여, `/data/local/tmp`를 거쳐 `run-as edu.dimigo.y700ort`로 앱 내부 `files/gemma3-1B-onnx`에 복사했다. 이후 앱 UID 소유 파일로 probe가 정상 완료되었다.

## Y700 실행 결과

| 항목 | 값 |
| --- | ---: |
| Device | Lenovo Y700 `TB320FC` |
| Platform | `taro`, Android 15 |
| ONNX Runtime Android providers | `[CPU, NNAPI, XNNPACK, WEBGPU]` |
| Status | completed |
| Session load | 30001.342385 ms |
| Decode-like step, runs 1 | 430.475885 ms |
| Warmup | 0 |
| Input shape | `input_ids [1,1]`, `attention_mask [1,2]` |
| Past cache shape | 26 layers x key/value `[1,1,1,256]` |

이 결과는 full Gemma ONNX graph가 Y700 ONNX Runtime CPU EP에서 로드되고 단일 decode-like step을 실행할 수 있음을 보여준다. 그러나 runs 1 조건의 feasibility probe이며, tokenizer를 포함한 full text generation throughput이나 안정적인 latency benchmark로 해석하지 않는다.

## 산출물

- 요약 CSV: `paper_assets/tables/y700_full_gemma_probe.csv`
- Android raw CSV/JSON: `logs/y700_full_gemma_probe/pulled_y700_onnx_runtime/`
- 장치 상태 로그: `logs/y700_full_gemma_probe/device_state_after_probe.txt`
- artifact 위치 로그: `logs/y700_full_gemma_probe/artifact_locations.txt`
- export log: `logs/gemma_export_y700_probe_20260702_103751.log`
- ONNX SHA-256:
  - `logs/gemma_full_onnx_model_sha256.txt`
  - `logs/gemma_full_onnx_data_sha256.txt`

## 논문 반영 원칙

- “Y700에서 full Gemma ONNX graph의 CPU EP 단일 decode-like step probe를 수행했다”로 쓴다.
- session load와 단일 step latency를 분리한다.
- full generation throughput, ONNX Runtime QNN EP, FPGA 가속, 전체 실행 성능 개선 근거로 사용하지 않는다.
- 기존 projection micrograph 결과는 dense projection primitive 분석 근거로 유지하고, full Gemma probe는 모델 단위 실행 가능성 보강 근거로 분리한다.
