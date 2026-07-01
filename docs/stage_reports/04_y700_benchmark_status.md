# 04단계 Lenovo Y700 ONNX Runtime Benchmark 보고

작성 시점: 2026-07-01

## 결론

Lenovo Y700(TB320FC)에서 ONNX Runtime Android APK 기반 representative micrograph benchmark를 수행했다. CPU EP와 NNAPI EP는 실행되었고, QNN EP는 사용한 `onnxruntime-android:1.27.0` AAR build에서 지원되지 않아 `integration_blocked`로 기록했다.

## 실행 경로

```bash
python3 scripts/build_y700_ort_benchmark_apk.py
adb install --no-streaming -r -g y700_ort_benchmark-signed.apk
adb shell am start -n edu.dimigo.y700ort/.MainActivity
adb pull /sdcard/Android/data/edu.dimigo.y700ort/files/y700_onnx_runtime
```

## 로그 산출물

- `logs/y700_onnx_runtime/device_info.json`
- `logs/y700_onnx_runtime/runtime_env.md`
- `logs/y700_onnx_runtime/benchmark_y700_ort_android.csv`
- `logs/y700_onnx_runtime/benchmark_y700_ort_android.json`
- `logs/y700_onnx_runtime/benchmark_summary.json`
- `logs/y700_onnx_runtime/benchmark_summary.md`

## 주요 결과

조건: ONNX Runtime Android 1.27.0, APK asset model, warmup 3, runs 20, `session.run` wall-clock latency.

| micrograph | op | CPU EP p50 | NNAPI EP p50 | QNN EP |
| --- | --- | ---: | ---: | --- |
| attention output 1024x1152 | MatMulInteger | 0.738 ms | 0.518 ms | integration blocked |
| `lm_head` tile 1152x4096 | MatMulInteger | 3.582 ms | 2.989 ms | integration blocked |
| MLP projection 1152x6912 | MatMulInteger | 3.428 ms | 3.333 ms | integration blocked |
| smoke 16x4 | MatMulInteger | 0.051 ms | 0.159 ms | integration blocked |

## 해석

- 16x4 smoke graph는 provider dispatch overhead 영향을 크게 받으므로 FPGA core cycle과 직접 비교하지 않는다.
- Projection-scale micrograph에서는 NNAPI가 CPU EP보다 낮은 p50을 보이는 경우가 있었지만, 이것을 전체 sLLM 실행 개선으로 해석하지 않는다.
- QNN은 provider가 build에 없었으므로 실패 결과가 아니라 integration blocked로 기록한다.

## 논문 반영 방식

- 표 2와 그림 2에 Y700 결과를 반영했다.
- 기존 host CPU profile은 operator-share evidence로 유지하고, Y700 APK 결과를 온디바이스 latency evidence로 분리했다.
- QNN/NNAPI/CPU provider 상태를 혼동하지 않도록 table row마다 status를 유지한다.
