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

목표 파일은 `OpenRouter Chat Thu Jul 02 2026.md` 비평문을 반드시 읽으라고 지정한다. 그러나 다음 범위에서 해당 파일을 찾지 못했다.

- `/home/monad/.codex/attachments`
- `/home/monad/develop/ai_accel/sllm-fpga-decode-accelerator`
- `/Users/choiyunhyuk/Documents/Playground`

현재 repo에는 `docs/OpenRouter Chat Tue Jun 30 2026.md`와 macOS sidecar `docs/._OpenRouter Chat Tue Jun 30 2026.md`만 확인된다.

## 현재 원고에서 즉시 확인된 위험

- `저자 검토 필요` 메타 문장이 본문에 남아 있다.
- `integration blocked`, `smoke-test`, `anchor` 등 개발 로그식 표현이 제출본 톤에 맞지 않는다.
- 1.58bit, DDR2/LPDDR2, SRAM-like FPGA 제안이 초록과 결론에 비교적 크게 배치되어 있다.
- roofline 절에 `T_compute`, `T_stream`, `B_required` 수식이 아직 들어가 있지 않다.
- `USB3 320 MB/s` 가정의 성격이 measured인지 projected인지 더 명확해야 한다.
- 본문 그림 링크가 `../../paper_assets/...` 상대경로로 남아 있다.

## Phase 0 판정

초기 repo 상태와 원고 상태는 확인되었으나, 목표에서 지정한 Thu Jul 02 비평문 파일이 없어 비평문 기반 최종 수정은 완전히 수행할 수 없다. QNN 환경도 별도 중단 조건에 걸렸으므로 `01_qnn_environment_check.md`를 함께 참조한다.
