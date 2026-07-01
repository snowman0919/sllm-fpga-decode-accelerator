# Phase 3 비평 기반 원고 재구성 계획

`OpenRouter Chat Thu Jul 02 2026.md` 원문은 작업 중 `docs/OpenRouter Chat Thu Jul 02 2026.md`로 확보해 읽었다. 본 계획은 해당 원문 비평과 goal objective의 사용자 판단, 현재 원고 점검 결과를 함께 기준으로 작성한다.

| 문제 | 비평 근거 | 수정 방향 | 반영 위치 | 사용자 확인 필요 |
| --- | --- | --- | --- | --- |
| `제출 전 검토 표시` 메타 문장 | 제출본에 내부 메모가 남으면 안 됨 | 문장 삭제, 구조 절을 자연스러운 본문으로 전환 | 5장 | 아니오 |
| `QNN EP 실행 경로 미확보` 표현 | 개발 로그식 표현을 피해야 함 | "QNN EP 실행 경로를 확보하지 못했다"로 순화 | 초록, 3장, 8장 | 아니오 |
| `PoC`, `검증 기준` 표현 | 제출본 톤에 부적절 | PoC, 기능 정합성, cycle-level validation으로 변경 | 초록, 1장, 6장 | 아니오 |
| Y700 micrograph 과장 위험 | 고립 micrograph latency는 full decode share를 증명하지 않음 | ORT trace와 micrograph evidence layer를 분리 | 4장, 5장, 8장 | 아니오 |
| ORT QK score 0% 해석 부족 | classifier 결과만으로 QK 부재를 의미하지 않음 | graph optimization/fused operator 가능성을 명시하고 kernel-level profiling 필요성을 적음 | 4장 | 아니오 |
| micrograph 선택 이유 부족 | full graph 대신 micrograph를 쓴 실험 설계 의도가 약함 | Android full export/KV-cache 비용과 dense projection dispatch/compute 비용을 분리하기 위한 설계로 설명 | 4장 | 아니오 |
| 1.58bit/DDR2/SRAM 비대화 | INT8 PoC와 직접 연결되지 않음 | 후속 특기자 산출물 후보로 축소 | 5장, 7장, 8장 | 필요 시 |
| roofline 수식 부족 | CPU 병목과 FPGA 요구사항의 정량 bridge 필요 | `T_compute`, `T_stream`, `B_required` 추가 | 7장 | 아니오 |
| USB3 320 MB/s 가정 불명확 | projected/model과 measured 혼동 방지 | 외부 streaming prototype model case로 명시 | 7장 | 아니오 |
| 미인용 참고문헌 | 참고문헌과 본문 연결 필요 | quantization/1.58bit 관련 문헌 본문 인용 추가 | 2장, 5장 | 아니오 |
| 상대 그림 경로 | 제출본에 경로가 노출되면 안 됨 | Markdown 경로를 repo 기준으로 바꾸고 변환 스크립트에서 HTML 경로 보정 | 그림 1-3, export script | 아니오 |
| HWP 직접 생성 불가 | 최종 제출 파일 리스크 | HWPX/DOCX/PDF와 수동 변환 README 제공 | `paper/final/README_conversion.md` | Hancom 변환 필요 |
