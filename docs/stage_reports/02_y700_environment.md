# 2단계 Lenovo Y700 Android/ADB 환경 보고

작성 시점: 2026-07-01

## 현재 상태

- ADB 경로: Windows Pocket4 `C:\platform-tools\adb.exe`
- 연결 장치: `HA1XEE8V`
- 제품/모델: Lenovo `TB320FC`
- platform/hardware: `taro` / `qcom`
- Android: 15, SDK 35
- ABI: `arm64-v8a`
- MemTotal: 15,578,208 kB
- storage: `/sdcard` 기준 약 69 GB available
- thermal: `dumpsys thermalservice` 수집 완료

## 실행한 수집

```bash
ssh win "adb devices -l"
ssh win "py -3 scripts\\y700_collect_device_info.py --log-dir logs\\y700_onnx_runtime"
```

로컬 보존 위치:

- `logs/y700_onnx_runtime/device_info.json`
- `logs/y700_onnx_runtime/runtime_env.md`

## ONNX Runtime 실행 경로 판단

Android shell에는 `python3`/`python`이 없었다. Termux package는 설치되어 있었지만, 앱 sandbox 때문에 ADB shell에서 직접 Termux Python을 실행할 수 없고 `run-as com.termux`도 허용되지 않았다. 설치된 Termux APK에는 `RunCommandService`가 없어 intent 기반 비대화식 실행도 사용할 수 없었다.

따라서 최종 benchmark 경로는 별도 Android APK로 전환했다.

- `android/y700_ort_benchmark/`: 최소 Android ONNX Runtime benchmark app
- `scripts/build_y700_ort_benchmark_apk.py`: Gradle 없이 AAR, `aapt2`, `d8`, `apksigner`로 APK 생성
- ONNX Runtime Android AAR: Maven Central `onnxruntime-android:1.27.0`
- benchmark 방식: ONNX model을 APK asset으로 포함하고 Java API에서 `session.run` wall-clock latency 측정

## Provider 상태

- CPU EP: 실행 성공
- NNAPI EP: 실행 성공
- QNN EP: tested AAR build에서 provider 미지원, `integration_blocked`
- available providers in APK: `[CPU, NNAPI, XNNPACK, WEBGPU]`

## 논문 반영

Y700 장치 정보는 온디바이스 실험 환경의 근거로 사용한다. 단, 결과는 representative ONNX micrograph latency이며 Gemma 전체 모델 실행 또는 전체 ONNX graph latency가 아니다.
