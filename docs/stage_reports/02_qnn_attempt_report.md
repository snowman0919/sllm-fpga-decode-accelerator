# Phase 2 QNN 추가 실험 판정

## 판정

Phase 2는 실행하지 않았다.

## 이유

Phase 1에서 지정된 QNN 설치 경로 `C:\Users\dbsgu\dev\qinst`가 존재하지 않는 것으로 확인되었다. 따라서 다음을 판단할 수 없었다.

- QNN SDK 버전
- Android AAR 또는 native library 존재 여부
- ONNX Runtime QNN EP artifact 존재 여부
- QNN backend library 존재 여부
- Y700에서 QNN EP micrograph benchmark 가능 여부

## 논문 반영 원칙

원고에는 QNN을 실패 로그처럼 쓰지 않고 다음 의미로 정리한다.

> 본 실험 환경에서는 QNN EP 실행 경로를 확보하지 못했으며, Y700 실측은 CPU EP와 NNAPI EP로 제한하였다. 따라서 Snapdragon NPU backend 평가는 후속 과제로 남는다.

## 후속 조건

QNN 실험을 재개하려면 다음 중 하나가 필요하다.

1. `ssh win`에서 접근 가능한 실제 QNN SDK 경로
2. ONNX Runtime QNN EP가 포함된 Android AAR 또는 APK build 환경
3. Qualcomm AI Engine Direct/QNN SDK sample을 Y700에서 실행할 수 있는 명령 절차
