# 11단계 보강: QAIRT 기반 Y700 QNN direct 실행

## 목적

사용자가 제공한 Windows Pocket4의 QAIRT 설치본을 사용해 Lenovo Y700에서 QNN 계층 실험 데이터를 추가 확보했다. 이 실험은 ONNX Runtime QNN Execution Provider가 아니라, QAIRT 2.47.0의 converter, DLC 변환, Android `qnn-net-run` direct 실행 경로이다.

## 환경

- QAIRT SDK: Windows Pocket4의 QAIRT 2.47.0 설치본
- Device: Lenovo Y700 `TB320FC`
- Platform: `taro`, Qualcomm, Android 15, `arm64-v8a`
- 실행 도구: `qnn-onnx-converter`, `snpe-onnx-to-dlc`, Android `qnn-net-run`
- Backend: QNN CPU, QNN HTP

## 준비 및 제약

- Windows 기본 Python 3.11에서는 QAIRT converter의 `libPyIrGraph310.pyd` ABI와 맞지 않았다.
- `pyenv-win`으로 Python 3.10.11을 설치하고, `numpy`, `onnx`, `onnxruntime`, `pyyaml`, `scipy`, `pandas` 등 converter 의존성을 설치했다.
- ONNX Runtime Android AAR는 `[CPU, NNAPI, XNNPACK, WEBGPU]`만 제공하여 ORT QNN EP는 사용할 수 없었다.
- QAIRT ONNX converter dry-run에서 `MatMulInteger`는 `unsupported in Converter`로 확인되었다.
- 따라서 QNN direct 실행은 float MatMul DLC로 제한했다.
- 기존 micrograph는 weight를 initializer가 아닌 입력 tensor로 받으므로, QNN direct 결과는 weight-resident deployment 성능으로 해석하지 않는다.

## 실행 결과

10회 반복 input list 기준, profile CSV의 per-inference 행에서 mean/p50/p95/min/max를 직접 계산했다.

| graph | backend | runs | NetRun execute mean/p50/p95 | backend 또는 accelerator mean/p50/p95 | 해석 |
| --- | --- | ---: | --- | --- | --- |
| `lm_head` tile 1152x4096 float | QNN CPU | 10 | 14.192 / 12.709 / 26.671 ms | 12.032 / 10.750 / 22.504 ms | direct DLC CPU baseline |
| MLP projection 1152x6912 float | QNN CPU | 10 | 16.078 / 15.885 / 19.955 ms | 12.399 / 12.245 / 15.958 ms | direct DLC CPU baseline |
| `lm_head` tile 1152x4096 float | QNN HTP | 10 | 3.415 / 3.166 / 4.253 ms | 1.668 / 1.770 / 1.898 ms | HTP accelerator path 확인 |
| MLP projection 1152x6912 float | QNN HTP | 10 | 19.536 / 19.125 / 23.533 ms | 13.945 / 13.789 / 15.887 ms | shape와 data movement 영향 큼 |

## 산출물

- 요약 CSV: `paper_assets/tables/y700_qnn_direct_profile_summary.csv`
- 원본 profile 요약: `logs/y700_qnn/qnn_y700_profile_summary_10runs.csv`
- JSON 요약: `logs/y700_qnn/qnn_y700_profile_summary_10runs.json`
- Android 실행 로그: `logs/y700_qnn/qnn_net_run_y700_*`
- profile viewer 로그: `logs/y700_qnn/qnn_profile_viewer_y700_10_*`
- pulled profile/output: `logs/y700_qnn/pulled_y700_qnn_10/`

## 논문 반영 원칙

- QNN direct 결과는 ONNX Runtime QNN EP 결과가 아니다.
- QNN direct 결과는 sLLM 전체 추론 가속 근거가 아니다.
- `lm_head` HTP 결과는 accelerator 경로가 가능함을 보여주지만, MLP 결과는 shape와 movement가 병목이 될 수 있음을 함께 보여준다.
- 이 결과는 FPGA 파트에서 weight residency, invocation granularity, output tile 처리, low-overhead boundary가 필요하다는 구조 요구사항을 강화하는 근거로 사용한다.
