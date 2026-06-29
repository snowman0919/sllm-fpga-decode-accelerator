# 저장소 구조

`main` 브랜치는 논문 검토자용 최소 구조이다. 전체 실험 흔적, raw JSON, raw board log, diagnostic 문서, legacy Quartus artifact는 `examine` 브랜치에 보존한다.

## 브랜치 역할

| 브랜치 | 역할 |
| --- | --- |
| `main` | 논문, 최종 표/그림, 핵심 source, compact manifest |
| `examine` | 전체 실험 흔적, raw logs, raw profile JSON, 중간 문서, legacy artifact |

`main`에서 어떤 파일이 제거되었다고 해서 증거가 폐기된 것은 아니다. 검토 흐름을 방해하지 않도록 `examine`에 보존한 것이다.

## main에 남기는 것

| 경로 | 내용 |
| --- | --- |
| `README.md` | 저장소 목적, 핵심 결과, claim boundary |
| `paper/current/manuscript.md` | canonical 논문 원고 |
| `docs/01_실험_근거와_주장_범위.md` | 측정 근거와 주장 범위 |
| `docs/02_재현_가이드.md` | Linux/Nix + Windows board 재현 절차 |
| `docs/03_저장소_구조.md` | 저장소 구조와 artifact 정책 |
| `paper_assets/tables/` | 논문 최종 CSV 표 |
| `paper_assets/figures/` | 논문 최종 그림 |
| `logs/*/BOARD_RUN_MANIFEST.md` | compact board evidence manifest |
| `hw/spinal/` | SpinalHDL source와 simulation |
| `quartus/de10_lite_jtag_matvec/` | clean rebuild 가능한 JTAG MatVec Quartus project |
| `windows/` | board run 및 host baseline runner |
| `scripts/` | 표/그림/package 생성 및 검증 script |

## main에서 제거하는 것

- ONNX Runtime raw profile JSON
- long-decode raw trace
- raw board stdout/stderr
- generated Tcl dump
- legacy QK / UART / non-JTAG Quartus project artifact
- custom op stub 또는 FPGA stub ONNX graph처럼 실제 구현 범위와 혼동될 수 있는 파일
- generated `dist/` package copy
- agent 작업 지시문과 diagnostic-only 문서

## generated artifact 정책

`dist/ai_accel_paper/`는 추적하지 않는 generated release package이다. 필요하면 Linux에서 다시 만든다.

```bash
python scripts/build_ort_fpga_comparison.py
python scripts/build_dist_package.py
python scripts/verify_dist_package.py
```

생성된 package는 manifest와 checksum을 포함하지만, 새로운 측정 근거를 만들지는 않는다.

## evidence label

표와 문서에서는 evidence type을 구분한다.

- `measured`: host baseline 또는 JTAG invocation overhead처럼 실제 측정값
- `board_measured`: passing board run에서 읽은 FPGA internal cycle-counter 값
- `simulation`: RTL simulation 결과
- `projected`: optimized interface 가정에 따른 estimate

현재 FPGA compute latency evidence는 `board_measured`인 `COMPUTE_CYCLES=65`, `1.3 us @ 50 MHz`뿐이다.
