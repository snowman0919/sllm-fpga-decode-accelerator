# 비평 대응표

작성 시점: 2026-07-02

`OpenRouter Chat Thu Jul 02 2026.md` 원문은 `docs/OpenRouter Chat Thu Jul 02 2026.md`로 보존했다. 아래 대응표는 해당 비평 원문, 최신 goal objective, 현재 원고 점검 결과를 기준으로 작성했다. 원문 비평서는 source artifact라 금지 표현을 그대로 포함할 수 있으므로 제출본 위생 검사는 원문 critique 파일을 제외하고 수행한다.

| 비평 항목 | 기존 문제 | 수정 조치 | 최종 반영 위치 | 남은 한계 | 자체 평가 |
| --- | --- | --- | --- | --- | --- |
| 정직함을 기여처럼 보이면 안 됨 | "하지 않는다" 문장이 초록과 결론에 많았음 | 기여를 Y700 micrograph, ORT profiling, DE10-Lite PoC, 구조 요구사항으로 재정렬 | 초록, 1장, 8장 | full graph 실행은 아님 | 부분 해결 |
| Y700 micrograph는 full decode share가 아님 | micrograph와 ORT trace가 같은 결론처럼 읽힘 | micrograph는 absolute latency/provider granularity, ORT trace는 operator share로 분리 | 4장, 5장, 8장 | full decode trace on Y700 없음 | 해결 |
| micrograph 사용 당위성이 약함 | 전체 모델 실행 실패의 대체물처럼 읽힐 수 있음 | Android full export/KV-cache dynamic shape/copy 비용을 분리하고 dense projection dispatch와 compute 비용을 격리하기 위한 실험 설계라고 명시 | 4장 | full graph benchmark는 아님 | 해결 |
| `attention_qk_score` 0% 해석 부족 | QK 연산이 없다는 오해 가능 | ONNX Runtime graph optimization/fused operator 내부 흡수 가능성을 명시하고 kernel-level profiling 필요성을 추가 | 4장 | fused kernel 내부 비용은 미분해 | 해결 |
| 16x4 DE10-Lite 결과 과대해석 위험 | 1.3 us가 acceleration처럼 보일 수 있었음 | 64 MAC PoC의 기능 정합성 및 cycle-level validation으로 제한 | 6장 | projection-scale FPGA 측정 없음 | 해결 |
| JTAG latency와 internal compute 혼동 | 서로 다른 물리량이 같은 축에 놓일 위험 | JTAG는 host-tool invocation overhead로 분리 | 6장 | 실용 interface 실측 없음 | 해결 |
| QNN/NPU 경로가 약함 | ORT AAR에서 QNN EP가 없고 기존 원고는 실패 표현 중심이었음 | QAIRT 2.47 direct DLC 경로로 Y700 QNN CPU/HTP 실행을 추가하고, ORT QNN EP와 분리해 표 2a에 반영 | 초록, 3장, 5장, 8장, `docs/stage_reports/11_qnn_qairt_y700_direct_run.md` | ORT QNN EP 결과가 아니며 dynamic weight input float MatMul DLC 결과 | 부분 해결 |
| 1.58bit 제안과 INT8 PoC 연결 비약 | 후속 구조가 본문 중심으로 커졌음 | 1.58bit/MatMul-free는 후속 특기자 산출물 후보로 낮추고 본문에서는 memory-centric 요구사항의 확장 후보로 제한 | 5장, 7장, 8장 | 후속 구조 구현 없음 | 부분 해결 |
| DDR2/LPDDR2/SRAM-like FPGA는 구현 결과 아님 | custom board가 구현처럼 읽힐 수 있었음 | weight-resident memory pool 후보로 제한 | 5장, 7장 | 보드 설계/검증 없음 | 해결 |
| 표/그림의 evidence type 분리 필요 | measured/projected/proposal 혼동 위험 | 표 1 및 각 절에서 measured/projected/proposal/PoC 구분 | 3장, 5-7장 | 일부 CSV artifact에는 보조 design-space 행 존재 | 부분 해결 |
| Roofline 수식 부족 | 값만 있고 계산 관계가 약했음 | `T_compute`, `T_stream`, `B_required` 수식 추가 | 7장 | 실제 streaming 측정 없음 | 해결 |
| USB3 320 MB/s 가정 성격 불명확 | 실측값처럼 읽힐 수 있었음 | 외부 streaming prototype model case로 명시 | 7장 | Y700-FPGA path 없음 | 해결 |
| 제출본 메타 표현 제거 | `제출 전 검토 표시`, `PoC`, `검증 기준` 등 남아 있었음 | 원고에서 제거 또는 PoC/core-level validation으로 변경 | 전체 원고 | historical stage report에는 과거 용어 일부 보존 가능 | 해결 |
| HWP 최종본 필요 | legacy `.hwp` 직접 생성 불가 | HWPX/DOCX/PDF/HTML 중간본과 수동 변환 README 제공 | `paper/final/` | Hancom Office 필요 | 부분 해결 |
