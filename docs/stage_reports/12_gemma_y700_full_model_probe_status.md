# 12단계 보강: Y700 full Gemma ONNX probe 상태

## 목적

논문 초반에서 Gemma 3 1B를 문제 설정의 기준 모델로 언급하지만, 본문 실험 근거가 representative projection micrograph 중심으로 남아 있다는 약점을 보완하기 위해 Lenovo Y700에서 full Gemma ONNX graph의 실행 가능성을 별도로 확인한다.

## 로컬 artifact 확인

- HF 원본 모델: `/home/monad/develop/ai_accel/gemma3-1B`
- ONNX export: `/home/monad/develop/ai_accel/gemma3-1B-onnx`
- ONNX graph: `model.onnx`, 1.4 MB
- ONNX external data: `model.onnx_data`, 15.6 GB
- 주요 config: hidden size 1152, intermediate size 6912, layers 26, KV heads 1, head dim 256, vocab size 262144

ONNX graph는 external data를 사용하는 full Gemma graph이며, 입력은 `input_ids`, `attention_mask`, 26개 layer의 key/value past cache로 구성된다. 따라서 기존 micrograph와 달리 full graph session load 비용과 weight memory footprint가 함께 들어간다.

## Android benchmark app 보강

`android/y700_ort_benchmark` 앱에 full Gemma probe를 추가했다.

- probe 이름: `gemma3-1B-onnx/full_decode_step_probe`
- 실행 provider: ONNX Runtime Android CPU EP
- 입력: batch 1, sequence length 1, artificial past length 1
- 출력: logits `[1, 1, 262144]` 및 present KV cache
- model path: 앱 외부 파일 디렉터리의 `gemma3-1B-onnx/model.onnx`
- external data path: 같은 디렉터리의 `gemma3-1B-onnx/model.onnx_data`

파일이 없으면 `artifact_missing`으로 기록하고, 파일이 있으면 session load 시간과 1회 decode-like step latency를 분리해 기록한다. 이 probe는 full text generation benchmark가 아니라 full Gemma ONNX graph가 Y700 ONNX Runtime에서 로드 및 단일 step 실행 가능한지 확인하는 실행 가능성 실험이다.

## 현재 blocker

현재 `ssh win` 대상인 Windows Pocket4가 Tailscale/SSH에서 응답하지 않는다.

- SSH config host `win`은 `100.117.248.33`으로 해석된다.
- `ssh win`의 단순 PowerShell 명령도 timeout된다.
- `nc -vz -w 3 100.117.248.33 22`는 timeout된다.
- `tailscale status`에서는 `pocket4`가 `offline, last seen 43m ago`로 표시되었다.
- 따라서 Y700로 APK 설치, 15.6GB external data push, benchmark 실행은 아직 수행하지 못했다.

## 재접속 후 실행 절차

Windows Pocket4가 다시 연결되면 다음 순서로 진행한다.

1. APK 전달 및 설치

```bash
scp build/y700_ort_benchmark-signed.apk win:C:/Users/dbsgu/Dev/y700_ort_benchmark-signed.apk
ssh win "powershell -NoProfile -Command \"adb install --no-streaming -r -g C:\\Users\\dbsgu\\Dev\\y700_ort_benchmark-signed.apk\""
```

2. Gemma ONNX artifact 전달

```bash
scp /home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx win:C:/Users/dbsgu/Dev/gemma3-1B-onnx/model.onnx
scp /home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx_data win:C:/Users/dbsgu/Dev/gemma3-1B-onnx/model.onnx_data
ssh win "powershell -NoProfile -Command \"adb shell mkdir -p /sdcard/Android/data/edu.dimigo.y700ort/files/gemma3-1B-onnx; adb push C:\\Users\\dbsgu\\Dev\\gemma3-1B-onnx\\model.onnx /sdcard/Android/data/edu.dimigo.y700ort/files/gemma3-1B-onnx/model.onnx; adb push C:\\Users\\dbsgu\\Dev\\gemma3-1B-onnx\\model.onnx_data /sdcard/Android/data/edu.dimigo.y700ort/files/gemma3-1B-onnx/model.onnx_data\""
```

3. 실행 및 결과 회수

```bash
ssh win "powershell -NoProfile -Command \"adb shell am start -n edu.dimigo.y700ort/.MainActivity; Start-Sleep -Seconds 60; adb pull /sdcard/Android/data/edu.dimigo.y700ort/files/y700_onnx_runtime logs\\y700_full_gemma_probe\""
```

## 논문 반영 원칙

- 성공 시: “Y700에서 full Gemma ONNX graph의 CPU EP 단일 decode-like step probe를 수행했다”로만 쓴다.
- 실패 시: 실패 단계(session load OOM, external data load failure, run failure 등)를 그대로 기록한다.
- 이 probe는 전체 text generation 처리량, ONNX Runtime QNN EP, FPGA 가속, 전체 실행 성능 개선 근거로 사용하지 않는다.
- 기존 projection micrograph 결과는 dense projection primitive 분석 근거로 유지하고, full Gemma probe는 모델 단위 실행 가능성 보강 근거로 분리한다.
