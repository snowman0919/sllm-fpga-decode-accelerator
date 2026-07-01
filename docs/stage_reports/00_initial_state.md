# Phase 0 초기 상태 점검

## 기준 목표

이번 작업은 `/home/monad/.codex/attachments/6e87e1d2-5a81-4ab5-8b14-4cd39558d8ed/goal-objective.md`를 기준으로 새롭게 진행한다. 논문 성격은 가속기 구현 논문이 아니라 선행 병목 분석 논문으로 제한한다.

## Git 상태

- branch: `paper-final-y700-fpga`
- upstream: `origin/paper-final-y700-fpga`
- HEAD: `054cdb42 Reframe FPGA proposal around author structure boundaries`
- `git status --short`: clean

최근 커밋:

```text
054cdb42 Reframe FPGA proposal around author structure boundaries
27929754 Record Windows HWP automation probe
5b96c971 Document HWP conversion blocker and add PDF proof
72756a57 Finalize on-device ORT and FPGA paper artifacts
40af455a Remove outdated documentation
1bcc2ee5 Consolidate paper assets with short names
ac0477cc Shorten paper CSV source labels
bdd6ab02 readme
a357d308 Fix formatting in README.md
dc87b264 Update README.md
```

## 원고 상태

- `paper/current/manuscript.md`: 존재함
- `paper/final/final_manuscript_intermediate.md`: 존재함
- 두 파일은 현재 동일함

## 비평문 확인

작업 중 root 경로에 NFD 한글 파일명 `비평문.md`로 들어온 Thu Jul 02 비평문을 확인했고, 원문 보존을 위해 `docs/OpenRouter Chat Thu Jul 02 2026.md`로 이동했다. 원문은 장문의 review transcript이므로 금지 표현 검색에서는 제출 원고와 대응표를 대상으로 삼고, 원문 critique 파일은 source artifact로 별도 보존한다.

비평문에서 최종 반영해야 할 핵심 지적은 다음과 같이 정리했다.

- Y700 micrograph는 온디바이스 근거를 강화하지만 full decode share를 직접 측정한 것은 아니다.
- DE10-Lite 16x4 INT8 MatVec의 1.3 us는 64 MAC core-level validation이지 AI 가속 성능이 아니다.
- JTAG total latency와 internal compute time은 같은 성능 비교축에 놓지 않는다.
- 1.58bit, DDR2/LPDDR2, SRAM-like scratchpad, multi-FPGA custom connector는 구현 결과가 아니라 후속 구조 후보이다.
- QNN 경로 실패는 개발 로그식 표현이 아니라 학술적 한계로 정리한다.
- Roofline/interface model에는 계산 수식과 가정의 성격을 명시한다.
- 내부 검토 표시, 개발 로그식 영문 상태 표현, 비유적 검증 표현, 상대경로 그림 링크는 제출 원고에서 제거한다.

## 현재 원고에서 즉시 확인된 위험

- `제출 전 검토 표시` 메타 문장이 본문에 남아 있다.
- `QNN EP 실행 경로 미확보`, `PoC`, `검증 기준` 등 개발 로그식 표현이 제출본 톤에 맞지 않는다.
- 1.58bit, DDR2/LPDDR2, SRAM-like FPGA 제안이 초록과 결론에 비교적 크게 배치되어 있다.
- roofline 절에 `T_compute`, `T_stream`, `B_required` 수식이 아직 들어가 있지 않다.
- `USB3 320 MB/s` 가정의 성격이 measured인지 projected인지 더 명확해야 한다.
- 본문 그림 링크가 `paper_assets/...` 상대경로로 남아 있다.

## Phase 0 판정

초기 repo 상태와 원고 상태를 확인했고, Thu Jul 02 비평문 원문도 최종적으로 확보해 읽었다. QNN 환경은 지정 경로가 확인되지 않아 별도 중단 조건에 해당하며, 상세 내용은 `01_qnn_environment_check.md`를 함께 참조한다.
